"""Run and verify the local synthetic workcell."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import Workcell, WorkcellError, canonical_json, verify_job
from .view import render_status

ROOT = Path(__file__).resolve().parent.parent


def demo(output: Path) -> list[dict]:
    if output.exists() and any(output.iterdir()):
        raise WorkcellError("Demo output directory must be empty")
    cell = Workcell(output)
    first = cell.submit((ROOT / "fixtures" / "synthetic-a.svg").read_bytes())
    cell.advance(first["job_id"])
    duplicate = cell.submit((ROOT / "fixtures" / "synthetic-a.svg").read_bytes())
    if duplicate["job_id"] != first["job_id"]:
        raise WorkcellError("Duplicate submit changed job identity")
    cell.available["ocr"] = False
    second = cell.submit((ROOT / "fixtures" / "synthetic-b.svg").read_bytes())
    waiting = cell.advance(second["job_id"])
    if waiting["state"] != "WAITING_WORKER" or waiting["attempts"] != 0:
        raise WorkcellError("Unavailable worker did not hold without consuming an attempt")
    cell.available["ocr"] = True
    retry = cell.advance(second["job_id"], fail_first_attempts=1)
    if retry["state"] != "RETRY_PENDING":
        raise WorkcellError("Simulated first attempt did not schedule bounded retry")
    cell.advance(second["job_id"], fail_first_attempts=1)
    final = [verify_job(output, identifier) for identifier in sorted((first["job_id"], second["job_id"]))]
    if any(item["state"] != "DELIVERED" for item in final):
        raise WorkcellError("Demo did not deliver both jobs")
    (output / "index.html").write_text(render_status(final), encoding="utf-8", newline="\n")
    (output / "summary.json").write_bytes(canonical_json({
        "schema": "local-ai-workcell-summary-v1", "jobs": len(final),
        "delivered": 2, "retried": 1, "ocr_mode": "deterministic SVG text-node mock",
        "job_ids": [item["job_id"] for item in final],
    }))
    return final


def verify(output: Path) -> list[dict]:
    folders = sorted((output / "jobs").glob("*/manifest.json"))
    if len(folders) != 2:
        raise WorkcellError("Demo must contain exactly two jobs")
    items = [verify_job(output, path.parent.name) for path in folders]
    if any(item["state"] != "DELIVERED" for item in items):
        raise WorkcellError("Demo has undelivered jobs")
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    if summary["job_ids"] != [item["job_id"] for item in items]:
        raise WorkcellError("Summary does not match jobs")
    if (output / "index.html").read_text(encoding="utf-8") != render_status(items):
        raise WorkcellError("Status view does not match manifests")
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Local AI Workcell synthetic simulation")
    parser.add_argument("command", choices=("demo", "verify"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        items = demo(args.output) if args.command == "demo" else verify(args.output)
    except (WorkcellError, OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"WORKCELL_ERROR: {exc}\n")
    print(f"WORKCELL_{args.command.upper()}_OK jobs={len(items)} delivered={sum(i['state'] == 'DELIVERED' for i in items)} retried={sum(i['attempts'] > 1 for i in items)}")


if __name__ == "__main__":
    main()
