import os
from typing import List, Optional

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from src.utils.settings import GROQ_MODEL, TEMPERATURE
from src.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a helpful FAQ assistant with access to a knowledge base and user memory.

Your goal is to answer user questions accurately using the available tools while remembering user preferences.

Guidelines:
1. Check if you have relevant user preferences or history from previous conversations
2. Use the search_faq tool to find relevant information from the knowledge base
3. If the query is complex, use reformulate_query to search different aspects
4. Personalize responses based on user preferences when relevant
5. Always provide a clear, concise answer based on the retrieved information
6. If you cannot find relevant information, clearly state that

Think step-by-step and use tools strategically to provide the best answer."""


class FAQAgent:
    def __init__(
        self,
        tools: List,
        checkpointer=None,
        store=None,
        middleware: Optional[List] = None,
    ):
        self._tools = tools
        self._checkpointer = checkpointer
        self._store = store
        self._middleware = middleware or []
        self._agent = self._build()

    def _build(self):
        llm = init_chat_model(
            model=GROQ_MODEL,
            model_provider="groq",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=TEMPERATURE,
        )
        agent = create_agent(
            model=llm,
            tools=self._tools,
            checkpointer=self._checkpointer,
            store=self._store,
            middleware=self._middleware if self._middleware else None,
            system_prompt=SYSTEM_PROMPT,
        )
        logger.info("FAQAgent built successfully")
        return agent

    def invoke(self, query: str, config: Optional[dict] = None) -> str:
        try:
            result = self._agent.invoke(
                {"messages": [("human", query)]},
                config=config,
            )
            messages = result.get("messages", [])
            return messages[-1].content if messages else "No response generated"
        except Exception as e:
            logger.error("Agent invocation failed: %s", e)
            raise
