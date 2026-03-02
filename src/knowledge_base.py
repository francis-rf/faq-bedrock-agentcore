import csv
import os
from pathlib import Path
from typing import List

import boto3
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.utils.settings import (
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP,
    AWS_REGION, S3_BUCKET, S3_KEY, S3_VECTORSTORE_PREFIX
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

TMP_CSV_PATH = "/tmp/qna.csv"
TMP_VECTORSTORE_DIR = "/tmp/faiss_index"

# FAISS saves two files
FAISS_FILES = ["index.faiss", "index.pkl"]


class FAQKnowledgeBase:
    def __init__(self):
        self._index = None
        self._embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self._load()

    # ── S3 helpers ────────────────────────────────────────────────────────────

    def _s3(self):
        return boto3.client("s3", region_name=AWS_REGION)

    def _download_csv(self) -> str:
        try:
            self._s3().download_file(S3_BUCKET, S3_KEY, TMP_CSV_PATH)
            logger.info("CSV downloaded from s3://%s/%s", S3_BUCKET, S3_KEY)
            return TMP_CSV_PATH
        except Exception as e:
            logger.error("Failed to download CSV from S3: %s", e)
            raise

    def _vectorstore_exists_in_s3(self) -> bool:
        """Check if all FAISS index files exist in S3."""
        try:
            s3 = self._s3()
            for filename in FAISS_FILES:
                s3.head_object(Bucket=S3_BUCKET, Key=f"{S3_VECTORSTORE_PREFIX}/{filename}")
            return True
        except Exception:
            return False

    def _download_vectorstore(self):
        """Download FAISS index files from S3."""
        Path(TMP_VECTORSTORE_DIR).mkdir(parents=True, exist_ok=True)
        s3 = self._s3()
        for filename in FAISS_FILES:
            s3_key = f"{S3_VECTORSTORE_PREFIX}/{filename}"
            local_path = f"{TMP_VECTORSTORE_DIR}/{filename}"
            s3.download_file(S3_BUCKET, s3_key, local_path)
        logger.info("FAISS index downloaded from s3://%s/%s/", S3_BUCKET, S3_VECTORSTORE_PREFIX)

    def _upload_vectorstore(self):
        """Upload FAISS index files to S3."""
        s3 = self._s3()
        for filename in FAISS_FILES:
            local_path = f"{TMP_VECTORSTORE_DIR}/{filename}"
            s3_key = f"{S3_VECTORSTORE_PREFIX}/{filename}"
            s3.upload_file(local_path, S3_BUCKET, s3_key)
        logger.info("FAISS index uploaded to s3://%s/%s/", S3_BUCKET, S3_VECTORSTORE_PREFIX)

    # ── Load logic ────────────────────────────────────────────────────────────

    def _load(self):
        if self._vectorstore_exists_in_s3():
            self._load_from_s3()
        else:
            self._build_from_csv()

    def _load_from_s3(self):
        """Download and load existing FAISS index from S3."""
        try:
            self._download_vectorstore()
            self._index = FAISS.load_local(
                TMP_VECTORSTORE_DIR,
                self._embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("Knowledge base loaded from S3 vectorstore")
        except Exception as e:
            logger.error("Failed to load vectorstore from S3: %s — rebuilding", e)
            self._build_from_csv()

    def _build_from_csv(self):
        """Build FAISS index from CSV, then upload to S3."""
        try:
            csv_path = self._download_csv()
            docs = self._load_csv(csv_path)
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
            )
            chunks = splitter.split_documents(docs)
            self._index = FAISS.from_documents(chunks, self._embeddings)
            logger.info("Knowledge base built: %d chunks indexed", len(chunks))

            # Save locally and upload to S3 for future startups
            Path(TMP_VECTORSTORE_DIR).mkdir(parents=True, exist_ok=True)
            self._index.save_local(TMP_VECTORSTORE_DIR)
            self._upload_vectorstore()
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

    # ── Search ────────────────────────────────────────────────────────────────

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        return self._index.similarity_search(query, k=k)
