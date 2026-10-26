"""Accessible static status view generated from synthetic job metadata."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

CSS = (Path(__file__).with_name("status.css")).read_text(encoding="utf-8")
V2_SAMPLE = json.loads(
    (Path(__file__).resolve().parent.parent / "docs" / "v2-sample-report.json").read_text(encoding="utf-8")
)


def render_status(manifests: list[dict]) -> str:
    delivered = sum(item["state"] == "DELIVERED" for item in manifests)
    retries = sum(item["attempts"] > 1 for item in manifests)
    waiting = sum(
        any(event.get("code") == "CAPABILITY_UNAVAILABLE" for event in item["events"])
        for item in manifests
    )
    unresolved = len(manifests) - delivered
    jobs = []
    for item in manifests:
        identifier = escape(item["job_id"])
        state = escape(item["state"])
        events = []
        for event in item["events"]:
            worker = escape(event.get("worker", "coordinator-node"))
            code = f" · {escape(event['code'])}" if event.get("code") else ""
            events.append(
                f"<li><strong>{event['seq']:02} {escape(event['state'])}</strong>"
                f"<small>{worker}{code}</small></li>"
            )
        recovered = item["state"] == "DELIVERED" and any(
            event.get("code") == "CAPABILITY_UNAVAILABLE" for event in item["events"]
        )
        recovery_note = (
            '<p class="recovery">Worker unavailable, then recovered after one bounded retry.</p>'
            if recovered and item["attempts"] > 1 else ""
        )
        jobs.append(f"""<article class="job" aria-labelledby="job-{identifier}">
          <div class="job-head"><div><h3 id="job-{identifier}">Synthetic document</h3>
          <span class="job-id">Job {identifier}</span></div>
          <span class="state" data-state="{state}">{state.replace("_", " ")}</span></div>
          <div class="job-facts"><span>OCR attempts: <strong>{item['attempts']} of {item['max_attempts']}</strong></span>
          <span>Input hash: <strong>{escape(item['input_sha256'][:12])}…</strong></span>
          <span>Delivery hash: <strong>{escape((item.get('delivery_sha256') or 'pending')[:12])}{'…' if item.get('delivery_sha256') else ''}</strong></span></div>
          {recovery_note}<details><summary>View state trail</summary>
          <ol class="timeline">{''.join(events)}</ol></details></article>""")
    result_line = f"{delivered} of {len(manifests)} synthetic jobs delivered"
    recovery_line = (
        f"{waiting} waited for a worker; {retries} used a bounded retry; "
        f"{unresolved} remain unresolved."
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="A synthetic local AI workflow with capability routing, evidence handoffs, and bounded recovery.">
<title>Local AI Workcell | Synthetic workflow proof</title>
<style>{CSS}</style></head><body>
<a class="skip" href="#main">Skip to workflow</a>
<header class="mast"><div class="shell"><a class="brand" href="#main">LOCAL AI <span>WORKCELL</span></a>
<nav aria-label="Page"><a href="#v2-proof">v0.2 process proof</a><a href="#jobs">Inspect job trail</a><a href="#ownership">Design and evidence</a></nav></div></header>
<main id="main"><section class="hero shell" aria-labelledby="page-title">
<div class="hero-top"><div><p class="scope-label">Local orchestration / public synthetic proof</p>
<h1 id="page-title">Route local AI jobs by capability and verify every handoff.</h1>
<p class="lede">Leonel designs and operates adaptable AI workflows where coordinator control can move between machines. This public walkthrough assigns fictional documents to mock OCR, validation, and results roles, with recorded waits and bounded retries.</p></div>
<aside class="run-result" aria-label="Verified v0.1 synthetic result"><small class="proof-version">Live walkthrough · v0.1</small><strong>{result_line}</strong>
<p>{recovery_line}</p><a class="action" href="#jobs">Inspect recovery trail</a></aside></div>
<div class="hero-micro-route" role="img" aria-label="Synthetic request routes through coordinator and mock OCR to validation and delivery; {waiting} job waited for worker availability and {retries} retried before delivery."><div><span>Request</span><b>→</b><span>Route</span><b>→</b><span>Validate</span><b>→</b><span>Deliver</span></div><p>Unavailable ({waiting}) or retry ({retries}) returns to routing ↺</p></div>
<div class="v2-teaser"><div><strong>Separate v0.2 process proof</strong><p>{V2_SAMPLE['delivered']} of {V2_SAMPLE['submitted']} fictional PNGs delivered through two OCR processes, one validation process, and a durable queue. One deliberate loopback interruption recovered.</p></div><a href="#v2-proof">See the process and evidence <span aria-hidden="true">↘</span></a></div>
<figure class="route" aria-labelledby="route-title" aria-describedby="route-description">
<figcaption id="route-title">How one synthetic job reaches a validated result</figcaption>
<ol class="route-steps">
<li><b>Request</b><span>Fictional SVG input</span></li>
<li><b>Coordinator</b><span>Job ID and input hash</span></li>
<li><b>Capability route</b><span>Select available role</span></li>
<li><b>Mock OCR</b><span>SVG text nodes only</span></li>
<li><b>Validate</b><span>Separate facts and review</span></li>
<li class="result-node"><b>Deliver</b><span>Output checksum, once</span></li>
</ol>
<div class="route-branches"><p><strong>Unavailable:</strong> WAITING_WORKER keeps the job; it resumes when the OCR capability returns.</p>
<p><strong>Transient failure:</strong> RETRY_PENDING returns to routing and consumes one of two allowed OCR attempts.</p></div>
<p class="route-evidence" id="route-description">Evidence handoff: input hash → manifest and redacted state events → result hash → delivery hash. This run used {waiting} wait and {retries} retry event; all totals come from the generated manifests.</p>
</figure>
<p class="boundary">One computer and one Python process simulate the roles shown above. Mock OCR reads SVG text nodes; this view does not establish real OCR accuracy or multi-computer reliability.</p>
</section>
<section class="v2-section" id="v2-proof" aria-labelledby="v2-title"><div class="shell">
<div class="v2-heading"><div><p class="scope-label">v0.2 / local process experiment</p><h2 id="v2-title">The queue survives the interruption.</h2><p>The coordinator accepts only committed fictional PNGs. Two OCR worker processes call Tesseract; a separate validation worker checks the known synthetic labels. All workers register over authenticated loopback connections on one computer.</p></div><div class="v2-observation"><strong>{V2_SAMPLE['delivered']}/{V2_SAMPLE['submitted']} delivered</strong><span>{V2_SAMPLE['transport_interruptions']} interrupted connection · {V2_SAMPLE['recovered_jobs']} recovered job · {V2_SAMPLE['max_simultaneous_ocr_leases']} concurrent OCR leases</span></div></div>
<div class="v2-flow" role="img" aria-label="Synthetic PNG enters a durable SQLite queue, two OCR processes compete for work, a validation process checks the result, and one delivery is recorded. A dropped worker connection returns the job to the queue.">
<div><b>01</b><strong>Submit</strong><span>Fixed synthetic PNG</span></div><div><b>02</b><strong>Durable queue</strong><span>SQLite claim + restart recovery</span></div><div class="v2-worker"><b>03</b><strong>OCR workers ×2</strong><span>Separate processes · Tesseract</span></div><div><b>04</b><strong>Validate</strong><span>Separate worker process</span></div><div class="v2-result"><b>05</b><strong>Deliver once</strong><span>Result hash + terminal state</span></div></div>
<p class="v2-return"><strong>Recovery loop:</strong> a deliberate connection drop returns one claimed job to the queue; another worker finishes it within the two-attempt limit. A coordinator restart also requeues in-flight work.</p>
<div class="v2-links"><a href="docs/V2_PROOF.md">Method and limits</a><a href="docs/v2-sample-report.json">Inspect the synthetic report</a></div>
<p class="boundary">This observed run used Python 3.14 and {escape(V2_SAMPLE['ocr_engine'])}. Its {V2_SAMPLE['elapsed_ms']} ms elapsed time is one local observation, not a benchmark. No remote machine or private input was used.</p>
</div></section>
<section class="section shell" id="jobs" aria-labelledby="jobs-title"><h2 id="jobs-title">Inspect the state trail</h2>
<p class="section-intro">Each card shows the terminal state, attempts, and checksum excerpts. Open a trail to see exactly where the synthetic job waited, retried, and delivered.</p>
<div class="jobs">{''.join(jobs)}</div></section>
<section class="ownership" id="ownership"><div class="section shell"><h2>Design ownership and proof boundary</h2>
<div class="ownership-grid"><div><h3>Leonel's operating design</h3><p>Leonel reports designing and operating adaptable AI workflows across machines. He decides where coordination sits, routes by capability, and preserves handoffs and recovery. He set this public demo's scope and acceptance checks; coding agents assisted with implementation.</p></div>
<div><h3>What this repository verifies</h3><p>Its synthetic tests cover deterministic IDs, legal state changes, waiting, bounded retry, duplicate protection, checksums, and delivery. Reproduce the local run and inspect the source before treating any broader private practice as independently verified.</p></div></div></div></section>
<section class="section shell" aria-labelledby="next-title"><h2 id="next-title">What to examine next</h2><ul class="proof-list">
<li>Reproduce this one-process baseline with the commands in the repository README.</li>
<li>Reproduce the separate v0.2 local process experiment for authenticated workers, durable queue recovery, and Tesseract OCR on public synthetic images. Its evidence remains separate from this baseline.</li>
<li><a href="https://github.com/T-Crypt/berth">Berth</a> is a source-reviewed GPU contention research candidate, not installed or validated here. Any use requires a disposable controlled pilot.</li>
</ul></section></main>
<footer><div class="shell">Local AI Workcell · fictional inputs only · no private operating records</div></footer>
</body></html>
"""
