# Product

## Register

product

## Surface registers

The default register above governs the generated status page (`index.html`, `workcell/view.py`, `workcell/status.css`). Work on that surface loads Impeccable's product reference (`reference/product.md`).

The README hero, GitHub social preview, demonstration recordings, and any portfolio landing page are brand surfaces. Work on those loads the brand reference (`reference/brand.md`), and brand permissions (committed or drenched color, display type, art direction) apply only there. Brand surfaces still keep every claim and evidence boundary in this file.

## Product promise

A small local system that sends each document job to a worker that can do it, records every handoff, and recovers when a worker drops out.

## Users

Engineering and AI-operations leaders deciding whether Leonel can design and run controlled AI workflows. They arrive from a CV link or a GitHub profile, give the page a few seconds, and need to see a working system and its limits before they read any code. A second reader is the engineer who opens the repository to check whether the claims hold.

## The problem in one paragraph

When AI work is split between workers with different abilities (one runs OCR, another validates, another delivers), jobs get lost between them. The operator cannot easily say where a job is, whether it finished, what changed it, or how to resume it. A result without a reliable handoff record is hard to trust.

## What moves through the cell

| Stage | What happens | Where it is proven |
| --- | --- | --- |
| Controlled input | Only fictional fixtures are admitted (SVG in v0.1, three PNGs in v0.2). The job ID derives from the input bytes. | `workcell/core.py`, `workcell/v2.py`, tests |
| Coordinator | Assigns work by capability label, not by machine name. | `tests/test_workcell.py` |
| Specialized worker | v0.1: mock OCR that reads SVG text nodes. v0.2: Tesseract in separate worker processes. | `tests/test_v2.py`, `docs/v2-sample-report.json` |
| Validation | Keeps source hashes, derived counts, and the manual-review flag in separate fields. | results JSON, tests |
| Checked output | Delivered once, with an output checksum. A duplicate submission returns the existing job. | mutation check, tests |
| Recovery | Waiting for a missing worker, bounded retry, coordinator restart, and a deliberate loopback disconnect. | v0.1 and v0.2 tests, sample report |

## Evidence status

- **Implemented and tested:** everything in the table above, on one computer.
- **Observed once:** the v0.2 sample report (2026-10-26, Python 3.14.5, Tesseract 5.5.0). It records three delivered jobs, one recovered interruption, and two simultaneous OCR leases. Its timing is one run, not a benchmark.
- **Owner-reported, not verified here:** Leonel reports using a similar pattern in private work that spans more than one computer. Nothing in this repository shows, runs, or tests that, and no public surface may present it as a demonstrated capability.
- **Planned:** remote worker transport, real network partition tests, broader OCR corpora, GPU contention control.
- **Unsupported, never claim:** general OCR accuracy, multi-computer reliability, production security, quantified operational outcomes.

## Leonel's contribution

Leonel made the operating decisions: what the coordinator is responsible for, how work is assigned by capability, and which handoff and recovery evidence an operator needs. He set the public proof scope, the fictional fixtures, the failure cases, and the acceptance checks. Coding agents helped implement the source, interface, and tests. The presentation must say this plainly, once, without inflating or hiding either part.

## Five-second test

After five seconds on the README or the live page, a reader should be able to say: "It routes document jobs to local workers, records each handoff, and recovers from failures. It is a local synthetic proof, and I can run it."

## Brand personality

Machined, labeled, accountable. The feel of a well-marked workshop cell: every station has a plate, every route is drawn, and the safety boundary is painted on the floor. Confident about what is proven, precise about where proof stops.

## Anti-references

- Generic "AI agent platform" visuals: glowing nodes, neural meshes, robot or brain imagery, purple gradients.
- Terminal-cosplay heroes with green-on-black text that the system never prints.
- Live-ops dashboards with counters that imply a fleet of machines.
- A dashboard screenshot inside a decorative browser frame as the hero.
- Copying the Obsidian Second Brain, Dittofeed, Plasmic, or SpeakoFlow artwork, palettes, or layouts. Their lesson (identity, one promise, a visual explanation, then proof) is the only thing borrowed.

## Design principles

1. **Draw the cell, not the AI.** The first visual is the route a job takes and the boundary it stays inside.
2. **Show the failure path beside the normal path.** Recovery is the point; it is never a footnote.
3. **Every number comes from a manifest or report.** No figure is typed into copy by hand.
4. **Mark the boundary where the proof stops.** "One computer, fictional inputs" sits next to the claim it limits.
5. **End every screen with something to inspect.** A trail, a report, or a command.

## Accessibility & inclusion

WCAG 2.2 AA for text and controls in both themes. Body text at least 16px. State is carried by shape, label, and line pattern as well as color. Diagrams have an accessible name and an adjacent text equivalent. Visible focus, 44px primary targets, full keyboard operation, `prefers-reduced-motion` honored, and no horizontal overflow from 390px to 1440px.
