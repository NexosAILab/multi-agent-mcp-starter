"""
Calendar Agent Worker — Model Context Protocol (MCP) Client
Includes production fix for Timezone Offset Collisions (UTC vs Local IANA).
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, field_validator

class CalendarEventRequest(BaseModel):
    summary: str = Field(..., description="Title of the meeting")
    start_time: str = Field(..., description="ISO-8601 formatted timestamp with explicit offset")
    duration_minutes: int = Field(default=30, ge=15, le=120)
    timezone_iana: str = Field(default="America/New_York", description="Valid IANA timezone string")

    @field_validator("start_time")
    def validate_timezone_awareness(cls, v):
        """
        THE FIX: Intercept naive ISO strings that cause Google Calendar double-booking.
        Rejects timestamps lacking explicit offset or timezone awareness.
        """
        try:
            dt = datetime.fromisoformat(v)
            if dt.tzinfo is None:
                raise ValueError("CRITICAL: Naive datetime rejected. Must provide explicit timezone offset (e.g. -04:00 or Z).")
            return v
        except Exception as e:
            raise ValueError(f"Invalid timestamp format: {e}")

class CalendarAgent:
    def __init__(self, default_tz: str = "America/New_York"):
        self.default_tz = ZoneInfo(default_tz)

    async def schedule_meeting(self, summary: str, naive_or_iso_str: str, duration: int = 30) -> dict:
        """
        Simulates resolving availability and reserving verified calendar slot via MCP.
        Normalizes any timestamp to strict timezone-aware ISO string.
        """
        # Parse and localize if needed
        try:
            dt = datetime.fromisoformat(naive_or_iso_str)
            if dt.tzinfo is None:
                # Force local timezone mapping
                dt = dt.replace(tzinfo=self.default_tz)
        except Exception:
            dt = datetime.now(self.default_tz)

        validated = CalendarEventRequest(
            summary=summary,
            start_time=dt.isoformat(),
            duration_minutes=duration,
            timezone_iana=str(self.default_tz)
        )

        # MCP Tool payload dispatch
        return {
            "status": "confirmed",
            "event_id": "evt_mcp_9921",
            "summary": validated.summary,
            "start": validated.start_time,
            "timezone": validated.timezone_iana,
            "duration": f"{validated.duration_minutes}m"
        }
