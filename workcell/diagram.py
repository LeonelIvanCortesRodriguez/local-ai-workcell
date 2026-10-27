"""Inline SVG for the workcell route, the brand mark, and the state glyphs.

Colors come from CSS custom properties (see DESIGN.md) so the same markup
serves the light and dark status page and the rendered README hero.
"""

from __future__ import annotations

from html import escape

DESCRIPTION = (
    "A fictional SVG or PNG document enters the local cell through its input port. "
    "The coordinator gives it a job ID derived from the input bytes and routes it by capability "
    "to ocr-node, then validation-node, which flags the result for manual review, then results-node, "
    "which delivers it once through the output port. Each station records a hash in the manifest. "
    "If no OCR worker is available the job waits in WAITING_WORKER and keeps its place; "
    "after one transient failure it enters RETRY_PENDING and is routed again, with at most two OCR attempts. "
    "Everything runs on one computer with fictional inputs."
)

STATIONS = (
    ("Coordinator", "job ID from input bytes", "input sha256"),
    ("ocr-node", "mock or Tesseract", "ocr sha256"),
    ("validation-node", "flags manual review", "result sha256"),
    ("results-node", "delivers once", "delivery sha256"),
)


def _defs(prefix: str) -> str:
    return f"""<defs>
<pattern id="{prefix}-hatch" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
<rect width="14" height="14" class="dg-boundary"/><rect width="5" height="14" class="dg-boundary-ink"/></pattern>
<marker id="{prefix}-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0 0L10 5L0 10z" class="dg-ink-fill"/></marker>
<marker id="{prefix}-arrow-ev" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
<path d="M0 0L10 5L0 10z" class="dg-ev-fill"/></marker>
</defs>"""


def _clock(x: float, y: float) -> str:
    return (f'<g class="dg-glyph" transform="translate({x} {y})"><circle cx="8" cy="8" r="7"/>'
            '<path d="M8 4v4l3 2"/></g>')


def _retry(x: float, y: float) -> str:
    return (f'<g class="dg-glyph" transform="translate({x} {y})"><path d="M14 8a6 6 0 1 1-2-4.5"/>'
            '<path d="M12.5 0.5v3.5h-3.5"/></g>')


def _check_square(x: float, y: float, size: float = 30) -> str:
    return (f'<g transform="translate({x} {y})"><rect width="{size}" height="{size}" class="dg-ink-fill"/>'
            f'<path d="M{size*.24} {size*.52}l{size*.18} {size*.18} {size*.36}-{size*.4}" class="dg-check"/></g>')


def _doc(x: float, y: float, w: float, h: float) -> str:
    fold = 16
    return (f'<path d="M{x} {y}h{w-fold}l{fold} {fold}v{h-fold}h-{w}z" class="dg-plate"/>'
            f'<path d="M{x+w-fold} {y}v{fold}h{fold}" class="dg-plate-line"/>')


def wide_svg(prefix: str = "cell-wide") -> str:
    """Horizontal route, sized for content widths of roughly 1000 to 1200px."""
    plate_y, plate_h, plate_w = 168, 92, 190
    xs = (175, 395, 615, 835)
    parts = [_defs(prefix)]
    # The painted floor boundary with ports cut into it.
    parts.append(f'<rect x="150" y="40" width="900" height="396" fill="none" stroke="url(#{prefix}-hatch)" stroke-width="14"/>')
    parts.append('<rect x="141" y="184" width="18" height="60" class="dg-bg"/>')
    parts.append('<rect x="1041" y="184" width="18" height="60" class="dg-bg"/>')
    parts.append('<rect x="175" y="26" width="436" height="30" class="dg-boundary"/>')
    parts.append('<text x="189" y="47" class="dg-tab">LOCAL CELL · one computer · fictional inputs</text>')
    # Input slip outside the cell.
    parts.append(_doc(8, 150, 120, 128))
    parts.append('<text x="22" y="186" class="dg-title-sm">Fictional</text><text x="22" y="208" class="dg-title-sm">input</text>')
    parts.append('<text x="22" y="236" class="dg-mono">SVG · v0.1</text><text x="22" y="257" class="dg-mono">PNG · v0.2</text>')
    parts.append(f'<path d="M128 214H{xs[0]-4}" class="dg-route" marker-end="url(#{prefix}-arrow)"/>')
    # Stations, the route between them, and the hash each one records.
    for index, (x, (title, sub, evidence)) in enumerate(zip(xs, STATIONS)):
        parts.append(f'<g data-station="{index}"><rect x="{x}" y="{plate_y}" width="{plate_w}" height="{plate_h}" class="dg-plate"/>')
        parts.append(f'<text x="{x+14}" y="{plate_y+34}" class="dg-title">{escape(title)}</text>')
        parts.append(f'<text x="{x+14}" y="{plate_y+62}" class="dg-sub">{escape(sub)}</text></g>')
        if index < len(xs) - 1:
            parts.append(f'<path d="M{x+plate_w} 214H{xs[index+1]-4}" class="dg-route" marker-end="url(#{prefix}-arrow)"/>')
        tick = x + 22
        parts.append(f'<path d="M{tick} {plate_y+plate_h}V356" class="dg-ev-line" marker-end="url(#{prefix}-arrow-ev)"/>')
        parts.append(f'<text x="{tick+10}" y="318" class="dg-ev-text">{escape(evidence)}</text>')
    parts.append('<path d="M175 362H1025" class="dg-ev-rail"/>')
    parts.append('<text x="175" y="398" class="dg-ev-label">Manifest and redacted state events: every handoff is recorded</text>')
    # Recovery loop above the route: ocr-node back to the coordinator.
    loop_from, loop_to = xs[1] + plate_w / 2, xs[0] + plate_w / 2
    parts.append(f'<path d="M{loop_from} {plate_y}V112H{loop_to}V{plate_y-6}" class="dg-recovery" data-part="loop" marker-end="url(#{prefix}-arrow)"/>')
    parts.append('<g data-part="wait">' + _clock(530, 83))
    parts.append('<text x="554" y="96" class="dg-state">WAITING_WORKER</text>')
    parts.append('<text x="690" y="96" class="dg-sub">waits for an OCR worker without using an attempt</text></g>')
    parts.append('<g data-part="retry">' + _retry(530, 113))
    parts.append('<text x="554" y="126" class="dg-state">RETRY_PENDING</text>')
    parts.append('<text x="690" y="126" class="dg-sub">after one transient failure; attempt 2 of 2</text></g>')
    # Checked output outside the cell.
    parts.append(f'<path d="M{xs[3]+plate_w} 214H1072" class="dg-route" marker-end="url(#{prefix}-arrow)"/>')
    parts.append('<g data-part="output">' + _check_square(1078, 168))
    parts.append('<text x="1078" y="232" class="dg-title-sm">Checked</text><text x="1078" y="254" class="dg-title-sm">output</text>')
    parts.append('<text x="1078" y="280" class="dg-sub">delivered once</text></g>')
    body = "".join(parts)
    return (f'<svg class="dg dg-wide" viewBox="0 0 1200 450" role="img" aria-labelledby="{prefix}-t {prefix}-d">'
            f'<title id="{prefix}-t">How a document job moves through the local workcell</title>'
            f'<desc id="{prefix}-d">{escape(DESCRIPTION)}</desc>{body}</svg>')


def narrow_svg(prefix: str = "cell-narrow") -> str:
    """Vertical route for phone widths; drawn at roughly 1:1 on a 360px column."""
    parts = [_defs(prefix)]
    parts.append(_doc(70, 4, 220, 62))
    parts.append('<text x="84" y="30" class="dg-title-sm">Fictional input</text>')
    parts.append('<text x="84" y="53" class="dg-mono">SVG v0.1 · PNG v0.2</text>')
    parts.append(f'<path d="M180 66V150" class="dg-route" marker-end="url(#{prefix}-arrow)"/>')
    parts.append(f'<rect x="10" y="100" width="340" height="480" fill="none" stroke="url(#{prefix}-hatch)" stroke-width="12"/>')
    parts.append('<rect x="150" y="92" width="60" height="16" class="dg-bg"/>')
    parts.append('<rect x="150" y="572" width="60" height="16" class="dg-bg"/>')
    parts.append('<rect x="190" y="112" width="148" height="28" class="dg-boundary"/>')
    parts.append('<text x="200" y="131" class="dg-tab">LOCAL CELL</text>')
    y = 156
    for index, (title, sub, evidence) in enumerate(STATIONS):
        parts.append(f'<rect x="60" y="{y}" width="268" height="78" class="dg-plate"/>')
        parts.append(f'<text x="74" y="{y+26}" class="dg-title">{escape(title)}</text>')
        parts.append(f'<text x="74" y="{y+48}" class="dg-sub">{escape(sub)}</text>')
        parts.append(f'<text x="74" y="{y+68}" class="dg-ev-text">records {escape(evidence)}</text>')
        if index < len(STATIONS) - 1:
            parts.append(f'<path d="M194 {y+78}V{y+100}" class="dg-route" marker-end="url(#{prefix}-arrow)"/>')
        y += 104
    # Recovery lane on the left: ocr-node back to the coordinator.
    parts.append(f'<path d="M60 299H32V195H54" class="dg-recovery" marker-end="url(#{prefix}-arrow)"/>')
    parts.append(_clock(36, 220))
    parts.append(_retry(36, 248))
    parts.append(f'<path d="M194 546V612" class="dg-route" marker-end="url(#{prefix}-arrow)"/>')
    parts.append(_check_square(110, 618, 26))
    parts.append('<text x="146" y="638" class="dg-title-sm">Checked output</text>')
    parts.append('<text x="146" y="660" class="dg-sub">delivered once, hash recorded</text>')
    parts.append('<text x="10" y="700" class="dg-sub">One computer · fictional inputs</text>')
    parts.append(_clock(10, 716))
    parts.append('<text x="34" y="729" class="dg-state">WAITING_WORKER</text>')
    parts.append('<text x="34" y="749" class="dg-sub">keeps its place until OCR is free</text>')
    parts.append(_retry(10, 762))
    parts.append('<text x="34" y="775" class="dg-state">RETRY_PENDING</text>')
    parts.append('<text x="34" y="795" class="dg-sub">one transient failure; attempt 2 of 2</text>')
    body = "".join(parts)
    return (f'<svg class="dg dg-narrow" viewBox="0 0 360 805" role="img" aria-labelledby="{prefix}-t {prefix}-d">'
            f'<title id="{prefix}-t">How a document job moves through the local workcell</title>'
            f'<desc id="{prefix}-d">{escape(DESCRIPTION)}</desc>{body}</svg>')


def mark_svg(size: int = 40, title: str = "Local AI Workcell", decorative: bool = True) -> str:
    """The cell mark: a square with input and output ports, one route, and a hatched floor edge.

    Decorative by default because it always sits beside the wordmark text.
    """
    label = 'aria-hidden="true"' if decorative else f'role="img" aria-label="{escape(title)}"'
    return f"""<svg class="mark" width="{size}" height="{size}" viewBox="0 0 48 48" {label}>
<path d="M6 6H42V17M42 31V42H6V31M6 17V6" class="mk-frame"/>
<path d="M0 24H17Q24 24 24 17V14M24 14Q24 24 31 24H34" class="mk-route"/>
<path d="M32 21l3 3-3 3" class="mk-route"/>
<path d="M36 24h12" class="mk-route"/>
<rect x="6" y="38" width="36" height="4" class="mk-floor"/>
</svg>"""


STATE_GLYPHS = {
    "DELIVERED": '<svg class="glyph" viewBox="0 0 16 16" aria-hidden="true"><rect width="16" height="16" class="g-fill"/><path d="M4 8.5l2.6 2.6L12 5.5" class="g-cut"/></svg>',
    "FAILED": '<svg class="glyph" viewBox="0 0 16 16" aria-hidden="true"><rect width="16" height="16" class="g-fail"/><path d="M4.5 4.5l7 7M11.5 4.5l-7 7" class="g-cut"/></svg>',
    "WAITING_WORKER": '<svg class="glyph" viewBox="0 0 16 16" aria-hidden="true"><rect x="1" y="1" width="14" height="14" class="g-dash"/><path d="M8 4.5V8l2.5 1.5" class="g-line"/></svg>',
    "RETRY_PENDING": '<svg class="glyph" viewBox="0 0 16 16" aria-hidden="true"><rect x="1" y="1" width="14" height="14" class="g-dash"/><path d="M11.5 8a3.5 3.5 0 1 1-1.2-2.6M10.6 3.6v2h-2" class="g-line"/></svg>',
}
ROUTED_GLYPH = '<svg class="glyph" viewBox="0 0 16 16" aria-hidden="true"><rect x="1" y="1" width="14" height="14" class="g-line"/></svg>'


def state_glyph(state: str) -> str:
    return STATE_GLYPHS.get(state, ROUTED_GLYPH)


DIAGRAM_CSS = """
.dg { display: block; width: 100%; height: auto; overflow: visible; }
.dg text { font-family: "Archivo", "Segoe UI", system-ui, sans-serif; fill: var(--ink); }
.dg .dg-title { font-size: 18px; font-weight: 700; font-stretch: 112%; }
.dg .dg-title-sm { font-size: 17px; font-weight: 700; font-stretch: 112%; }
.dg .dg-sub { font-size: 15px; fill: var(--ink-2); }
.dg .dg-mono, .dg .dg-state, .dg .dg-tab, .dg .dg-ev-text { font-family: "Martian Mono", Consolas, monospace; }
.dg .dg-mono { font-size: 13px; fill: var(--ink-2); }
.dg .dg-state { font-size: 13px; font-weight: 600; }
.dg .dg-tab { font-size: 13px; font-weight: 600; fill: var(--boundary-ink); }
.dg .dg-ev-text { font-size: 12.5px; fill: var(--evidence); }
.dg .dg-ev-label { font-size: 15px; fill: var(--evidence); font-weight: 600; }
.dg .dg-boundary { fill: var(--boundary); }
.dg .dg-boundary-ink { fill: var(--boundary-ink); }
.dg .dg-bg { fill: var(--bg); }
.dg .dg-plate { fill: var(--surface); stroke: var(--line); stroke-width: 1.5; }
.dg .dg-plate-line { fill: none; stroke: var(--line); stroke-width: 1.5; }
.dg .dg-route { fill: none; stroke: var(--ink); stroke-width: 2.5; }
.dg .dg-ink-fill { fill: var(--ink); }
.dg .dg-check { fill: none; stroke: var(--bg); stroke-width: 3; }
.dg .dg-recovery { fill: none; stroke: var(--ink); stroke-width: 2; stroke-dasharray: 7 6; }
.dg .dg-glyph { fill: none; stroke: var(--ink); stroke-width: 1.8; }
.dg .dg-ev-line { fill: none; stroke: var(--evidence); stroke-width: 1.6; }
.dg .dg-ev-fill { fill: var(--evidence); }
.dg .dg-ev-rail { fill: none; stroke: var(--evidence); stroke-width: 3; }
.mark .mk-frame { fill: none; stroke: var(--ink); stroke-width: 3.5; }
.mark .mk-route { fill: none; stroke: var(--ink); stroke-width: 3; stroke-linecap: square; }
.mark .mk-floor { fill: var(--boundary); }
.glyph { width: 15px; height: 15px; flex: 0 0 15px; }
.glyph .g-fill { fill: var(--ink); }
.glyph .g-fail { fill: var(--fail); }
.glyph .g-cut { fill: none; stroke: var(--surface); stroke-width: 2; }
.glyph .g-line { fill: none; stroke: var(--ink); stroke-width: 1.6; }
.glyph .g-dash { fill: none; stroke: var(--ink); stroke-width: 1.6; stroke-dasharray: 3 2; }
"""
