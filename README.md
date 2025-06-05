# Data Ingestion API System

This is a FastAPI-based implementation of a data ingestion system that processes batches of IDs asynchronously with priority-based scheduling and rate limiting.

## Features

- Asynchronous batch processing
- Priority-based scheduling (HIGH, MEDIUM, LOW)
- Rate limiting (1 batch per 5 seconds)
- Batch size limit (3 IDs per batch)
- Status tracking for ingestion requests
- Comprehensive test suite

## Requirements

- Python 3.7+
- FastAPI
- Uvicorn
- Pydantic
- Pytest (for testing)

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Create Ingestion Request
- **Endpoint**: POST /ingest
- **Input**:
```json
{
    "ids": [1, 2, 3, 4, 5],
    "priority": "HIGH"
}
```
- **Output**:
```json
{
    "ingestion_id": "uuid-string"
}
```

### 2. Check Status
- **Endpoint**: GET /status/{ingestion_id}
- **Output**:
```json
{
    "ingestion_id": "uuid-string",
    "status": "yet_to_start|triggered|completed",
    "batches": [
        {
            "batch_id": "uuid-string",
            "ids": [1, 2, 3],
            "status": "yet_to_start|triggered|completed"
        }
    ]
}
```

## Running Tests

Run the test suite:
```bash
pytest test_main.py -v
```

## Design Choices

1. **FastAPI**: Chosen for its excellent async support, automatic API documentation, and type checking.

2. **Priority Queue**: Implemented using Python's heapq for efficient priority-based scheduling.

3. **In-memory Storage**: Used for simplicity, but can be easily extended to use a database.

4. **Asynchronous Processing**: Utilizes FastAPI's async capabilities and asyncio for non-blocking operations.

5. **Rate Limiting**: Implemented using a time-based approach with a processing lock.

## Limitations

1. In-memory storage means data is lost on server restart
2. No persistence layer for long-term storage
3. No authentication/authorization
4. No horizontal scaling support

## Future Improvements

1. Add database persistence
2. Implement authentication
3. Add monitoring and logging
4. Support horizontal scaling
5. Add more comprehensive error handling
6. Implement retry mechanisms for failed batches # LoopAiApi
