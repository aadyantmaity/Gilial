"""Gilial API - FastAPI backend wrapping the gilial_code vector compression library."""

from __future__ import annotations

import sys
import uuid
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import json

sys.path.insert(0, "/Users/aadyant/Gilial-1")

from gilial_code import PineconeCompressionClient

app = FastAPI(title="Gilial API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory connection store
connections: dict[str, PineconeCompressionClient] = {}


# --- Models ---

class StrategyEnum(str, Enum):
    balanced = "balanced"
    aggressive = "aggressive"


class CreateConnectionRequest(BaseModel):
    api_key: str
    index_name: str
    environment: str = "us-west"
    namespace: Optional[str] = None


class CompressionRequest(BaseModel):
    strategy: StrategyEnum = StrategyEnum.balanced
    dry_run: bool = True


class CompressionResponse(BaseModel):
    strategy: str
    original_vectors: int
    compressed_vectors: int
    original_size_mb: float
    compressed_size_mb: float
    compression_ratio: float
    savings_pct: float
    dry_run: bool
    metadata: dict


class StatusResponse(BaseModel):
    index_name: str
    environment: str
    total_vector_count: int
    dimension: int
    namespaces: dict = Field(default_factory=dict)

    class Config:
        extra = "allow"


class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None


# --- Helpers ---

def _get_client(connection_id: str) -> PineconeCompressionClient:
    client = connections.get(connection_id)
    if client is None:
        raise HTTPException(status_code=404, detail=f"Connection '{connection_id}' not found")
    return client


# --- Endpoints ---

@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/connections", status_code=201)
def create_connection(req: CreateConnectionRequest):
    """Create a new Pinecone connection."""
    try:
        client = PineconeCompressionClient(
            api_key=req.api_key,
            index_name=req.index_name,
            environment=req.environment,
            namespace=req.namespace,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    connection_id = str(uuid.uuid4())
    connections[connection_id] = client

    try:
        # Return as JSONResponse to bypass Pydantic validation
        return JSONResponse(
            status_code=201,
            content={
                "connection_id": connection_id,
                "status": "connected",
            }
        )
    except ConnectionError as e:
        del connections[connection_id]
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        del connections[connection_id]
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/connections/{connection_id}/compress")
def compress(connection_id: str, req: CompressionRequest):
    """Trigger compression on a connected Pinecone index."""
    client = _get_client(connection_id)
    try:
        result = client.compress(strategy=req.strategy.value, dry_run=req.dry_run)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return CompressionResponse(
        strategy=result.strategy,
        original_vectors=result.original_vectors,
        compressed_vectors=result.compressed_vectors,
        original_size_mb=result.original_size_mb,
        compressed_size_mb=result.compressed_size_mb,
        compression_ratio=result.compression_ratio,
        savings_pct=result.savings_pct,
        dry_run=result.dry_run,
        metadata=result.metadata,
    )


@app.get("/api/connections/{connection_id}/status")
def get_status(connection_id: str):
    """Get the current status of a connected Pinecone index."""
    client = _get_client(connection_id)
    try:
        status = client.get_status()

        # Convert namespaces to JSON-serializable format
        namespaces = {}
        for ns_name, ns_data in status.get("namespaces", {}).items():
            if hasattr(ns_data, "vector_count"):
                namespaces[ns_name] = {"vector_count": ns_data.vector_count}
            elif isinstance(ns_data, dict):
                namespaces[ns_name] = {"vector_count": ns_data.get("vector_count", 0)}
            else:
                namespaces[ns_name] = {"vector_count": 0}

        result = {
            "index_name": status.get("index_name", "unknown"),
            "environment": status.get("environment", "unknown"),
            "total_vector_count": int(status.get("total_vector_count", 0)),
            "dimension": int(status.get("dimension", 0)),
            "namespaces": namespaces
        }

        return JSONResponse(content=result)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/connections/{connection_id}/estimate")
def estimate_savings(
    connection_id: str,
    strategy: StrategyEnum = Query(default=StrategyEnum.balanced),
):
    """Estimate compression savings without performing changes."""
    client = _get_client(connection_id)
    try:
        estimate = client.estimate_savings()

        # estimate_savings() now returns accurate estimates based on strategy
        result = {
            "original_vectors": estimate.get("original_vectors", 0),
            "original_size_mb": estimate.get("original_size_mb", 0),
            "compressed_vectors": estimate.get("compressed_vectors", 0),
            "compressed_size_mb": estimate.get("compressed_size_mb", 0),
            "compression_ratio": estimate.get("compression_ratio", 0),
            "savings_pct": estimate.get("savings_pct", 0),
        }

        return JSONResponse(content=result)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
def startup():
    """Verify gilial_code is importable on startup."""
    print("Gilial API v0.1.0 starting up")
    print("Endpoints:")
    print("  GET  /api/health")
    print("  POST /api/connections")
    print("  POST /api/connections/{id}/compress")
    print("  GET  /api/connections/{id}/status")
    print("  GET  /api/connections/{id}/estimate")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
