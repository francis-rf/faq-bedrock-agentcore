import csv
from typing import List

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.utils.settings import DATA_PATH, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FAQKnowledgeBase:
    def __init__(self, csv_path=DATA_PATH):
        self.csv_path = csv_path
        self._index = None
        self._load()

    def _load(self):
        try:
            docs = self._load_csv()
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
            )
            chunks = splitter.split_documents(docs)
            embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
            self._index = FAISS.from_documents(chunks, embeddings)
            logger.info("Knowledge base loaded: %d chunks indexed", len(chunks))
        except FileNotFoundError:
            logger.error("CSV file not found: %s", self.csv_path)
            raise
        except Exception as e:
            logger.error("Failed to build knowledge base: %s", e)
            raise

    def _load_csv(self) -> List[Document]:
        docs = []
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                q = row["question"].strip()
                a = row["answer"].strip()
                docs.append(Document(page_content=f"Q: {q}\nA: {a}"))
        return docs

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        return self._index.similarity_search(query, k=k)
