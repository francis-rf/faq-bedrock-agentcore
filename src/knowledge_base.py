import csv
from typing import List

import boto3
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.utils.settings import EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, AWS_REGION, S3_BUCKET, S3_KEY
from src.utils.logger import get_logger

logger = get_logger(__name__)

TMP_CSV_PATH = "/tmp/qna.csv"


class FAQKnowledgeBase:
    def __init__(self):
        self._index = None
        self._load()

    def _download_from_s3(self) -> str:
        try:
            s3 = boto3.client("s3", region_name=AWS_REGION)
            s3.download_file(S3_BUCKET, S3_KEY, TMP_CSV_PATH)
            logger.info("CSV downloaded from s3://%s/%s", S3_BUCKET, S3_KEY)
            return TMP_CSV_PATH
        except Exception as e:
            logger.error("Failed to download CSV from S3: %s", e)
            raise

    def _load(self):
        try:
            csv_path = self._download_from_s3()
            docs = self._load_csv(csv_path)
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
            )
            chunks = splitter.split_documents(docs)
            embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
            self._index = FAISS.from_documents(chunks, embeddings)
            logger.info("Knowledge base loaded: %d chunks indexed", len(chunks))
        except Exception as e:
            logger.error("Failed to build knowledge base: %s", e)
            raise

    def _load_csv(self, csv_path: str) -> List[Document]:
        docs = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                q = row["question"].strip()
                a = row["answer"].strip()
                docs.append(Document(page_content=f"Q: {q}\nA: {a}"))
        return docs

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        return self._index.similarity_search(query, k=k)
