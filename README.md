# Local AI Workcell

**[View the live walkthrough](https://leonelivancortesrodriguez.github.io/local-ai-workcell/)** · **[Inspect the v0.2 process proof](docs/V2_PROOF.md)**

[![Verify synthetic Workcell](https://github.com/LeonelIvanCortesRodriguez/local-ai-workcell/actions/workflows/verify.yml/badge.svg)](https://github.com/LeonelIvanCortesRodriguez/local-ai-workcell/actions/workflows/verify.yml)

Leonel designs and operates adaptable AI workflows across machines. This public repository makes the control pattern inspectable: route work by capability, retain evidence at each handoff, recover an interrupted job, and deliver a validated result. The live page shows a one-process mock-OCR baseline. A separate v0.2 experiment uses three local worker processes, authenticated loopback registration, a persistent SQLite queue, and real Tesseract OCR on fictional PNGs. Neither is a reproduction of the private system.

The `0.2.0` source contains both the v0.1 walkthrough and v0.2 experiment. The earlier public baseline was not tagged as a `v0.1.0` release. The [release procedure](docs/RELEASE.md) specifies the tag, ZIP, inventory, CI gate, and rollback. A GitHub release is created only after the workflow passes on this source commit.

![Synthetic workcell status at desktop width](docs/images/workcell-desktop.png)

## The operating problem

When machines have different capabilities, the operator needs to know where a job went, whether it finished, what changed, and how to recover it. A result without a reliable handoff is hard to trust. The coordinator is a movable control role, not a fixed physical machine. This demonstration turns the control pattern into a small, inspectable workflow.

### What Leonel designed and validated

- **Operating decisions:** where coordination sits, how work is assigned by capability, and which handoff and recovery evidence an operator needs. The coordinator role can move between machines in Leonel's owner-reported private practice.
- **Public proof scope:** the fictional fixtures, privacy boundary, failure cases, and acceptance checks for both demonstrations.
- **Implementation assistance:** coding agents helped implement the public source, interface, and automated checks. The source and reproducible tests are available for independent inspection.
- **What the retained checks establish:** v0.1 state and checksum behavior; v0.2 durable queue recovery, authenticated local registration, concurrent OCR leases, a simulated loopback interruption, and OCR of fixed public images. These checks do not verify the private topology or its operational outcomes.

## Evidence map

| Category | What is stated or shown | Evidence boundary |
| --- | --- | --- |
| Owner-reported operating practice | A living multi-machine workflow supports remote tasks, capability-specific OCR, result transfer, Git coordination, and Docker-dependent work. Coordinator control can move between machines. | This is the owner's account of private practice. The public repository does not independently verify its topology, reliability, or outcomes. |
| Public v0.1 baseline | One Python process routes two fictional SVG jobs through mock OCR, validation, and results roles. Tests exercise identity, waiting, retry, duplicate protection, checksums, and delivery. | Run the commands below and inspect the synthetic manifests, results, and status view. The live Pages site shows this baseline. |
| Public v0.2 process proof | Two OCR processes and one validation process register with an authenticated local coordinator. A SQLite queue survives restart, one loopback connection deliberately drops, and Tesseract reads three fictional PNGs. | Run the v0.2 command and inspect the [retained sample report](docs/v2-sample-report.json) and [method](docs/V2_PROOF.md). This is local-only, not a distributed deployment. |
| Future research | Remote worker transport, real network partition behavior, broader OCR corpora, and GPU contention control. | Proposed only. Berth is a source-reviewed research candidate, not installed or validated here. |

## Inspect it in five minutes

The v0.1 walkthrough requires Python 3.11 or newer and no runtime dependencies or paid services.

```bash
python -m workcell.cli demo --output out
python -m workcell.cli verify --output out
```

Open `out/index.html` in a browser. The committed [static example](index.html) shows the same synthetic run. The first job delivers directly. The second waits for an unavailable OCR worker, then recovers after one simulated transient failure. Both have deterministic IDs, bounded attempts, checksums, and redacted state trails.

The output directory must be absent or empty. Delete your own `out/` directory before rerunning the demo. To refresh the committed static view from the fixtures, run `python scripts/refresh_demo.py`.

### Reproduce the v0.2 process proof

Install Tesseract from its official package for your platform, then run:

```bash
python -m workcell.v2 demo --output out-v2
```

The command prints delivered, interruption, recovery, concurrent-lease, and elapsed observations. `out-v2/report.json` records the bounded synthetic run; the SQLite queue remains in `out-v2/queue.sqlite3` so its terminal state can be inspected. See [v0.2 proof and limits](docs/V2_PROOF.md). Tesseract and Pillow are not bundled; Pillow is used only by an optional fixture-regeneration script on Windows.

## What the workflow does

1. A movable coordinator role accepts only synthetic SVG fixtures beginning with `SYNTHETIC DEMO`. In this demo it runs in the same Python process as every worker. The job ID derives from the document bytes and pipeline version.
2. Capability routing selects generic `ocr-node`, `validation-node`, and `results-node` labels. No hostname or remote connection is involved.
3. The OCR stage reads SVG text nodes as a **mock**. It does not recognize pixels, PDFs, or handwriting.
4. Validation produces a result that separates source checksums, derived counts, and a required manual-review flag.
5. The results stage delivers once, checks for conflicts, and records an output checksum. Duplicate submission returns the existing job without another delivery.

See the [architecture and state map](docs/ARCHITECTURE.md) for the recovery path and manifest schema.

## Verify the controls

```bash
python -m unittest discover -s tests -v
python tests/mutation_check.py
python scripts/privacy_scan.py
python scripts/package.py --output release
```

For the socket and OCR integration tests, set `WORKCELL_V2_INTEGRATION=1` before running `unittest`. The [GitHub Actions workflow](.github/workflows/verify.yml) is configured for Python 3.11–3.14 to run the mutation and privacy checks, regenerate the static page, verify both demos, and compare two release packages. Its badge reports GitHub's actual CI state; a local pass is not a CI pass. The mutation test changes a delivered v0.1 result and requires checksum verification to reject it. The package command creates a deterministic allowlisted ZIP and SHA-256 inventory. The privacy scan is a bounded detector; independent review of the public package remains necessary.

## Evidence and privacy boundary

The repository proves orchestration behavior in local simulations: deterministic identity, capability routing, legal state changes, bounded retry, waiting and recovery, duplicate protection, checksum validation, and a status view. v0.2 additionally proves local process coordination and the adapter connection to Tesseract on three fixed images. It does **not** prove general OCR accuracy, multi-computer reliability, production security, or quantified operational outcomes. The v0.1 retained event log contains state, phase, generic worker label, and reason code. It contains no job ID, document text, or local path; the job ID is in the manifest and its parent directory. The v0.2 sample report contains synthetic job IDs, hashes, generic worker labels, and measured local timings, but no recognized text or local path.

The two SVG documents and three PNG images are fictional and were created for this release. No private document, real-node identity, credential, operational log, or personal screenshot is included. Read [SECURITY.md](SECURITY.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

Owner-authored source, documentation, fixtures, and status-view images are released under the [MIT License](LICENSE). See [third-party notices](THIRD_PARTY_NOTICES.md) for development tools used to capture screenshots.
