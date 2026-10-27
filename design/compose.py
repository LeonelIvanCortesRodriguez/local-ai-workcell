"""Write the HTML compositions that design/render.mjs turns into README and social images.

Every number and state comes from a fresh synthetic run or the retained v0.2 report.
Output goes to design/build/ (ignored by Git).
"""

from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workcell.cli import demo  # noqa: E402
from workcell.diagram import DIAGRAM_CSS, mark_svg, state_glyph, wide_svg  # noqa: E402
from workcell.view import CSS as PAGE_CSS, EVENT_NOTES, V2_SAMPLE  # noqa: E402

BUILD = ROOT / "design" / "build"
PROMISE = "Send each document job to a worker that can do it, and keep proof of every handoff."
BASE_CSS = PAGE_CSS.replace('url("assets/fonts/', 'url("../../assets/fonts/') + """
body { margin: 0; }
.canvas { position: relative; overflow: hidden; background: var(--bg); }
.id { display: flex; align-items: center; gap: 14px; }
.id .mark { width: 44px; height: 44px; }
.id .wordmark { font-size: 26px; }
"""


def page(title: str, css: str, body: str) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{escape(title)}</title>'
            f'<style>{BASE_CSS}{css}</style></head><body>{body}</body></html>')


def hero() -> str:
    css = """
.canvas { width: 1280px; height: 690px; padding: 36px 40px 0; }
.top { display: flex; justify-content: space-between; align-items: center; }
.tag { font: 600 14px/1 var(--mono); color: var(--ink-2); }
h1 { max-width: none; margin: 26px 0 8px; font-size: 38px; line-height: 1.12; }
.sub { margin: 0 0 6px; color: var(--ink-2); font-size: 19px; }
.dg { width: 1200px; }
"""
    body = f"""<div class="canvas"><div class="top"><div class="id">{mark_svg(44)}<span class="wordmark">Local AI Workcell</span></div>
<span class="tag">Python · local synthetic proof</span></div>
<h1>{escape(PROMISE)}</h1>
<p class="sub">Capability routing, a hash at each handoff, and recovery when a worker is missing or fails once.</p>
{wide_svg("hero")}</div>"""
    return page("Local AI Workcell hero", css, body)


def social() -> str:
    css = """
.canvas { width: 1280px; height: 640px; padding: 0; }
.frame { position: absolute; inset: 28px; border: 16px solid transparent; border-image: repeating-linear-gradient(45deg, var(--boundary) 0 12px, var(--boundary-ink) 12px 18px) 16; }
.port { position: absolute; width: 18px; height: 92px; top: 274px; background: var(--bg); }
.port.in { left: 27px; } .port.out { right: 27px; }
.inner { position: absolute; inset: 96px 104px 92px; display: flex; flex-direction: column; gap: 34px; }
.id .mark { width: 72px; height: 72px; }
.id .wordmark { font-size: 58px; }
.promise { max-width: 24ch; margin: 0; font-size: 44px; font-weight: 650; font-stretch: 106%; line-height: 1.14; }
.route { display: flex; align-items: center; gap: 10px; margin-top: auto; white-space: nowrap; font: 600 18px/1 var(--mono); color: var(--ink-2); }
.scope { margin: -18px 0 0; font: 600 16px/1 var(--mono); color: var(--ink-2); }
.route b { color: var(--ink); }
.route .glyph { width: 20px; height: 20px; }
"""
    body = f"""<div class="canvas"><div class="frame"></div><div class="port in"></div><div class="port out"></div>
<div class="inner"><div class="id">{mark_svg(72)}<span class="wordmark">Local AI Workcell</span></div>
<p class="promise">{escape(PROMISE)}</p>
<div class="route"><b>input</b> → coordinator → ocr → validation → results {state_glyph('DELIVERED')}<b>delivered</b></div><p class="scope">Python · one computer · fictional inputs · MIT</p></div></div>"""
    return page("Local AI Workcell social preview", css, body)


def replay(manifest: dict) -> str:
    station_for = {"NEW": 0, "WAITING_WORKER": 0, "ROUTED": 1, "RETRY_PENDING": 1, "OCR_DONE": 1, "VALIDATED": 2, "DELIVERED": 3}
    steps = []
    for event in manifest["events"]:
        code = event.get("code")
        note = EVENT_NOTES.get(code) or f"Handled by {event.get('worker', 'coordinator')}"
        part = {"WAITING_WORKER": "wait", "RETRY_PENDING": "retry", "DELIVERED": "output"}.get(event["state"], "")
        steps.append({"seq": event["seq"], "state": event["state"], "note": note,
                      "station": station_for[event["state"]], "part": part})
    css = """
.canvas { width: 1280px; height: 720px; padding: 30px 40px 0; }
.top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.job { font: 600 15px/1 var(--mono); color: var(--ink-2); }
.dg { width: 1200px; }
[data-station] rect, [data-part] { transition: none; }
.dg [data-station].on rect { fill: var(--ink); stroke: var(--ink); }
.dg [data-station].on text { fill: var(--bg); }
.dg [data-part].dim { opacity: .5; }
.dg [data-part="loop"].on { stroke-width: 3.5; }
.caption { position: absolute; left: 40px; right: 40px; bottom: 34px; display: grid; grid-template-columns: auto 1fr auto; gap: 18px; align-items: center; padding: 18px 22px; border: 2.5px solid var(--ink); background: var(--surface); }
.caption .glyph { width: 26px; height: 26px; }
.caption b { display: block; font: 600 18px/1.3 var(--mono); }
.caption span { font-size: 18px; color: var(--ink-2); }
.caption small { font: 600 15px/1 var(--mono); color: var(--ink-2); }
"""
    data = json.dumps(steps)
    glyphs = json.dumps({state: state_glyph(state) for state in ("WAITING_WORKER", "RETRY_PENDING", "DELIVERED", "ROUTED")})
    body = f"""<div class="canvas"><div class="top"><div class="id">{mark_svg(44)}<span class="wordmark">Local AI Workcell</span></div>
<span class="job">Replay of job {escape(manifest['job_id'][:12])} · read from its manifest</span></div>
{wide_svg("replay")}
<div class="caption" aria-live="polite"><span id="glyph"></span><div><b id="state"></b><span id="note"></span></div><small id="count"></small></div></div>
<script>
const steps = {data}; const glyphs = {glyphs};
window.showStep = (index) => {{
  const step = steps[index];
  document.querySelectorAll('[data-station]').forEach((el) => el.classList.toggle('on', Number(el.dataset.station) === step.station));
  document.querySelectorAll('[data-part]').forEach((el) => {{
    const name = el.dataset.part;
    const active = name === step.part || (name === 'loop' && (step.part === 'wait' || step.part === 'retry'));
    el.classList.toggle('on', active); el.classList.toggle('dim', !active);
  }});
  document.getElementById('glyph').innerHTML = glyphs[step.state] || glyphs.ROUTED;
  document.getElementById('state').textContent = String(step.seq).padStart(2, '0') + ' ' + step.state;
  document.getElementById('note').textContent = step.note;
  document.getElementById('count').textContent = 'event ' + step.seq + ' of ' + steps.length;
}};
window.stepCount = steps.length; showStep(0);
</script>"""
    return page("Local AI Workcell replay", css, body)


VIEWS = [
    ("view-mobile", "cap-mobile.png", "The same story on a phone", 390,
     ["The promise, the delivered count, and both actions fit the first screen at 390px.",
      "Below them the route turns vertical, so no label shrinks below 15px.",
      "The yellow line still marks the proof boundary: one computer, fictional inputs."]),
    ("view-trail", "cap-trail.png", "One job's recovery, event by event", 712,
     ["The job that recovered is open by default and carries the heavier border.",
      "Waiting is drawn with a dashed outline and a clock; retry with a circular arrow. Delivered is a filled square.",
      "Every line is read from the job's manifest; nothing is typed into the page by hand."]),
    ("view-v2", "cap-v2.png", "v0.2: real OCR in separate processes", 712,
     [f"{V2_SAMPLE['delivered']} of {V2_SAMPLE['submitted']} fictional PNGs delivered by Tesseract running in two worker processes.",
      "A deliberately dropped connection is requeued and finished by the other worker.",
      f"The {V2_SAMPLE['elapsed_ms']} ms figure is labelled as one local run, not a benchmark."]),
]


def view(capture: str, title: str, notes: list[str], width: int) -> str:
    css = f"""
.canvas {{ width: {width + 520}px; display: grid; grid-template-columns: {width}px 1fr; gap: 56px; padding: 48px; align-items: start; }}
.shot {{ display: block; width: {width}px; border: 1.5px solid var(--line); }}
.notes {{ position: sticky; top: 48px; padding-top: 8px; }}
h2 {{ max-width: none; margin: 28px 0 22px; font-size: 32px; }}
ol {{ margin: 0; padding: 0; list-style: none; counter-reset: n; }}
li {{ counter-increment: n; display: grid; grid-template-columns: 34px 1fr; gap: 12px; margin: 0 0 18px; font-size: 20px; line-height: 1.45; color: var(--ink-2); }}
li::before {{ content: counter(n); display: grid; place-items: center; width: 30px; height: 30px; background: var(--ink); color: var(--bg); font: 700 15px/1 var(--mono); }}
.foot {{ margin-top: 26px; font: 600 14px/1.5 var(--mono); color: var(--ink-2); }}
"""
    items = "".join(f"<li>{escape(note)}</li>" for note in notes)
    body = f"""<div class="canvas"><img class="shot" src="{capture}" alt="">
<div class="notes"><div class="id">{mark_svg(36)}<span class="wordmark">Local AI Workcell</span></div><h2>{escape(title)}</h2><ol>{items}</ol>
<p class="foot">Captured from the committed status page · fictional inputs</p></div></div>"""
    return page(title, css, body)


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    work = ROOT / "_tmp"
    work.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=work) as temporary:
        manifests = demo(Path(temporary) / "run")
    recovered = next(item for item in manifests if item["attempts"] > 1)
    (BUILD / "hero.html").write_text(hero(), encoding="utf-8")
    (BUILD / "social.html").write_text(social(), encoding="utf-8")
    (BUILD / "replay.html").write_text(replay(recovered), encoding="utf-8")
    for name, capture, title, width, notes in VIEWS:
        (BUILD / f"{name}.html").write_text(view(capture, title, notes, width), encoding="utf-8")
    print(f"COMPOSE_OK build={BUILD.relative_to(ROOT).as_posix()} replay_job={recovered['job_id'][:12]} events={len(recovered['events'])}")


if __name__ == "__main__":
    main()
