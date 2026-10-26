from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workcell.cli import demo, verify
from workcell.core import MAX_ATTEMPTS, Workcell, WorkcellError, job_id, mock_ocr, verify_job

ROOT = Path(__file__).resolve().parent.parent
A = (ROOT / "fixtures" / "synthetic-a.svg").read_bytes()
B = (ROOT / "fixtures" / "synthetic-b.svg").read_bytes()


class WorkcellTests(unittest.TestCase):
    def setUp(self) -> None:
        work_temp = ROOT / "_tmp"
        work_temp.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=work_temp)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_deterministic_identity_and_delivery_checksums(self) -> None:
        cell = Workcell(self.root)
        first = cell.submit(A)
        self.assertEqual(first["job_id"], job_id(A))
        complete = cell.advance(first["job_id"])
        self.assertEqual(complete["state"], "DELIVERED")
        self.assertEqual([e["worker"] for e in complete["events"] if "worker" in e],
                         ["ocr-node", "ocr-node", "validation-node", "results-node"])
        self.assertEqual(verify_job(self.root, first["job_id"])["delivery_sha256"], complete["result_sha256"])
        result = json.loads((self.root / "results" / f"{first['job_id']}.json").read_text())
        self.assertEqual(result["manual_review"]["status"], "REQUIRED")
        self.assertEqual(result["derived"]["line_count"], 5)

    def test_duplicate_submission_does_not_mutate_or_redeliver(self) -> None:
        cell = Workcell(self.root)
        identifier = cell.submit(A)["job_id"]
        cell.advance(identifier)
        manifest = self.root / "jobs" / identifier / "manifest.json"
        before = manifest.read_bytes()
        self.assertEqual(cell.submit(A)["job_id"], identifier)
        self.assertEqual(cell.advance(identifier)["state"], "DELIVERED")
        self.assertEqual(manifest.read_bytes(), before)
        self.assertEqual(len(list((self.root / "results").glob("*.json"))), 1)

    def test_unavailable_worker_holds_then_recovers(self) -> None:
        cell = Workcell(self.root, available={"ocr": False})
        identifier = cell.submit(B)["job_id"]
        held = cell.advance(identifier)
        self.assertEqual((held["state"], held["attempts"]), ("WAITING_WORKER", 0))
        cell.available["ocr"] = True
        done = cell.advance(identifier)
        self.assertEqual(done["state"], "DELIVERED")
        self.assertIn("CAPABILITY_UNAVAILABLE", [e.get("code") for e in done["events"]])

    def test_validation_worker_can_wait_without_repeating_ocr(self) -> None:
        cell = Workcell(self.root, available={"validate": False})
        identifier = cell.submit(A)["job_id"]
        held = cell.advance(identifier)
        self.assertEqual((held["state"], held["phase"], held["attempts"]), ("WAITING_WORKER", "validate", 1))
        cell.available["validate"] = True
        done = cell.advance(identifier)
        self.assertEqual((done["state"], done["attempts"]), ("DELIVERED", 1))

    def test_transient_failure_retries_once_and_stops_at_limit(self) -> None:
        cell = Workcell(self.root)
        identifier = cell.submit(A)["job_id"]
        pending = cell.advance(identifier, fail_first_attempts=1)
        self.assertEqual((pending["state"], pending["attempts"]), ("RETRY_PENDING", 1))
        done = cell.advance(identifier, fail_first_attempts=1)
        self.assertEqual((done["state"], done["attempts"]), ("DELIVERED", MAX_ATTEMPTS))
        other = cell.submit(B)["job_id"]
        self.assertEqual(cell.advance(other, fail_first_attempts=2)["state"], "RETRY_PENDING")
        failed = cell.advance(other, fail_first_attempts=2)
        self.assertEqual((failed["state"], failed["attempts"]), ("FAILED", MAX_ATTEMPTS))
        self.assertEqual(cell.advance(other)["state"], "FAILED")

    def test_tamper_fails_checksum_validation(self) -> None:
        cell = Workcell(self.root)
        identifier = cell.submit(A)["job_id"]
        cell.advance(identifier)
        (self.root / "jobs" / identifier / "result.json").write_bytes(b"changed")
        with self.assertRaisesRegex(WorkcellError, "Checksum mismatch: result_sha256"):
            verify_job(self.root, identifier)

    def test_event_log_tamper_fails_verification(self) -> None:
        cell = Workcell(self.root)
        identifier = cell.submit(A)["job_id"]
        cell.advance(identifier)
        log = self.root / "jobs" / identifier / "events.jsonl"
        log.write_bytes(log.read_bytes().replace(b"ocr-node", b"other-node"))
        with self.assertRaisesRegex(WorkcellError, "Event log differs"):
            verify_job(self.root, identifier)

    def test_rejects_non_synthetic_input_before_retention(self) -> None:
        with self.assertRaisesRegex(WorkcellError, "SYNTHETIC DEMO"):
            Workcell(self.root).submit(b'<svg xmlns="http://www.w3.org/2000/svg"><text>PRIVATE</text></svg>')
        self.assertFalse((self.root / "jobs").exists())

    def test_logs_are_redacted_and_mock_is_labeled(self) -> None:
        cell = Workcell(self.root)
        identifier = cell.submit(A)["job_id"]
        cell.advance(identifier)
        log = (self.root / "jobs" / identifier / "events.jsonl").read_text()
        for event in log.splitlines():
            self.assertIsInstance(json.loads(event), dict)
        self.assertNotIn("Project packet A", log)
        self.assertNotIn(identifier, log)
        self.assertNotIn(str(self.root), log)
        self.assertIn("mock", verify_job(self.root, identifier)["ocr_mode"])
        self.assertIn("Project packet A", mock_ocr(A))

    def test_demo_is_reproducible_and_verifiable(self) -> None:
        first, second = self.root / "one", self.root / "two"
        demo(first)
        demo(second)
        self.assertEqual((first / "index.html").read_bytes(), (second / "index.html").read_bytes())
        self.assertEqual((first / "summary.json").read_bytes(), (second / "summary.json").read_bytes())
        self.assertEqual(len(verify(first)), 2)


if __name__ == "__main__":
    unittest.main()
