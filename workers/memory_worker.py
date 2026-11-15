"""
memory_worker.py - Short-term and semantic context worker.
Provides memory storage and query tools for the coordinator agent.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Dict, Optional
import uvicorn

app = FastAPI(
    title="Memory Micro-Agent Worker",
    description="Context and session memory worker for distributed multi-agent systems.",
    version="1.0.0"
)

MEMORY_STORE: Dict[str, List[dict]] = {}

class StoreMemoryRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    key: str = Field(..., description="Context key or topic")
    content: str = Field(..., description="Text content to remember")
    metadata: Optional[dict] = Field(default_factory=dict)

@app.get("/health")
async def health_check():
    total_memories = sum(len(v) for v in MEMORY_STORE.values())
    return {"status": "healthy", "service": "memory_worker", "total_memories": total_memories}

@app.post("/store")
async def store_memory(req: StoreMemoryRequest):
    if req.session_id not in MEMORY_STORE:
        MEMORY_STORE[req.session_id] = []
    
    item = {
        "key": req.key,
        "content": req.content,
        "metadata": req.metadata,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    MEMORY_STORE[req.session_id].append(item)
    return {"status": "stored", "session_id": req.session_id, "key": req.key}

@app.get("/retrieve/{session_id}")
async def retrieve_memories(session_id: str, key: Optional[str] = None):
    memories = MEMORY_STORE.get(session_id, [])
    if key:
        memories = [m for m in memories if m["key"] == key]
    return {"session_id": session_id, "memories": memories}

if __name__ == "__main__":
    uvicorn.run("memory_worker:app", host="127.0.0.1", port=8002, reload=False)
