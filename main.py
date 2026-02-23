import json
import os
import traceback

import boto3

from src.utils.settings import SECRET_NAME, AWS_REGION
from src.utils.logger import get_logger

_logger = get_logger(__name__)

# AgentCoreMemorySaver creates its boto3 client using the AWS_DEFAULT_REGION env var.
# AgentCore's managed runtime doesn't set this automatically, so we set it explicitly
# here — before any lazy initialization runs — so boto3 can resolve the region.
os.environ.setdefault("AWS_DEFAULT_REGION", AWS_REGION)


def _load_secrets():
    """Fetch all secrets from Secrets Manager."""
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        response = client.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(response["SecretString"])
        os.environ["GROQ_API_KEY"] = secret["GROQ_API_KEY"]
        os.environ["MEMORY_ID"] = secret["MEMORY_ID"]
        _logger.info("Secrets loaded from Secrets Manager")
    except Exception as e:
        _logger.error("Failed to load secrets: %s", e)
        raise


_load_secrets()

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from langgraph_checkpoint_aws import AgentCoreMemorySaver, AgentCoreMemoryStore

from src.knowledge_base import FAQKnowledgeBase
from src.tools import FAQTools
from src.agent import FAQAgent
from src.memory import MemoryMiddleware

app = BedrockAgentCoreApp()

# Lazy initialization — agent is built on the first invocation request,
# not at container startup. This ensures app.run() is reached quickly so
# AgentCore's health check on /ping succeeds before initialization completes.
_agent = None
_init_error = None


def _init_agent():
    """Initialize the agent on first call. Subsequent calls return the cached instance."""
    global _agent, _init_error

    if _agent is not None:
        return _agent

    if _init_error is not None:
        raise _init_error

    try:
        MEMORY_ID = os.environ["MEMORY_ID"]
        knowledge_base = FAQKnowledgeBase()
        tools = FAQTools(knowledge_base).get_tools()
        checkpointer = AgentCoreMemorySaver(memory_id=MEMORY_ID)
        memory_store = AgentCoreMemoryStore(memory_id=MEMORY_ID)
        _agent = FAQAgent(
            tools=tools,
            checkpointer=checkpointer,
            store=memory_store,
            middleware=[MemoryMiddleware()],
        )
        _logger.info("Agent initialized successfully")
        return _agent
    except Exception as e:
        _logger.error("Failed to initialize agent: %s", e, exc_info=True)
        _init_error = e
        raise


@app.entrypoint
def agent_invocation(payload, context):
    try:
        agent = _init_agent()

        _logger.info("Received payload: %s", payload)
        _logger.info("Context: %s", context)

        query = payload.get("prompt", "No prompt found in input")
        actor_id = payload.get("actor_id", "default-user")
        thread_id = payload.get("thread_id", payload.get("session_id", "default-session"))

        config = {
            "configurable": {
                "thread_id": thread_id,
                "actor_id": actor_id,
            }
        }

        answer = agent.invoke(query, config=config)
        _logger.info("Response generated for actor %s", actor_id)

        return {
            "result": answer,
            "actor_id": actor_id,
            "thread_id": thread_id,
        }
    except Exception as e:
        error_details = traceback.format_exc()
        _logger.error("Invocation failed: %s", error_details)
        return {"error": str(e), "traceback": error_details}


if __name__ == "__main__":
    app.run()
