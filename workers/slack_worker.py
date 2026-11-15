"""
slack_worker.py - Notification and outbound dispatch worker.
Simulates sending targeted alerts and executive briefs to Slack channels.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Optional
import uvicorn

app = FastAPI(
    title="Slack Dispatcher Worker",
    description="Notification and message dispatch worker for multi-agent workflows.",
    version="1.0.0"
)

OUTBOX: List[dict] = []

class SlackMessageRequest(BaseModel):
    channel: str = Field(default="#general", description="Slack channel name")
    text: str = Field(..., description="Message text or notification payload")
    priority: str = Field(default="normal", description="urgent | normal | low")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "slack_worker", "messages_sent": len(OUTBOX)}

@app.post("/send")
async def send_message(req: SlackMessageRequest):
    msg = {
        "id": f"msg_{len(OUTBOX) + 1:04d}",
        "channel": req.channel,
        "text": req.text,
        "priority": req.priority,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    OUTBOX.append(msg)
    return {"status": "delivered", "message": msg}

if __name__ == "__main__":
    uvicorn.run("slack_worker:app", host="127.0.0.1", port=8003, reload=False)
