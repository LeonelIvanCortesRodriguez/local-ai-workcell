"""Accessible static status view generated from synthetic job metadata."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from urllib.parse import quote

from .diagram import DIAGRAM_CSS, mark_svg, narrow_svg, state_glyph, wide_svg

CSS = (Path(__file__).with_name("status.css")).read_text(encoding="utf-8") + DIAGRAM_CSS
V2_SAMPLE = json.loads(
    (Path(__file__).resolve().parent.parent / "docs" / "v2-sample-report.json").read_text(encoding="utf-8")
)
REPO = "https://github.com/LeonelIvanCortesRodriguez/local-ai-workcell"
FAVICON = "data:image/svg+xml," + quote(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><rect width="48" height="48" fill="#24272c"/>'
    '<path d="M9 9H39V18M39 30V39H9V30M9 18V9" fill="none" stroke="#f7f7f8" stroke-width="4"/>'
    '<path d="M3 24H18Q24 24 24 18M24 18Q24 24 30 24H45" fill="none" stroke="#f7f7f8" stroke-width="3.5"/>'
    '<rect x="9" y="35" width="30" height="4" fill="#f2c94c"/></svg>'
)
EVENT_NOTES = {
    "SUBMITTED": "Admitted; job ID derived from the input bytes",
    "CAPABILITY_UNAVAILABLE": "No OCR worker available; the job keeps its place without using an attempt",
    "SIMULATED_TRANSIENT_FAILURE": "Simulated transient failure; one of two OCR attempts used",
}


def _event(event: dict) -> str:
    worker = escape(event.get("worker", "coordinator"))
    code = event.get("code")
    note = EVENT_NOTES.get(code, f"Handled by {worker}") if code else f"Handled by {worker}"
    return (f"<li>{state_glyph(event['state'])}<b>{event['seq']:02} {escape(event['state'])}</b>"
            f"<small>{escape(note)}</small></li>")


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
        recovered = item["state"] == "DELIVERED" and item["attempts"] > 1 and any(
            event.get("code") == "CAPABILITY_UNAVAILABLE" for event in item["events"]
        )
        title = "Job that waited, retried, and delivered" if recovered else "Job delivered on the first route"
        recovery_note = (
            '<p class="recovery">The OCR worker was missing, the job waited, failed once, and was delivered on its second attempt.</p>'
            if recovered else ""
        )
        jobs.append(f"""<article class="job{' job-recovered' if recovered else ''}" aria-labelledby="job-{identifier}">
          <div class="job-head"><div><h3 id="job-{identifier}">{title}</h3>
          <span class="job-id">Job {identifier}</span></div>
          <span class="state" data-state="{state}">{state_glyph(item['state'])}{state.replace("_", " ")}</span></div>
          <div class="job-facts"><span>OCR attempts <strong>{item['attempts']} of {item['max_attempts']}</strong></span>
          <span>Input <strong>{escape(item['input_sha256'][:12])}…</strong></span>
          <span>Delivery <strong>{escape((item.get('delivery_sha256') or 'pending')[:12])}{'…' if item.get('delivery_sha256') else ''}</strong></span></div>
          {recovery_note}<details{' open' if recovered else ''}><summary>State trail ({len(item['events'])} recorded events)</summary>
          <ol class="timeline">{''.join(_event(event) for event in item['events'])}</ol></details></article>""")
    detail = (f"{waiting} waited for a worker · {retries} retried once · {unresolved} unresolved")
    v2 = V2_SAMPLE
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="A small local system that sends each document job to a worker that can do it, records every handoff, and recovers when a worker drops out. Fictional inputs, one computer.">
<title>Local AI Workcell</title>
<link rel="icon" href="{FAVICON}">
<style>{CSS}</style></head><body>
<a class="skip" href="#main">Skip to the workflow</a>
<header class="mast"><div class="shell"><a class="brand" href="#main">{mark_svg(36)}<span class="wordmark">Local AI Workcell</span></a>
<nav aria-label="Page"><a href="#how">How it works</a><a href="#jobs">Recovery trail</a><a href="#v2-proof">v0.2 process proof</a><a href="#role">Leonel's role</a></nav></div></header>
<main id="main"><section class="hero shell" aria-labelledby="page-title">
<h1 id="page-title">Send each document job to a worker that can do it, and keep proof of every handoff.</h1>
<p class="lede">A coordinator routes fictional documents to OCR, validation, and results workers by capability, records a hash at each handoff, and recovers when a worker is missing or fails once. Leonel designed the operating pattern and its checks. It runs on one computer.</p>
<div class="result"><p class="result-line">{state_glyph('DELIVERED')}<span>{delivered} of {len(manifests)} synthetic jobs delivered <span class="result-detail">· {detail}</span></span></p>
<div class="actions"><a class="action action-primary" href="#jobs">Inspect the recovery trail</a><a class="action" href="{REPO}#run-it-locally">Run it locally</a></div></div>
<figure class="cell" id="how" aria-describedby="cell-caption">
{wide_svg()}{narrow_svg()}
<figcaption id="cell-caption">The yellow line is the proof boundary: one computer, fictional inputs. The dashed loop is the recovery path; the blue rail is the evidence each station records.</figcaption>
<details><summary>Read the diagram as a list</summary><ol>
<li>A fictional SVG (v0.1) or PNG (v0.2) enters the cell. Nothing else is admitted.</li>
<li>The coordinator derives the job ID from the input bytes and records the input hash.</li>
<li>It routes by capability to <code>ocr-node</code> (mock OCR in v0.1, Tesseract in v0.2), then <code>validation-node</code>, which keeps source, derived, and manual-review fields apart, then <code>results-node</code>, which delivers once.</li>
<li>Each station records a hash in the manifest; state events are redacted.</li>
<li>Recovery: without an OCR worker the job waits in WAITING_WORKER and keeps its place. After one transient failure it enters RETRY_PENDING and is routed again, with at most two OCR attempts.</li>
</ol></details>
</figure>
</section>
<section class="section band" id="jobs" aria-labelledby="jobs-title"><div class="shell">
<h2 id="jobs-title">The recovery trail, event by event</h2>
<p class="section-intro">Both jobs come from the committed fixtures. The first waited for a missing worker and used its second OCR attempt; the second went straight through. Every line below is read from its manifest.</p>
<div class="jobs">{''.join(jobs)}</div></div></section>
<section class="section shell" id="v2-proof" aria-labelledby="v2-title">
<h2 id="v2-title">v0.2: separate processes, a durable queue, real OCR</h2>
<p class="section-intro">A separate experiment on the same computer. Workers are separate processes that register over authenticated loopback connections; Tesseract reads three fictional PNGs.</p>
<div class="v2-grid"><ol class="v2-route">
<li><strong>Submit</strong><span>Only the three committed fictional PNGs are admitted</span></li>
<li><strong>Durable queue</strong><span>SQLite claim; a coordinator restart requeues in-flight work</span></li>
<li><strong>OCR workers ×2</strong><span>Separate processes calling Tesseract</span></li>
<li><strong>Dropped connection</strong><span>One worker deliberately drops its loopback connection; the job is requeued and another worker finishes it</span></li>
<li><strong>Validate and deliver</strong><span>A separate validation process checks the known label and records a result hash</span></li>
</ol>
<div class="v2-observed" aria-label="Observed v0.2 sample run"><p class="big">{v2['delivered']} of {v2['submitted']} delivered</p>
<p>{v2['transport_interruptions']} interrupted connection, {v2['recovered_jobs']} recovered job, {v2['max_simultaneous_ocr_leases']} OCR leases at once.</p>
<ul><li>{escape(v2['ocr_engine'])}</li><li>{v2['elapsed_ms']} ms for one local run, not a benchmark</li></ul></div></div>
<div class="links"><a href="docs/V2_PROOF.md">Read the v0.2 method and limits</a><a href="docs/v2-sample-report.json">Inspect the sample report</a></div>
</section>
<section class="section band" id="role" aria-labelledby="role-title"><div class="shell role">
<div><h2 id="role-title">Leonel's role</h2>
<p>Leonel designs and runs adaptable AI workflows across machines in Leonel's own practice, which this repository does not verify. Here he made the operating decisions, set the public proof scope and fictional fixtures, chose the failure cases, and wrote the acceptance checks. Coding agents helped implement the source, page, and tests.</p></div>
<ul class="decisions">
<li><strong>Route by capability, not by machine.</strong> Workers are <code>ocr-node</code> or <code>validation-node</code>, so the coordinator role can move.</li>
<li><strong>Waiting costs no attempt.</strong> A missing worker is not a failure; the job keeps its place.</li>
<li><strong>Bounded retry.</strong> Two OCR attempts, then FAILED, so nothing loops forever.</li>
<li><strong>Hash at every handoff.</strong> A changed delivered result is detected; the mutation check proves it.</li>
<li><strong>Manual review stays required.</strong> Mock OCR proves nothing about accuracy, so the result says so.</li>
</ul></div></section>
<section class="section shell" aria-labelledby="limits-title"><h2 id="limits-title">What this does not prove</h2>
<p class="boundary">One computer. Fictional inputs. No remote node, TLS, production credential store, arbitrary upload, or private document. It does not establish general OCR accuracy, multi-computer reliability, production security, or operational outcomes.</p>
<ul class="proof-list">
<li>Reproduce both runs with the commands in the <a href="{REPO}#run-it-locally">README</a>.</li>
<li><a href="https://github.com/T-Crypt/berth">Berth</a> is a source-reviewed GPU contention research candidate, not installed or validated here.</li>
</ul></section></main>
<footer><div class="shell">Local AI Workcell · fictional inputs only · MIT licensed · Archivo and Martian Mono under the SIL Open Font License</div></footer>
</body></html>
"""
