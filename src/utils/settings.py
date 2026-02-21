from pathlib import Path

# Paths — src/utils/settings.py is 2 levels deep, go up 3 to reach project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "lauki_qna.csv"

# Embeddings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 0

# LLM
GROQ_MODEL = "openai/gpt-oss-20b"
TEMPERATURE = 0

# AWS
AWS_REGION = "ap-southeast-2"
MEMORY_ID = "lauki_agent_memory-Yrm3JrG0Vz"
