import json
import logging
from datetime import datetime
from pathlib import Path

class Telemetry:
    def __init__(self, log_path: str = "./telemetry.jsonl"):
        self.log_path = Path(log_path)

    def _write(self, event: dict):
        event["timestamp"] = datetime.utcnow().isoformat()
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def log_write(self, memory_id: str):
        self._write({"event": "write", "memory_id": memory_id})

    def log_read(self, memory_id: str, similarity_score: float = None):
        self._write({"event": "read", "memory_id": memory_id, "similarity_score": similarity_score})

    def log_search(self, query: str, results: list):
        top_sim = results[0][1] if results else None
        self._write({
            "event": "search",
            "query_preview": query[:50],
            "n_results": len(results),
            "top_similarity": top_sim,
        })
