from dotenv import load_dotenv

_ = load_dotenv()

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from langgraph_checkpoint_aws import AgentCoreMemorySaver, AgentCoreMemoryStore

from src.utils.settings import MEMORY_ID
from src.utils.logger import get_logger
from src.knowledge_base import FAQKnowledgeBase
from src.tools import FAQTools
from src.agent import FAQAgent
from src.memory import MemoryMiddleware

logger = get_logger(__name__)

app = BedrockAgentCoreApp()

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

logger.info("Application initialized")


@app.entrypoint
def agent_invocation(payload, context):
    logger.info("Received payload: %s", payload)
    logger.info("Context: %s", context)

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
    logger.info("Response generated for actor %s", actor_id)

    return {
        "result": answer,
        "actor_id": actor_id,
        "thread_id": thread_id,
    }


if __name__ == "__main__":
    app.run()
