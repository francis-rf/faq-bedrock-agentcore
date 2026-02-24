# 🤖 Lauki FAQ Agent

![Python](https://img.shields.io/badge/Python-3.11-blue) ![LangGraph](https://img.shields.io/badge/LangGraph-latest-green) ![AWS](https://img.shields.io/badge/AWS-Bedrock_AgentCore-orange) ![License](https://img.shields.io/badge/License-MIT-yellow)

Answers customer questions about **Lauki Phones** — a fictional mobile carrier covering plans, SIM activation, billing, roaming, eSIM, and device support.
Built with LangGraph and deployed on AWS Bedrock AgentCore, with a web chat UI powered by a FastAPI proxy.

---

## 🎯 Features

- Semantic FAQ search using FAISS + sentence-transformers
- Persistent conversation memory via AgentCore Memory (LangGraph checkpointing)
- Web chat UI (HTML/CSS/JS) served by a FastAPI proxy
- Two Docker containers — ARM64 agent backend + AMD64 web server
- CI/CD via GitHub Actions with a self-hosted ARM64 runner

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent | LangGraph, LangChain, Groq (OPENAI) |
| Search | FAISS, sentence-transformers |
| Backend | AWS Bedrock AgentCore, S3, Secrets Manager, ECR |
| Web | FastAPI, uvicorn, boto3 |
| CI/CD | GitHub Actions, App Runner |

---

## 📁 Project Structure

```
final_project/
├── src/
│   ├── agent.py            # FAQAgent — LangGraph graph + tool binding
│   ├── knowledge_base.py   # FAQKnowledgeBase — FAISS index builder
│   ├── tools.py            # Search tools (exact, semantic, hybrid)
│   ├── memory.py           # AgentCore Memory middleware
│   └── utils/
│       ├── settings.py     # All config values (S3, Secrets, region)
│       └── logger.py       # Centralized logging
├── frontend/
│   ├── index.html          # Chat UI
│   ├── style.css           # Dark theme, AWS orange accents
│   └── app.js              # Fetch /chat, render bubbles
├── data/
│   └── qna.csv             # FAQ dataset
├── main.py                 # AgentCore entrypoint (BedrockAgentCoreApp)
├── server.py               # FastAPI proxy — serves UI + forwards to AgentCore
├── Dockerfile              # ARM64 agent backend image
├── Dockerfile.web          # AMD64 web server image
├── requirements.txt        # Agent dependencies
└── requirements.web.txt    # Web server dependencies
```

---

## 🚀 Local Development

### Web UI

```bash
# Install dependencies
pip install -r requirements.web.txt

# Set environment variables
$env:AGENT_RUNTIME_ARN="arn:aws:bedrock-agentcore:<region>:<account>:runtime/<id>"
$env:AWS_REGION="us-east-1"

# Run
uvicorn server:app --port 8000
```

Open `http://localhost:8000`

> AWS credentials must be configured locally (`aws configure` or env vars).

### Agent (local testing)

```bash
pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY
python main.py
```

---

## ☁️ AWS Deployment

### Agent Backend → Bedrock AgentCore

1. Build ARM64 image on an EC2 Graviton instance
2. Push to ECR (`faq-agent` repository)
3. Create AgentCore agent runtime pointing to ECR image + IAM role
4. Create a version → wait for READY → update DEFAULT endpoint

### Web Server → App Runner

1. Build AMD64 image: `docker build -f Dockerfile.web -t faq-agent-web .`
2. Push to ECR (`faq-agent-web` repository)
3. Create App Runner service pointing to ECR image
4. Set env vars: `AGENT_RUNTIME_ARN`, `AWS_REGION`
5. Attach IAM role with `bedrock-agentcore:InvokeAgentRuntime` permission

---

## 📄 License

MIT
