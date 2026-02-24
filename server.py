"""
server.py — FAQ Agent Web Frontend (v1.1)

FastAPI proxy that:
  - Serves the static chat UI from frontend/
  - Exposes POST /chat which forwards requests to the
    AgentCore DEFAULT endpoint using boto3 (SigV4 signing handled automatically)

Environment variables required at runtime:
  AGENT_RUNTIME_ARN — AgentCore runtime ARN (full ARN)
  AWS_REGION        — AWS region (default: us-east-1)

AWS credentials are picked up automatically via:
  - IAM role attached to the container (App Runner / EC2)
  - or environment variables (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)
"""

import json
import os

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Config ────────────────────────────────────────────────────────────────────

REGION            = os.environ.get("AWS_REGION", "us-east-1")
AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN", "")

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="FAQ Agent Web UI", docs_url=None, redoc_url=None)


# ── Request / Response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    prompt:    str
    actor_id:  str = "web-user"
    thread_id: str = "web-session-1"


# ── API endpoints ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check for App Runner / load balancers."""
    return {"status": "ok", "agent_runtime_arn": AGENT_RUNTIME_ARN or "not-set"}


@app.post("/chat")
def chat(req: ChatRequest):
    """
    Forward a chat message to AgentCore and return the agent's response.

    boto3 handles AWS SigV4 request signing automatically using the
    credentials available in the environment (IAM role or env vars).
    """
    if not AGENT_RUNTIME_ARN:
        raise HTTPException(
            status_code=503,
            detail="AGENT_RUNTIME_ARN environment variable is not set.",
        )

    client = boto3.client("bedrock-agentcore", region_name=REGION)

    payload = {
        "prompt":    req.prompt,
        "actor_id":  req.actor_id,
        "thread_id": req.thread_id,
    }

    try:
        response = client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            payload=json.dumps(payload).encode(),
        )
        body = response["response"].read()
        return json.loads(body)

    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        raise HTTPException(status_code=502, detail=f"AgentCore error [{code}]: {msg}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Static frontend — mounted LAST so /chat and /health take priority ─────────

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")


# ── Local dev entry-point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
