"""Local multi-process proof with authenticated loopback workers and durable jobs.

Only the committed synthetic PNG fixtures are accepted by the demo entry point.
This experiment is separate from the v0.1 single-process SVG simulation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
from multiprocessing.connection import Client, Listener
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures" / "v2"
SAMPLES = (
    ("synthetic-1.png", "SYNTHETIC WORKCELL ONE"),
    ("synthetic-2.png", "SYNTHETIC WORKCELL TWO"),
    ("synthetic-3.png", "SYNTHETIC WORKCELL THREE"),
)
TERMINAL = {"DELIVERED", "FAILED"}
MAX_OCR_ATTEMPTS = 2


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(text: str) -> str:
    return " ".join(text.upper().split())


def locate_tesseract(explicit: str | None = None) -> str:
    found = explicit or shutil.which("tesseract")
    if not found and os.name == "nt":
        candidate = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
        if candidate.is_file():
            found = str(candidate)
    if not found or not Path(found).is_file():
        raise RuntimeError("Tesseract executable is required for the v0.2 OCR adapter")
    return str(found)


class Store:
    """One locked SQLite connection; commits make queue state restartable."""

    def __init__(self, path: Path):
        self.path = path
        self.db = sqlite3.connect(path, check_same_thread=False, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        with self.lock:
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                  id TEXT PRIMARY KEY, fixture TEXT NOT NULL, image BLOB NOT NULL,
                  expected TEXT NOT NULL, input_sha TEXT NOT NULL,
                  state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                  ocr_text TEXT, ocr_ms INTEGER, result_sha TEXT,
                  recoveries INTEGER NOT NULL DEFAULT 0, error TEXT,
                  submitted REAL NOT NULL, finished REAL
                );
                CREATE TABLE IF NOT EXISTS events (
                  seq INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL,
                  state TEXT NOT NULL, reason TEXT NOT NULL, worker TEXT NOT NULL
                );
            """)
            self.db.commit()

    def close(self) -> None:
        with self.lock:
            self.db.close()

    def _event(self, job_id: str, state: str, reason: str, worker: str) -> None:
        self.db.execute(
            "INSERT INTO events(job_id,state,reason,worker) VALUES(?,?,?,?)",
            (job_id, state, reason, worker),
        )

    def submit(self, fixture: str, image: bytes, expected: str) -> str:
        known = dict(SAMPLES)
        if (fixture not in known or expected != known[fixture]
                or len(image) > 2_000_000 or image != (FIXTURES / fixture).read_bytes()):
            raise ValueError("Only the committed synthetic fixtures are accepted")
        identifier = sha(image)[:20]
        with self.lock:
            exists = self.db.execute("SELECT 1 FROM jobs WHERE id=?", (identifier,)).fetchone()
            if not exists:
                self.db.execute(
                    "INSERT INTO jobs(id,fixture,image,expected,input_sha,state,submitted) "
                    "VALUES(?,?,?,?,?,'QUEUED_OCR',?)",
                    (identifier, fixture, image, expected, sha(image), time.time()),
                )
                self._event(identifier, "QUEUED_OCR", "SUBMITTED", "coordinator")
                self.db.commit()
        return identifier

    def recover_inflight(self) -> int:
        """On process restart, return claimed jobs to the durable queue."""
        with self.lock:
            rows = self.db.execute(
                "SELECT id,state,attempts FROM jobs WHERE state IN ('OCR_RUNNING','VALIDATING')"
            ).fetchall()
            for row in rows:
                if row["state"] == "OCR_RUNNING" and row["attempts"] >= MAX_OCR_ATTEMPTS:
                    self.db.execute(
                        "UPDATE jobs SET state='FAILED',error='OCR_RETRY_LIMIT',finished=? WHERE id=?",
                        (time.time(), row["id"]),
                    )
                    self._event(row["id"], "FAILED", "OCR_RETRY_LIMIT", "coordinator")
                    continue
                next_state = "QUEUED_OCR" if row["state"] == "OCR_RUNNING" else "QUEUED_VALIDATE"
                self.db.execute(
                    "UPDATE jobs SET state=?, recoveries=recoveries+1 WHERE id=?",
                    (next_state, row["id"]),
                )
                self._event(row["id"], next_state, "COORDINATOR_RESTART", "coordinator")
            self.db.commit()
            return len(rows)

    def claim(self, role: str, worker: str) -> dict | None:
        queued = "QUEUED_OCR" if role == "ocr" else "QUEUED_VALIDATE"
        running = "OCR_RUNNING" if role == "ocr" else "VALIDATING"
        with self.lock:
            row = self.db.execute(
                "SELECT * FROM jobs WHERE state=? ORDER BY submitted,id LIMIT 1", (queued,)
            ).fetchone()
            if row is None:
                return None
            attempts = row["attempts"] + (1 if role == "ocr" else 0)
            self.db.execute(
                "UPDATE jobs SET state=?,attempts=? WHERE id=?",
                (running, attempts, row["id"]),
            )
            self._event(row["id"], running, "CLAIMED", worker)
            self.db.commit()
            result = dict(row)
            result["attempts"] = attempts
            return result

    def requeue(self, job_id: str, role: str, worker: str) -> None:
        expected = "OCR_RUNNING" if role == "ocr" else "VALIDATING"
        queued = "QUEUED_OCR" if role == "ocr" else "QUEUED_VALIDATE"
        with self.lock:
            row = self.db.execute("SELECT state,attempts FROM jobs WHERE id=?", (job_id,)).fetchone()
            if row is None or row["state"] != expected:
                return
            if role == "ocr" and row["attempts"] >= MAX_OCR_ATTEMPTS:
                self.db.execute(
                    "UPDATE jobs SET state='FAILED',error='OCR_RETRY_LIMIT',finished=? WHERE id=?",
                    (time.time(), job_id),
                )
                self._event(job_id, "FAILED", "OCR_RETRY_LIMIT", worker)
            else:
                self.db.execute(
                    "UPDATE jobs SET state=?,recoveries=recoveries+1 WHERE id=?",
                    (queued, job_id),
                )
                self._event(job_id, queued, "TRANSPORT_DISCONNECT", worker)
            self.db.commit()

    def complete(self, job_id: str, role: str, payload: dict, worker: str) -> None:
        with self.lock:
            expected_state = "OCR_RUNNING" if role == "ocr" else "VALIDATING"
            row = self.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if row is None or row["state"] != expected_state:
                raise RuntimeError("Stale or unknown worker result")
            if role == "ocr":
                if payload.get("error"):
                    self.db.execute(
                        "UPDATE jobs SET state='FAILED',error=?,finished=? WHERE id=?",
                        ("OCR_ERROR", time.time(), job_id),
                    )
                    self._event(job_id, "FAILED", "OCR_ERROR", worker)
                else:
                    text = str(payload["text"])
                    self.db.execute(
                        "UPDATE jobs SET state='QUEUED_VALIDATE',ocr_text=?,ocr_ms=? WHERE id=?",
                        (text, int(payload["ocr_ms"]), job_id),
                    )
                    self._event(job_id, "QUEUED_VALIDATE", "OCR_RESULT_HASHED", worker)
            else:
                if payload.get("valid") is True and row["ocr_text"] is not None:
                    result_sha = sha(row["ocr_text"].encode("utf-8"))
                    self.db.execute(
                        "UPDATE jobs SET state='DELIVERED',result_sha=?,finished=? WHERE id=?",
                        (result_sha, time.time(), job_id),
                    )
                    self._event(job_id, "DELIVERED", "VALIDATED_ONCE", worker)
                else:
                    self.db.execute(
                        "UPDATE jobs SET state='FAILED',error='OCR_TEXT_MISMATCH',finished=? WHERE id=?",
                        (time.time(), job_id),
                    )
                    self._event(job_id, "FAILED", "OCR_TEXT_MISMATCH", worker)
            self.db.commit()

    def summary(self) -> dict:
        with self.lock:
            rows = [dict(row) for row in self.db.execute(
                "SELECT id,fixture,input_sha,state,attempts,ocr_ms,result_sha,recoveries,error "
                "FROM jobs ORDER BY fixture"
            )]
            events = [dict(row) for row in self.db.execute(
                "SELECT job_id,state,reason,worker FROM events ORDER BY seq"
            )]
        return {"jobs": rows, "events": events}


def worker_main(address: tuple, authkey: bytes, role: str, name: str,
                tesseract: str, delay: float, interrupt_once: bool) -> None:
    interrupted = False
    while True:
        connection = Client(address, authkey=authkey)
        connection.send({"role": role, "name": name})
        try:
            while True:
                message = connection.recv()
                if message["kind"] == "stop":
                    return
                if interrupt_once and not interrupted:
                    interrupted = True
                    connection.close()  # Synthetic loopback transport loss before a result.
                    time.sleep(0.08)
                    break
                job = message["job"]
                if delay:
                    time.sleep(delay)
                if role == "ocr":
                    started = time.perf_counter()
                    with tempfile.TemporaryDirectory(prefix="workcell-v2-") as temporary:
                        image = Path(temporary) / "synthetic.png"
                        image.write_bytes(job["image"])
                        process = subprocess.run(
                            [tesseract, str(image), "stdout", "--psm", "6"],
                            capture_output=True, text=True, timeout=15, check=False,
                        )
                    elapsed = round((time.perf_counter() - started) * 1000)
                    payload = ({"text": normalize(process.stdout), "ocr_ms": elapsed}
                               if process.returncode == 0 else {"error": "OCR_ERROR"})
                else:
                    payload = {"valid": normalize(job["ocr_text"] or "") == normalize(job["expected"])}
                connection.send({"kind": "result", "job_id": job["id"], "payload": payload})
        except (EOFError, OSError):
            return
        finally:
            connection.close()


class Coordinator:
    def __init__(self, store: Store, tesseract: str, delay: float = 0.15):
        self.store = store
        self.tesseract = tesseract
        self.delay = delay
        self.authkey = secrets.token_bytes(32)
        self.listener = Listener(("127.0.0.1", 0), authkey=self.authkey)
        self.address = self.listener.address
        self.stop_event = threading.Event()
        self.threads: list[threading.Thread] = []
        self.processes: list[mp.Process] = []
        self.registrations: set[str] = set()
        self.lock = threading.Lock()
        self.active_ocr = 0
        self.max_ocr_leases = 0
        self.accept_thread = threading.Thread(target=self._accept, daemon=True)

    def start(self) -> None:
        self.store.recover_inflight()
        self.accept_thread.start()

    def start_worker(self, role: str, name: str, interrupt_once: bool = False) -> None:
        if role not in {"ocr", "validate"}:
            raise ValueError("Unknown capability")
        process = mp.Process(
            target=worker_main,
            args=(self.address, self.authkey, role, name, self.tesseract, self.delay, interrupt_once),
            name=name,
        )
        process.start()
        self.processes.append(process)

    def _accept(self) -> None:
        while not self.stop_event.is_set():
            try:
                connection = self.listener.accept()
            except mp.AuthenticationError:
                continue  # A connection without the ephemeral key cannot register.
            except (OSError, EOFError):
                break
            thread = threading.Thread(target=self._serve, args=(connection,), daemon=True)
            self.threads.append(thread)
            thread.start()

    def _serve(self, connection) -> None:
        current = None
        role = ""
        name = ""
        try:
            hello = connection.recv()
            role, name = hello.get("role"), hello.get("name")
            if role not in {"ocr", "validate"} or not isinstance(name, str) or len(name) > 40:
                return
            with self.lock:
                self.registrations.add(name)
            while not self.stop_event.is_set():
                current = self.store.claim(role, name)
                if current is None:
                    time.sleep(0.02)
                    continue
                if role == "ocr":
                    with self.lock:
                        self.active_ocr += 1
                        self.max_ocr_leases = max(self.max_ocr_leases, self.active_ocr)
                connection.send({"kind": "job", "job": current})
                response = connection.recv()
                if response.get("kind") != "result" or response.get("job_id") != current["id"]:
                    raise RuntimeError("Worker response does not match assigned job")
                self.store.complete(current["id"], role, response["payload"], name)
                if role == "ocr":
                    with self.lock:
                        self.active_ocr -= 1
                current = None
        except (EOFError, OSError, RuntimeError):
            if current is not None:
                self.store.requeue(current["id"], role, name)
                if role == "ocr":
                    with self.lock:
                        self.active_ocr -= 1
        finally:
            try:
                connection.send({"kind": "stop"})
            except (OSError, EOFError):
                pass
            connection.close()

    def wait(self, timeout: float = 30) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            summary = self.store.summary()
            if summary["jobs"] and all(row["state"] in TERMINAL for row in summary["jobs"]):
                return summary
            time.sleep(0.04)
        raise TimeoutError("Synthetic v0.2 jobs did not reach terminal states")

    def stop(self) -> None:
        self.stop_event.set()
        for thread in self.threads:
            thread.join(timeout=1)
        for process in self.processes:
            process.join(timeout=2)
            if process.is_alive():
                process.terminate()
                process.join(timeout=2)
        self.listener.close()


def run_demo(output: Path, tesseract: str | None = None, delay: float = 0.15) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be absent or empty")
    binary = locate_tesseract(tesseract)
    output.mkdir(parents=True, exist_ok=True)
    store = Store(output / "queue.sqlite3")
    for name, expected in SAMPLES:
        store.submit(name, (FIXTURES / name).read_bytes(), expected)
    coordinator = Coordinator(store, binary, delay)
    engine_version = subprocess.run(
        [binary, "--version"], capture_output=True, text=True, timeout=5, check=True
    ).stdout.splitlines()[0]
    started = time.perf_counter()
    try:
        coordinator.start()
        coordinator.start_worker("ocr", "ocr-1", interrupt_once=True)
        coordinator.start_worker("ocr", "ocr-2")
        coordinator.start_worker("validate", "validate-1")
        summary = coordinator.wait()
    finally:
        coordinator.stop()
    jobs = summary["jobs"]
    report = {
        "schema": "workcell-v2-synthetic-v1",
        "boundary": "Loopback-only multi-process experiment; public synthetic PNGs; no real node",
        "ocr_engine": engine_version,
        "submitted": len(jobs),
        "delivered": sum(row["state"] == "DELIVERED" for row in jobs),
        "failed": sum(row["state"] == "FAILED" for row in jobs),
        "transport_interruptions": sum(event["reason"] == "TRANSPORT_DISCONNECT" for event in summary["events"]),
        "recovered_jobs": sum(row["recoveries"] > 0 for row in jobs),
        "max_simultaneous_ocr_leases": coordinator.max_ocr_leases,
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
        "jobs": [
            {key: row[key] for key in ("id", "fixture", "input_sha", "state", "attempts", "ocr_ms", "result_sha", "recoveries", "error")}
            for row in jobs
        ],
        "events": summary["events"],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    store.close()
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("demo", choices=["demo"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tesseract")
    args = parser.parse_args()
    report = run_demo(args.output, args.tesseract)
    print(
        f"V2_DEMO_OK delivered={report['delivered']}/{report['submitted']} "
        f"interruptions={report['transport_interruptions']} "
        f"recovered={report['recovered_jobs']} "
        f"max_ocr_leases={report['max_simultaneous_ocr_leases']} "
        f"elapsed_ms={report['elapsed_ms']}"
    )


if __name__ == "__main__":
    mp.freeze_support()
    main()
