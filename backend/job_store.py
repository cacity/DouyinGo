from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from backend.schemas import DownloadJob, JobStatus


TERMINAL_STATUSES = (
    JobStatus.SUCCESS.value,
    JobStatus.ERROR.value,
    JobStatus.CANCELLED.value,
)


class JobStore:
    def __init__(self, database_path: str | Path, max_terminal_jobs: int = 500):
        self.database_path = str(database_path)
        self.max_terminal_jobs = max_terminal_jobs
        self._lock = threading.RLock()

        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

        self._connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False,
            timeout=5,
        )
        with self._connection:
            self._connection.execute("PRAGMA busy_timeout = 5000")
            if self.database_path != ":memory:":
                self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS download_jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_download_jobs_created_at "
                "ON download_jobs(created_at DESC)"
            )

    def load_jobs(self) -> list[DownloadJob]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT payload FROM download_jobs ORDER BY created_at DESC"
            ).fetchall()

        jobs: list[DownloadJob] = []
        for (payload,) in rows:
            try:
                jobs.append(DownloadJob.model_validate_json(payload))
            except ValueError:
                # Ignore records from an incompatible or partially written schema.
                continue
        return jobs

    def save(self, job: DownloadJob) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO download_jobs(id, status, created_at, updated_at, payload)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    payload = excluded.payload
                """,
                (
                    job.id,
                    job.status.value,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                    job.model_dump_json(),
                ),
            )
            self._prune_terminal_jobs()

    def delete(self, job_id: str) -> bool:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                "DELETE FROM download_jobs WHERE id = ?",
                (job_id,),
            )
            return cursor.rowcount > 0

    def delete_terminal(self) -> int:
        placeholders = ", ".join("?" for _ in TERMINAL_STATUSES)
        with self._lock, self._connection:
            cursor = self._connection.execute(
                f"DELETE FROM download_jobs WHERE status IN ({placeholders})",
                TERMINAL_STATUSES,
            )
            return cursor.rowcount

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def _prune_terminal_jobs(self) -> None:
        if self.max_terminal_jobs < 0:
            return
        placeholders = ", ".join("?" for _ in TERMINAL_STATUSES)
        self._connection.execute(
            f"""
            DELETE FROM download_jobs
            WHERE status IN ({placeholders})
              AND id NOT IN (
                  SELECT id FROM download_jobs
                  WHERE status IN ({placeholders})
                  ORDER BY created_at DESC
                  LIMIT ?
              )
            """,
            (*TERMINAL_STATUSES, *TERMINAL_STATUSES, self.max_terminal_jobs),
        )
