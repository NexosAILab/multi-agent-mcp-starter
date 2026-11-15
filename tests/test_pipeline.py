"""
test_pipeline.py - Verification suite for multi-agent coordinator and workers.
"""

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def test_timezone_conversion():
    # Verify zoneinfo behaves deterministically without UTC drift
    ny_tz = ZoneInfo("America/New_York")
    naive_dt = datetime(2026, 11, 15, 15, 0, 0)
    local_dt = naive_dt.replace(tzinfo=ny_tz)
    utc_dt = local_dt.astimezone(timezone.utc)
    
    # 15:00 EST is 20:00 UTC
    assert utc_dt.hour == 20
    assert utc_dt.day == 15

def test_worker_configs():
    import json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "mcp_servers.json")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "mcpServers" in data
    assert "calendar_worker" in data["mcpServers"]
    assert "memory_worker" in data["mcpServers"]
    assert "slack_worker" in data["mcpServers"]

if __name__ == "__main__":
    test_timezone_conversion()
    test_worker_configs()
    print("ALL TESTS PASSED")
