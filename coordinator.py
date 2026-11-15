"""
coordinator.py - Orchestrator Agent.
Coordinates calendar, memory, and notification micro-agents concurrently via AsyncIO.
Exposes FastAPI interface and direct CLI test runner.
"""

import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn

app = FastAPI(
    title="Coordinator Agent Orchestrator",
    description="Multi-agent orchestrator utilizing asyncio and MCP micro-agents.",
    version="1.0.0"
)

WORKER_URLS = {
    "calendar": "http://127.0.0.1:8001",
    "memory": "http://127.0.0.1:8002",
    "slack": "http://127.0.0.1:8003"
}

class PipelineTaskRequest(BaseModel):
    session_id: str = Field(default="demo-session-001")
    event_title: str = Field(..., description="Title of the meeting")
    start_time: str = Field(..., description="ISO 8601 start time (e.g. 2026-11-15T15:00:00)")
    timezone_str: str = Field(default="America/New_York", description="User's local IANA timezone")
    slack_channel: str = Field(default="#ai-ops")

async def call_worker(client: httpx.AsyncClient, name: str, endpoint: str, payload: dict) -> Dict[str, Any]:
    url = f"{WORKER_URLS[name]}{endpoint}"
    try:
        response = await client.post(url, json=payload, timeout=5.0)
        response.raise_for_status()
        return {"worker": name, "success": True, "data": response.json()}
    except Exception as e:
        return {"worker": name, "success": False, "error": str(e)}

@app.post("/execute_workflow")
async def execute_workflow(req: PipelineTaskRequest):
    """
    Executes a resilient 3-step multi-agent pipeline:
    1. Schedule calendar event with exact timezone normalization.
    2. Store event metadata into session memory.
    3. Dispatch confirmation notification to Slack.
    Uses asyncio.gather for concurrent execution where appropriate.
    """
    async with httpx.AsyncClient() as client:
        # Step 1: Calendar scheduling
        cal_res = await call_worker(client, "calendar", "/schedule", {
            "title": req.event_title,
            "start_time": req.start_time,
            "timezone_str": req.timezone_str,
            "duration_minutes": 45
        })

        if not cal_res["success"]:
            raise HTTPException(status_code=502, detail=f"Calendar worker failed: {cal_res.get('error')}")

        event_data = cal_res["data"]["event"]

        # Step 2 & 3: Run Memory and Slack notifications concurrently via asyncio.gather
        memory_payload = {
            "session_id": req.session_id,
            "key": "last_scheduled_meeting",
            "content": f"Meeting '{req.event_title}' booked for {event_data['utc_start']}",
            "metadata": event_data
        }
        slack_payload = {
            "channel": req.slack_channel,
            "text": f"✅ Multi-Agent Orchestrator: Event '{req.event_title}' confirmed for {event_data['local_start']} ({req.timezone_str})",
            "priority": "normal"
        }

        memory_res, slack_res = await asyncio.gather(
            call_worker(client, "memory", "/store", memory_payload),
            call_worker(client, "slack", "/send", slack_payload)
        )

        return {
            "status": "completed",
            "pipeline_summary": {
                "calendar": cal_res,
                "memory": memory_res,
                "slack": slack_res
            }
        }

if __name__ == "__main__":
    uvicorn.run("coordinator:app", host="127.0.0.1", port=8000, reload=False)
