# Embeddings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 0

# LLM
GROQ_MODEL = "openai/gpt-oss-20b"
TEMPERATURE = 0

# AWS
AWS_REGION = "us-east-1"

# S3
S3_BUCKET = "faq-agent-data"
S3_KEY = "qna.csv"

# Secrets Manager
SECRET_NAME = "faq-agent/groq-api-key"
