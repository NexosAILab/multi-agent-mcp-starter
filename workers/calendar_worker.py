"""
calendar_worker.py - Calendar Micro-Agent Worker.
Handles event scheduling, availability checks, and strict timezone conversions using zoneinfo.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, List
import uvicorn

app = FastAPI(
    title="Calendar Micro-Agent Worker",
    description="MCP-compliant calendar worker with zero-drift timezone normalization.",
    version="1.0.0"
)

# In-memory storage for demonstration
SCHEDULED_EVENTS: List[dict] = []

class ScheduleRequest(BaseModel):
    title: str = Field(..., description="Title of the calendar event")
    start_time: str = Field(..., description="ISO 8601 start time (e.g. 2026-11-15T10:00:00)")
    duration_minutes: int = Field(default=30, ge=5, le=480, description="Duration in minutes")
    timezone_str: str = Field(default="UTC", description="IANA Time Zone Name (e.g. America/New_York)")
    attendees: Optional[List[str]] = Field(default_factory=list, description="List of attendee emails")

class ConflictCheckRequest(BaseModel):
    start_time: str
    end_time: str
    timezone_str: str = "UTC"

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "calendar_worker", "events_count": len(SCHEDULED_EVENTS)}

@app.post("/schedule")
async def schedule_event(req: ScheduleRequest):
    try:
        tz = ZoneInfo(req.timezone_str)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid IANA timezone: {req.timezone_str}")

    try:
        # Parse local time and attach timezone
        naive_dt = datetime.fromisoformat(req.start_time)
        local_dt = naive_dt.replace(tzinfo=tz)
        utc_dt = local_dt.astimezone(timezone.utc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse datetime: {str(e)}")

    event = {
        "id": f"evt_{len(SCHEDULED_EVENTS) + 1:04d}",
        "title": req.title,
        "local_start": local_dt.isoformat(),
        "utc_start": utc_dt.isoformat(),
        "timezone": req.timezone_str,
        "duration_minutes": req.duration_minutes,
        "attendees": req.attendees,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    SCHEDULED_EVENTS.append(event)
    return {
        "status": "scheduled",
        "event": event,
        "message": f"Event scheduled at {local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC: {utc_dt.strftime('%H:%M:%S')})"
    }

@app.get("/events")
async def list_events():
    return {"events": SCHEDULED_EVENTS}

if __name__ == "__main__":
    uvicorn.run("calendar_worker:app", host="127.0.0.1", port=8001, reload=False)
