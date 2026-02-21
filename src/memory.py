import uuid

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain.agents.middleware import AgentMiddleware, AgentState
from langgraph.store.base import BaseStore

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryMiddleware(AgentMiddleware):
    def pre_model_hook(self, state: AgentState, config: RunnableConfig, *, store: BaseStore):
        actor_id = config["configurable"]["actor_id"]
        thread_id = config["configurable"]["thread_id"]
        namespace = (actor_id, thread_id)
        messages = state.get("messages", [])

        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                store.put(namespace, str(uuid.uuid4()), {"message": msg})

                user_preferences_namespace = ("preferences", actor_id)
                try:
                    preferences = store.search(
                        user_preferences_namespace,
                        query=msg.content,
                        limit=5
                    )
                    if preferences:
                        memory_context = "\n".join(
                            f"Memory: {item.value.get('message', '')}"
                            for item in preferences
                        )
                        logger.info("Retrieved memories for actor %s: %s", actor_id, memory_context)
                except Exception as e:
                    logger.error("Memory retrieval error for actor %s: %s", actor_id, e)
                break

        return {"messages": messages}

    def post_model_hook(self, state: AgentState, config: RunnableConfig, *, store: BaseStore):
        actor_id = config["configurable"]["actor_id"]
        thread_id = config["configurable"]["thread_id"]
        namespace = (actor_id, thread_id)
        messages = state.get("messages", [])

        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                store.put(namespace, str(uuid.uuid4()), {"message": msg})
                logger.info("Saved AI response to memory for actor %s", actor_id)
                break

        return state
