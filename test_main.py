import pytest
from fastapi.testclient import TestClient
import time
from main import app, Priority, BatchStatus

client = TestClient(app)

def test_create_ingestion():
    response = client.post(
        "/ingest",
        json={"ids": [1, 2, 3, 4, 5], "priority": "MEDIUM"}
    )
    assert response.status_code == 200
    assert "ingestion_id" in response.json()

def test_invalid_id_range():
    response = client.post(
        "/ingest",
        json={"ids": [0, 1, 2], "priority": "MEDIUM"}
    )
    assert response.status_code == 400

    response = client.post(
        "/ingest",
        json={"ids": [1, 2, 10**9 + 8], "priority": "MEDIUM"}
    )
    assert response.status_code == 400

def test_priority_ordering():
    # First request with MEDIUM priority
    response1 = client.post(
        "/ingest",
        json={"ids": [1, 2, 3, 4, 5], "priority": "MEDIUM"}
    )
    ingestion_id1 = response1.json()["ingestion_id"]
    
    # Second request with HIGH priority
    response2 = client.post(
        "/ingest",
        json={"ids": [6, 7, 8, 9], "priority": "HIGH"}
    )
    ingestion_id2 = response2.json()["ingestion_id"]
    
    # Wait for some processing
    time.sleep(6)
    
    # Check status of both requests
    status1 = client.get(f"/status/{ingestion_id1}")
    status2 = client.get(f"/status/{ingestion_id2}")
    
    # HIGH priority request should have more completed batches
    completed_batches1 = sum(1 for batch in status1.json()["batches"] 
                           if batch["status"] == BatchStatus.COMPLETED)
    completed_batches2 = sum(1 for batch in status2.json()["batches"] 
                           if batch["status"] == BatchStatus.COMPLETED)
    
    assert completed_batches2 >= completed_batches1

def test_rate_limiting():
    # Create multiple requests
    ingestion_ids = []
    for _ in range(3):
        response = client.post(
            "/ingest",
            json={"ids": [1, 2, 3], "priority": "MEDIUM"}
        )
        ingestion_ids.append(response.json()["ingestion_id"])
    
    # Wait for 6 seconds
    time.sleep(6)
    
    # Check status of all requests
    statuses = [client.get(f"/status/{id}") for id in ingestion_ids]
    
    # Count completed batches
    completed_batches = sum(
        sum(1 for batch in status.json()["batches"] 
            if batch["status"] == BatchStatus.COMPLETED)
        for status in statuses
    )
    
    # Should have processed at most 3 IDs (one batch) in 5 seconds
    assert completed_batches <= 1

def test_status_endpoint():
    # Create a request
    response = client.post(
        "/ingest",
        json={"ids": [1, 2, 3], "priority": "MEDIUM"}
    )
    ingestion_id = response.json()["ingestion_id"]
    
    # Check status immediately
    status = client.get(f"/status/{ingestion_id}")
    assert status.status_code == 200
    assert status.json()["ingestion_id"] == ingestion_id
    assert status.json()["status"] in [BatchStatus.YET_TO_START, BatchStatus.TRIGGERED]
    
    # Check non-existent ingestion
    response = client.get("/status/nonexistent")
    assert response.status_code == 404

def test_batch_size_limit():
    response = client.post(
        "/ingest",
        json={"ids": [1, 2, 3, 4, 5, 6, 7, 8, 9], "priority": "MEDIUM"}
    )
    ingestion_id = response.json()["ingestion_id"]
    
    status = client.get(f"/status/{ingestion_id}")
    batches = status.json()["batches"]
    
    # Verify that no batch has more than 3 IDs
    for batch in batches:
        assert len(batch["ids"]) <= 3 