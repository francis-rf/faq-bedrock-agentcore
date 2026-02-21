from typing import List

from langchain_core.tools import tool

from src.knowledge_base import FAQKnowledgeBase
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FAQTools:
    def __init__(self, knowledge_base: FAQKnowledgeBase):
        self._kb = knowledge_base

    def get_tools(self) -> List:
        kb = self._kb

        @tool
        def search_faq(query: str) -> str:
            """Search the FAQ knowledge base for relevant information.
            Use this tool when the user asks questions about products, services, or policies.

            Args:
                query: The search query to find relevant FAQ entries

            Returns:
                Relevant FAQ entries that might answer the question
            """
            results = kb.similarity_search(query, k=3)
            if not results:
                return "No relevant FAQ entries found."
            context = "\n\n---\n\n".join(
                f"FAQ Entry {i+1}:\n{doc.page_content}"
                for i, doc in enumerate(results)
            )
            return f"Found {len(results)} relevant FAQ entries:\n\n{context}"

        @tool
        def search_detailed_faq(query: str, num_results: int = 5) -> str:
            """Search the FAQ knowledge base with more results for complex queries.
            Use this when the initial search doesn't provide enough information.

            Args:
                query: The search query
                num_results: Number of results to retrieve (default: 5)

            Returns:
                More comprehensive FAQ entries
            """
            results = kb.similarity_search(query, k=num_results)
            if not results:
                return "No relevant FAQ entries found."
            context = "\n\n---\n\n".join(
                f"FAQ Entry {i+1}:\n{doc.page_content}"
                for i, doc in enumerate(results)
            )
            return f"Found {len(results)} detailed FAQ entries:\n\n{context}"

        @tool
        def reformulate_query(original_query: str, focus_aspect: str) -> str:
            """Reformulate the query to focus on a specific aspect.
            Use this when you need to search for a different angle of the question.

            Args:
                original_query: The original user question
                focus_aspect: The specific aspect to focus on (e.g., "pricing", "activation", "troubleshooting")

            Returns:
                A reformulated query focused on the specified aspect
            """
            reformulated = f"{focus_aspect} related to {original_query}"
            results = kb.similarity_search(reformulated, k=3)
            if not results:
                return f"No results found for aspect: {focus_aspect}"
            context = "\n\n---\n\n".join(
                f"Entry {i+1}:\n{doc.page_content}"
                for i, doc in enumerate(results)
            )
            return f"Results for '{focus_aspect}' aspect:\n\n{context}"

        logger.info("FAQ tools initialized")
        return [search_faq, search_detailed_faq, reformulate_query]
