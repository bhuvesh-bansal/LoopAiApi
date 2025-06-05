from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum
import asyncio
import uuid
from datetime import datetime
import time
from collections import defaultdict
import heapq

app = FastAPI(title="Data Ingestion API")

class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IngestionRequest(BaseModel):
    ids: List[int] = Field(..., description="List of IDs to process")
    priority: Priority = Field(..., description="Priority level of the request")

class BatchStatus(str, Enum):
    YET_TO_START = "yet_to_start"
    TRIGGERED = "triggered"
    COMPLETED = "completed"

class Batch:
    def __init__(self, batch_id: str, ids: List[int], priority: Priority, created_time: float):
        self.batch_id = batch_id
        self.ids = ids
        self.priority = priority
        self.created_time = created_time
        self.status = BatchStatus.YET_TO_START

    def __lt__(self, other):
        # Priority order: HIGH > MEDIUM > LOW
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        if priority_order[self.priority] != priority_order[other.priority]:
            return priority_order[self.priority] < priority_order[other.priority]
        return self.created_time < other.created_time

# In-memory storage
ingestion_store: Dict[str, Dict] = {}
batch_queue = []
processing_lock = asyncio.Lock()
last_batch_time = 0
BATCH_SIZE = 3
RATE_LIMIT_SECONDS = 5

async def process_batch(batch: Batch):
    """Process a batch of IDs with simulated API calls"""
    batch.status = BatchStatus.TRIGGERED
    await asyncio.sleep(1)  # Simulate API call
    batch.status = BatchStatus.COMPLETED

async def batch_processor():
    """Background task to process batches"""
    global last_batch_time
    while True:
        async with processing_lock:
            if batch_queue:
                current_time = time.time()
                if current_time - last_batch_time >= RATE_LIMIT_SECONDS:
                    batch = heapq.heappop(batch_queue)
                    await process_batch(batch)
                    last_batch_time = current_time
        await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(batch_processor())

@app.post("/ingest")
async def create_ingestion(request: IngestionRequest):
    ingestion_id = str(uuid.uuid4())
    created_time = time.time()
    
    # Validate IDs
    for id in request.ids:
        if not 1 <= id <= 10**9 + 7:
            raise HTTPException(status_code=400, detail=f"Invalid ID: {id}. Must be between 1 and 10^9+7")
    
    # Split into batches
    batches = []
    for i in range(0, len(request.ids), BATCH_SIZE):
        batch_ids = request.ids[i:i + BATCH_SIZE]
        batch_id = str(uuid.uuid4())
        batch = Batch(batch_id, batch_ids, request.priority, created_time)
        batches.append(batch)
        heapq.heappush(batch_queue, batch)
    
    # Store ingestion info
    ingestion_store[ingestion_id] = {
        "batches": batches,
        "created_time": created_time
    }
    
    return {"ingestion_id": ingestion_id}

@app.get("/status/{ingestion_id}")
async def get_status(ingestion_id: str):
    if ingestion_id not in ingestion_store:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    
    ingestion = ingestion_store[ingestion_id]
    batches = ingestion["batches"]
    
    # Calculate overall status
    statuses = [batch.status for batch in batches]
    if all(status == BatchStatus.COMPLETED for status in statuses):
        overall_status = BatchStatus.COMPLETED
    elif any(status == BatchStatus.TRIGGERED for status in statuses):
        overall_status = BatchStatus.TRIGGERED
    else:
        overall_status = BatchStatus.YET_TO_START
    
    return {
        "ingestion_id": ingestion_id,
        "status": overall_status,
        "batches": [
            {
                "batch_id": batch.batch_id,
                "ids": batch.ids,
                "status": batch.status
            }
            for batch in batches
        ]
    } 