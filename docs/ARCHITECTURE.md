# Architecture and state map

The public demonstration runs every role, including the coordinator, in one Python process on one computer. Node names describe capabilities, not machines or network endpoints. Remote workers are planned, not built.

```mermaid
flowchart LR
    A[Synthetic SVG] --> B[Coordinator role<br/>job ID + input checksum]
    B --> C[ocr-node<br/>SVG text-node mock]
    C --> D[validation-node<br/>source + derived + review]
    D --> E[results-node<br/>idempotent delivery]
    B --> F[Manifest and redacted events]
    C --> F
    D --> F
    E --> F
    F --> G[Static status view]
```

## State path

`NEW → ROUTED → OCR_DONE → VALIDATED → DELIVERED` is the normal path. If the needed worker is unavailable, the job enters `WAITING_WORKER` without using an OCR attempt; making that capability available lets it resume at the saved phase. A simulated OCR failure enters `RETRY_PENDING` after the first attempt. The second attempt either succeeds or ends at `FAILED`. Delivered and failed jobs are terminal.

The manifest records a deterministic ID, pipeline version, phase, state, attempts, input/OCR/result/delivery hashes, mock-OCR label, and ordered events. The separate `events.jsonl` contains only job ID-free state metadata and generic worker labels; the job ID appears in its parent folder and manifest. The status page shows state, attempts, truncated checksums, and event codes. It does not display input text.

The results JSON keeps `source` hashes, `derived` counts, and `manual_review` status in separate fields. The manual-review flag remains required because reading SVG text nodes provides no evidence of real OCR accuracy.

## Limitations

Owner-reported and not verified here: Leonel describes a private workflow that spans more than one computer, with remote tasks, capability-specific OCR, result transfer, Git coordination, and Docker-dependent work. This repository does not show, run, or test it, and this diagram does not depict it. The public simulation does not schedule distributed tasks, authenticate workers, encrypt traffic, process scans or PDFs, or claim fault tolerance across real machines. Docker is unnecessary for this bounded single-computer proof. Future experiments could test synthetic distribution and Docker routing, authenticated transport, public-corpus OCR, and distributed recovery.
