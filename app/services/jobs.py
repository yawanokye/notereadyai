import json
import os
import time
import uuid
from pathlib import Path
from typing import Any


class JobStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir / "jobs"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = uuid.uuid4().hex
        job = {
            "job_id": job_id,
            "created_at": time.time(),
            "batches": {},
            **payload,
        }
        self.save(job)
        return job

    def load(self, job_id: str) -> dict[str, Any]:
        path = self._path(job_id)
        if not path.exists():
            raise KeyError("Lecture-note job not found. Start a new generation.")
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, job: dict[str, Any]) -> None:
        path = self._path(job["job_id"])
        temp_path = path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
        os.replace(temp_path, path)

    def _path(self, job_id: str) -> Path:
        if not job_id.isalnum():
            raise KeyError("Invalid job identifier.")
        return self.base_dir / f"{job_id}.json"
