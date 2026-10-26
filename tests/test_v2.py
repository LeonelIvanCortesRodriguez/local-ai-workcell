"""Synthetic v0.2 queue, authentication, OCR, and recovery proofs."""

import json
from contextlib import closing
import multiprocessing as mp
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from workcell.v2 import Coordinator, FIXTURES, ROOT, SAMPLES, Store, locate_tesseract, run_demo

WORK_TEMP = ROOT / "_tmp"
WORK_TEMP.mkdir(exist_ok=True)


class V2StoreTests(unittest.TestCase):
    def test_durable_queue_recovers_claim_after_restart_and_deduplicates(self):
        with TemporaryDirectory(dir=WORK_TEMP) as directory:
            database = Path(directory) / "queue.sqlite3"
            first = Store(database)
            name, expected = SAMPLES[0]
            image = (FIXTURES / name).read_bytes()
            identifier = first.submit(name, image, expected)
            self.assertEqual(identifier, first.submit(name, image, expected))
            self.assertEqual(len(first.summary()["jobs"]), 1)
            self.assertEqual(first.claim("ocr", "synthetic-worker")["id"], identifier)
            first.close()  # A claimed job is left durable, as after coordinator exit.

            restarted = Store(database)
            self.assertEqual(restarted.recover_inflight(), 1)
            job = restarted.claim("ocr", "replacement-worker")
            self.assertEqual(job["id"], identifier)
            self.assertEqual(job["attempts"], 2)
            self.assertEqual(restarted.summary()["jobs"][0]["recoveries"], 1)
            restarted.close()

    def test_private_or_modified_image_is_rejected_before_retention(self):
        with TemporaryDirectory(dir=WORK_TEMP) as directory:
            store = Store(Path(directory) / "queue.sqlite3")
            with self.assertRaises(ValueError):
                store.submit(SAMPLES[0][0], b"not the committed image", SAMPLES[0][1])
            self.assertEqual(store.summary()["jobs"], [])
            store.close()

    def test_restart_after_second_ocr_claim_respects_attempt_limit(self):
        with TemporaryDirectory(dir=WORK_TEMP) as directory:
            database = Path(directory) / "queue.sqlite3"
            first = Store(database)
            name, expected = SAMPLES[0]
            identifier = first.submit(name, (FIXTURES / name).read_bytes(), expected)
            self.assertIsNotNone(first.claim("ocr", "synthetic-worker"))
            first.close()

            second = Store(database)
            self.assertEqual(second.recover_inflight(), 1)
            self.assertEqual(second.claim("ocr", "replacement-worker")["attempts"], 2)
            second.close()

            exhausted = Store(database)
            self.assertEqual(exhausted.recover_inflight(), 1)
            job = exhausted.summary()["jobs"][0]
            self.assertEqual(job["id"], identifier)
            self.assertEqual(job["state"], "FAILED")
            self.assertEqual(job["error"], "OCR_RETRY_LIMIT")
            self.assertEqual(job["attempts"], 2)
            self.assertIsNone(exhausted.claim("ocr", "third-worker"))
            exhausted.close()


@unittest.skipUnless(os.environ.get("WORKCELL_V2_INTEGRATION") == "1", "Requires local loopback sockets and Tesseract")
class V2IntegrationTests(unittest.TestCase):
    def test_wrong_worker_key_cannot_register(self):
        with TemporaryDirectory(dir=WORK_TEMP) as directory:
            store = Store(Path(directory) / "queue.sqlite3")
            coordinator = Coordinator(store, locate_tesseract())
            coordinator.start()
            try:
                with self.assertRaises(mp.AuthenticationError):
                    from multiprocessing.connection import Client
                    Client(coordinator.address, authkey=b"invalid-test-key")
                self.assertEqual(coordinator.registrations, set())
            finally:
                coordinator.stop()
                store.close()

    def test_two_ocr_workers_recover_loopback_interruption_and_deliver_real_ocr(self):
        with TemporaryDirectory(dir=WORK_TEMP) as directory:
            output = Path(directory) / "demo"
            report = run_demo(output, delay=0.25)
            self.assertEqual(report["submitted"], 3)
            self.assertEqual(report["delivered"], 3)
            self.assertEqual(report["failed"], 0)
            self.assertEqual(report["transport_interruptions"], 1)
            self.assertGreaterEqual(report["recovered_jobs"], 1)
            self.assertGreaterEqual(report["max_simultaneous_ocr_leases"], 2)
            self.assertTrue(all(row["result_sha"] for row in report["jobs"]))
            retained = (output / "report.json").read_text(encoding="utf-8")
            self.assertEqual(json.loads(retained), report)
            self.assertNotIn("SYNTHETIC WORKCELL ONE", retained)
            self.assertNotIn(str(Path(directory)), retained)
            with closing(sqlite3.connect(output / "queue.sqlite3")) as database:
                recognized = database.execute(
                    "SELECT fixture,ocr_text,expected FROM jobs ORDER BY fixture"
                ).fetchall()
            self.assertEqual(len(recognized), 3)
            for fixture, ocr_text, expected in recognized:
                with self.subTest(fixture=fixture):
                    self.assertEqual(ocr_text, expected)

    def test_all_worker_processes_register_and_stop(self):
        with TemporaryDirectory(dir=WORK_TEMP) as directory:
            store = Store(Path(directory) / "queue.sqlite3")
            for name, expected in SAMPLES:
                store.submit(name, (FIXTURES / name).read_bytes(), expected)
            coordinator = Coordinator(store, locate_tesseract(), delay=0.25)
            coordinator.start()
            try:
                coordinator.start_worker("ocr", "ocr-1", interrupt_once=True)
                coordinator.start_worker("ocr", "ocr-2")
                coordinator.start_worker("validate", "validate-1")
                self.assertEqual(len(coordinator.processes), 3)
                self.assertTrue(all(process.pid is not None and process.is_alive()
                                    for process in coordinator.processes))
                summary = coordinator.wait(timeout=20)
                self.assertTrue(all(job["state"] == "DELIVERED" for job in summary["jobs"]))
                self.assertEqual(coordinator.registrations,
                                 {"ocr-1", "ocr-2", "validate-1"})
            finally:
                coordinator.stop()
                store.close()
            self.assertTrue(all(not process.is_alive() and process.exitcode == 0
                                for process in coordinator.processes))


if __name__ == "__main__":
    unittest.main()
