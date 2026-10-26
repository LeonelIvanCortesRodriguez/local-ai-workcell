# v0.2 local multi-process proof

This is a separate experiment beside the v0.1 one-process SVG simulation. It runs a coordinator, two OCR worker processes, and one validation worker process on one computer. Workers connect over loopback through Python's authenticated `multiprocessing.connection` challenge/response. The key is generated for each run and is not written to disk. This does not establish transport security for remote machines.

## Route and recovery

```text
synthetic PNG -> durable SQLite queue -> OCR worker (Tesseract) -> validation worker -> delivered hash
                          |                    |
                          |                    +-- disconnect before result -> requeue -> other OCR worker
                          +-- coordinator restart -> in-flight claim requeued
```

The coordinator admits only the three committed fictional PNGs. It stores the input bytes and expected text in a local SQLite queue under the user-selected output directory. The output directory is ignored by Git and excluded from the public source package. A duplicate byte submission returns the same job ID. A claimed job is committed before worker execution; on restart, an in-flight OCR or validation state returns to the durable queue. OCR claims are limited to two attempts.

The first OCR worker deliberately drops its authenticated loopback connection before returning one result. The coordinator records `TRANSPORT_DISCONNECT`, requeues the job, and another worker completes it. Validation compares normalized OCR text with the known fictional fixture label and records a result hash. The OCR adapter invokes an installed Tesseract executable on a temporary PNG and removes the temporary file afterward. No OCR text is placed in the summary report or event list.

## Reproduce

Requires Python 3.11+ and Tesseract on `PATH` or supplied through `--tesseract`:

```bash
python -m workcell.v2 demo --output out-v2
```

The output directory must be absent or empty. Read `out-v2/report.json` for the result and `out-v2/queue.sqlite3` for durable state. `WORKCELL_V2_INTEGRATION=1 python -m unittest discover -s tests -v` runs the loopback, authentication, recovery, and OCR integration tests. Without that environment variable, the suite runs storage and v0.1 tests and clearly marks the socket-dependent tests skipped.

The retained [sample report](v2-sample-report.json) was generated locally on 2026-10-26 using Python 3.14.5 and Tesseract `v5.5.0.20241111`. It records three delivered jobs, one synthetic connection interruption recovered, and two simultaneous OCR leases. Its elapsed time is one observed run, not a benchmark or service-level claim. The tests assert the exact recognized text for all three fixed images inside the temporary SQLite queue, confirm that all three worker processes register and stop, reject a worker with an invalid ephemeral key, recover a claimed job after coordinator restart, and reject modified or nonfixture images before retention. Recognized text is deliberately absent from the public sample report.

## Boundary

All workers share one host. There is no remote node, TLS, distributed consensus, production credential store, arbitrary upload, or private document. The transport interruption is a deliberate loopback connection drop; it does not prove recovery from a real network partition. Tesseract is an optional local dependency and is not bundled. The fixed synthetic images demonstrate that a real OCR executable can be connected to the queue, not general OCR accuracy.
