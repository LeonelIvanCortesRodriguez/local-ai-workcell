"""Deterministic job routing with a deliberately simulated OCR worker."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree

PIPELINE_VERSION = "1"
MAX_INPUT_BYTES = 200_000
MAX_ATTEMPTS = 2
PHASES = ("ocr", "validate", "results")
DEFAULT_NODES = {"ocr": "ocr-node", "validate": "validation-node", "results": "results-node"}
TERMINAL = {"DELIVERED", "FAILED"}
TRANSITIONS = {
    "NEW": {"ROUTED", "WAITING_WORKER"},
    "WAITING_WORKER": {"ROUTED", "OCR_DONE", "VALIDATED", "DELIVERED"},
    "ROUTED": {"OCR_DONE", "RETRY_PENDING", "FAILED"},
    "RETRY_PENDING": {"ROUTED", "WAITING_WORKER"},
    "OCR_DONE": {"VALIDATED", "WAITING_WORKER"},
    "VALIDATED": {"DELIVERED", "WAITING_WORKER"},
    "DELIVERED": set(),
    "FAILED": set(),
}


class WorkcellError(ValueError):
    """A state, fixture, or checksum violates the public workflow contract."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def job_id(document: bytes) -> str:
    return sha256(b"local-ai-workcell:" + PIPELINE_VERSION.encode() + b"\0" + document)[:16]


def mock_ocr(document: bytes) -> str:
    """Read SVG text nodes as a deterministic OCR stand-in; no image recognition occurs."""
    if len(document) > MAX_INPUT_BYTES:
        raise WorkcellError("Fixture exceeds the synthetic input limit")
    try:
        root = ElementTree.fromstring(document)
    except ElementTree.ParseError as exc:
        raise WorkcellError("Synthetic SVG is malformed") from exc
    if not root.tag.endswith("svg"):
        raise WorkcellError("Only synthetic SVG fixtures are supported")
    lines = [" ".join("".join(node.itertext()).split()) for node in root.iter() if node.tag.endswith("text")]
    lines = [line for line in lines if line]
    if not lines or lines[0] != "SYNTHETIC DEMO" or len(lines) < 3:
        raise WorkcellError("Fixture must start with SYNTHETIC DEMO and contain three text lines")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _event_bytes(events: list[dict]) -> bytes:
    return b"".join((json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8") for event in events)


def _transition(manifest: dict, state: str, *, worker: str | None = None, code: str | None = None) -> None:
    current = manifest["state"]
    if state not in TRANSITIONS[current]:
        raise WorkcellError(f"Illegal transition: {current} -> {state}")
    manifest["state"] = state
    event = {"seq": len(manifest["events"]) + 1, "state": state, "phase": manifest["phase"]}
    if worker:
        event["worker"] = worker
    if code:
        event["code"] = code
    manifest["events"].append(event)


def verify_job(output: Path, identifier: str) -> dict:
    """Check every materialized artifact against the manifest's checksum chain."""
    if len(identifier) != 16 or any(c not in "0123456789abcdef" for c in identifier):
        raise WorkcellError("Invalid job ID")
    folder = output / "jobs" / identifier
    manifest = _load_json(folder / "manifest.json")
    if manifest["job_id"] != identifier or job_id((folder / "input.svg").read_bytes()) != identifier:
        raise WorkcellError("Input identity mismatch")
    checks = [("input_sha256", folder / "input.svg"), ("ocr_sha256", folder / "ocr.txt"),
              ("result_sha256", folder / "result.json"), ("delivery_sha256", output / "results" / f"{identifier}.json")]
    for field, path in checks:
        expected = manifest.get(field)
        if expected is not None and (not path.is_file() or sha256(path.read_bytes()) != expected):
            raise WorkcellError(f"Checksum mismatch: {field}")
    if manifest["state"] == "DELIVERED" and any(manifest.get(field) is None for field, _ in checks):
        raise WorkcellError("Delivered job has an incomplete checksum chain")
    if not 0 <= manifest["attempts"] <= MAX_ATTEMPTS:
        raise WorkcellError("OCR retry limit exceeded")
    events = manifest["events"]
    if not events or events[0] != {"seq": 1, "state": "NEW", "phase": "ocr", "code": "SUBMITTED"}:
        raise WorkcellError("Invalid initial event")
    if any(event["seq"] != index for index, event in enumerate(events, 1)):
        raise WorkcellError("Event sequence is not contiguous")
    previous = "NEW"
    for event in events[1:]:
        if event["state"] not in TRANSITIONS[previous]:
            raise WorkcellError("Event transition is invalid")
        previous = event["state"]
    if events[-1]["state"] != manifest["state"]:
        raise WorkcellError("Manifest state differs from event trail")
    if (folder / "events.jsonl").read_bytes() != _event_bytes(events):
        raise WorkcellError("Event log differs from manifest trail")
    return manifest


class Workcell:
    def __init__(self, output: Path, *, available: dict[str, bool] | None = None):
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.available = {phase: True for phase in PHASES}
        if available:
            self.available.update(available)

    def _persist(self, manifest: dict) -> None:
        folder = self.output / "jobs" / manifest["job_id"]
        _write_json(folder / "manifest.json", manifest)
        (folder / "events.jsonl").write_bytes(_event_bytes(manifest["events"]))

    def submit(self, document: bytes) -> dict:
        mock_ocr(document)  # Enforce synthetic-only input before retaining bytes.
        identifier = job_id(document)
        folder = self.output / "jobs" / identifier
        if (folder / "manifest.json").exists():
            return verify_job(self.output, identifier)  # Duplicate submission is read-only.
        folder.mkdir(parents=True, exist_ok=False)
        (folder / "input.svg").write_bytes(document)
        manifest = {
            "schema": "local-ai-workcell-demo-v1", "job_id": identifier,
            "pipeline_version": PIPELINE_VERSION, "input_sha256": sha256(document),
            "ocr_sha256": None, "result_sha256": None, "delivery_sha256": None,
            "phase": "ocr", "state": "NEW", "attempts": 0, "max_attempts": MAX_ATTEMPTS,
            "ocr_mode": "deterministic SVG text-node mock; no optical recognition",
            "events": [{"seq": 1, "state": "NEW", "phase": "ocr", "code": "SUBMITTED"}],
        }
        self._persist(manifest)
        return manifest

    def advance(self, identifier: str, *, fail_first_attempts: int = 0) -> dict:
        manifest = verify_job(self.output, identifier)
        if manifest["state"] in TERMINAL:
            return manifest
        folder = self.output / "jobs" / identifier
        while manifest["phase"] in PHASES:
            phase = manifest["phase"]
            if not self.available[phase]:
                if manifest["state"] != "WAITING_WORKER":
                    _transition(manifest, "WAITING_WORKER", code="CAPABILITY_UNAVAILABLE")
                    self._persist(manifest)
                return manifest
            worker = DEFAULT_NODES[phase]
            if phase == "ocr":
                _transition(manifest, "ROUTED", worker=worker)
                manifest["attempts"] += 1
                if manifest["attempts"] <= fail_first_attempts:
                    state = "FAILED" if manifest["attempts"] >= MAX_ATTEMPTS else "RETRY_PENDING"
                    _transition(manifest, state, worker=worker, code="SIMULATED_TRANSIENT_FAILURE")
                    self._persist(manifest)
                    return manifest
                ocr = mock_ocr((folder / "input.svg").read_bytes()).encode("utf-8")
                (folder / "ocr.txt").write_bytes(ocr)
                manifest["ocr_sha256"] = sha256(ocr)
                _transition(manifest, "OCR_DONE", worker=worker)
                manifest["phase"] = "validate"
            elif phase == "validate":
                lines = (folder / "ocr.txt").read_text(encoding="utf-8").splitlines()
                if lines[0] != "SYNTHETIC DEMO" or len(lines) < 3:
                    raise WorkcellError("Mock OCR output failed validation")
                result = {
                    "job_id": identifier,
                    "source": {"input_sha256": manifest["input_sha256"], "ocr_sha256": manifest["ocr_sha256"]},
                    "derived": {"line_count": len(lines), "word_count": sum(len(line.split()) for line in lines)},
                    "manual_review": {"status": "REQUIRED", "reason": "Mock OCR carries no recognition-accuracy evidence"},
                }
                data = canonical_json(result)
                (folder / "result.json").write_bytes(data)
                manifest["result_sha256"] = sha256(data)
                _transition(manifest, "VALIDATED", worker=worker)
                manifest["phase"] = "results"
            else:
                data = (folder / "result.json").read_bytes()
                destination = self.output / "results" / f"{identifier}.json"
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists() and destination.read_bytes() != data:
                    raise WorkcellError("Conflicting delivery already exists")
                destination.write_bytes(data)
                manifest["delivery_sha256"] = sha256(data)
                _transition(manifest, "DELIVERED", worker=worker)
                manifest["phase"] = "complete"
            self._persist(manifest)
        return verify_job(self.output, identifier)
