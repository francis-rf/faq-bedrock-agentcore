import json
import os

import boto3

from src.utils.settings import SECRET_NAME, AWS_REGION
from src.utils.logger import get_logger

_logger = get_logger(__name__)


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

MEMORY_ID = os.environ["MEMORY_ID"]

# Initialize components
knowledge_base = FAQKnowledgeBase()
tools = FAQTools(knowledge_base).get_tools()
checkpointer = AgentCoreMemorySaver(memory_id=MEMORY_ID)
memory_store = AgentCoreMemoryStore(memory_id=MEMORY_ID)
agent = FAQAgent(
    tools=tools,
    checkpointer=checkpointer,
    store=memory_store,
    middleware=[MemoryMiddleware()],
)

_logger.info("Application initialized")


@app.entrypoint
def agent_invocation(payload, context):
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


if __name__ == "__main__":
    app.run()
