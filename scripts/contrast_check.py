"""Check every named DESIGN.md token pair with the WCAG 2.x contrast formula.

Reads the OKLCH token table in DESIGN.md. ``--write`` refreshes
docs/CONTRAST_CHECK.txt; without it the retained report must match.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "CONTRAST_CHECK.txt"

# (foreground, background, minimum, note, themes). 4.5 = normal text, 3 = non-text UI and graphics.
PAIRS = [
    ("ink", "bg", 4.5, ""), ("ink", "surface", 4.5, ""),
    ("ink-2", "bg", 4.5, ""), ("ink-2", "surface", 4.5, ""),
    ("boundary-ink", "boundary", 4.5, "text and hatch on yellow"),
    ("evidence", "bg", 4.5, ""), ("evidence", "surface", 4.5, ""),
    ("fail", "bg", 4.5, ""), ("fail", "surface", 4.5, ""),
    ("line", "bg", 3, ""), ("line", "surface", 3, ""),
    # The boundary edge: graphite hatch carries it on the light floor, yellow itself on the dark floor.
    ("boundary-ink", "bg", 3, "boundary edge from hatch", ("light",)),
    ("boundary", "bg", 3, "boundary edge from yellow", ("dark",)),
    ("evidence", "bg", 3, "focus ring"),
]
ROW = re.compile(r"^\| `--([a-z0-9-]+)` \| `([\d. ]+)` \| `([\d. ]+)` \|", re.MULTILINE)


def read_tokens() -> dict[str, dict[str, tuple[float, float, float]]]:
    tokens: dict[str, dict[str, tuple[float, float, float]]] = {"light": {}, "dark": {}}
    for name, light, dark in ROW.findall((ROOT / "DESIGN.md").read_text(encoding="utf-8")):
        tokens["light"][name] = tuple(float(v) for v in light.split())
        tokens["dark"][name] = tuple(float(v) for v in dark.split())
    return tokens


def luminance(color: tuple[float, float, float]) -> float:
    lightness, chroma, hue = color
    a = chroma * math.cos(math.radians(hue))
    b = chroma * math.sin(math.radians(hue))
    l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (lightness - 0.0894841775 * a - 1.291485548 * b) ** 3
    clamp = lambda v: min(1.0, max(0.0, v))
    red = clamp(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s)
    green = clamp(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s)
    blue = clamp(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def ratio(fg: tuple[float, float, float], bg: tuple[float, float, float]) -> float:
    high, low = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def main() -> int:
    tokens = read_tokens()
    lines = ["Contrast check: WCAG 2.x relative luminance from DESIGN.md OKLCH tokens", ""]
    failures = 0
    for theme in ("light", "dark"):
        for fg, bg, minimum, note, *only in PAIRS:
            if only and theme not in only[0]:
                continue
            missing = [name for name in (fg, bg) if name not in tokens[theme]]
            if missing:
                raise SystemExit(f"DESIGN.md is missing --{missing[0]} for {theme}")
            value = ratio(tokens[theme][fg], tokens[theme][bg])
            failures += value < minimum
            suffix = f", {note}" if note else ""
            minimum_text = f"{minimum:g}"
            lines.append(
                f"{'PASS' if value >= minimum else 'FAIL'} {theme} --{fg} on --{bg} "
                f"{value:.2f}:1 (minimum {minimum_text}:1{suffix})"
            )
    report = "\n".join(lines) + "\n"
    if "--write" in sys.argv:
        REPORT.write_text(report, encoding="utf-8", newline="\n")
    elif not REPORT.exists() or REPORT.read_text(encoding="utf-8").replace("\r\n", "\n") != report:
        print("docs/CONTRAST_CHECK.txt is missing or stale; run python scripts/contrast_check.py --write", file=sys.stderr)
        return 1
    if failures:
        print(report, file=sys.stderr)
        print(f"CONTRAST_CHECK_FAILED pairs={failures}", file=sys.stderr)
        return 1
    print(f"CONTRAST_CHECK_OK pairs={len(lines) - 2}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
