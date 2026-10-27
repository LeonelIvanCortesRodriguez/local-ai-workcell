# Design system: Local AI Workcell

## Visual theme

A marked workshop cell. Picture a machine bay with stations bolted to the floor, each with a stamped plate, and a yellow-and-graphite safety line painted around the whole bay. Jobs enter on one side, move station to station along drawn routes, and leave with a tag. That painted boundary is the brand: it stands for "local, controlled, inside the proof".

Color strategy: **restrained** in the product, **committed** in the social preview (graphite field carrying the yellow boundary). Light and dark are designed separately: light is a daylight bay with graphite plates; dark is the same bay at night with lit plates and the boundary still the brightest thing.

## Mark and wordmark

- **Mark:** a square cell drawn as a 2px graphite outline with one notch on the left (input port) and one on the right (output port). A single route enters the left port, bends once, and leaves the right port ending in a small check. A short hatched yellow segment along the bottom edge is the floor boundary. It must read at 16px (favicon) by dropping the hatch and keeping the ports.
- **Wordmark:** "Local AI Workcell" set in Archivo at width 112 (SemiExpanded), weight 700, tracking 0. "Workcell" is never split into two words. No gradient, no glow.

## Color tokens

All values OKLCH. Contrast measured with WCAG 2.x relative luminance (`scripts/contrast_check.mjs`, added with the visual implementation).

| Role | Light | Dark | Meaning (stable) |
| --- | --- | --- | --- |
| `--bg` | `0.975 0.003 260` | `0.18 0.008 260` | Bay floor |
| `--surface` | `1 0 0` | `0.22 0.009 260` | Station plate |
| `--ink` | `0.22 0.012 260` | `0.95 0.004 260` | Text, routes, delivered state |
| `--ink-2` | `0.40 0.012 260` | `0.78 0.008 260` | Secondary text |
| `--line` | `0.62 0.01 260` | `0.52 0.01 260` | Plate borders, waiting outlines |
| `--boundary` | `0.86 0.17 95` | `0.84 0.16 95` | The local cell boundary. A fill, never a text color |
| `--boundary-ink` | `0.22 0.012 260` | `0.18 0.008 260` | Text and hatch stripes placed on the yellow fill, in both themes |
| `--evidence` | `0.47 0.13 255` | `0.76 0.11 250` | Hashes, manifests, recorded evidence; also focus ring |
| `--fail` | `0.50 0.17 28` | `0.74 0.14 28` | Failed or rejected only |

`scripts/contrast_check.py` reads this table and tests every named foreground and background pair in both themes; its output is retained in `docs/CONTRAST_CHECK.txt`. The dark theme's `--ink` is a light color and must never be placed on `--boundary`; that pairing measures 1.4:1. Only `--boundary-ink` goes on yellow.

Yellow means the boundary and nothing else. It is never used for "warning", "waiting", or decoration. The boundary is always drawn as yellow with `--boundary-ink` hatch stripes. On the light floor the hatch supplies the 3:1 edge that yellow alone would not; on the dark floor the yellow itself does.

## State language

Every state has a shape, a word, and a line style. Color is the fourth cue, not the first.

| State | Shape | Line | Label |
| --- | --- | --- | --- |
| DELIVERED | Filled ink square with a check | Solid 2px | Delivered · checksum |
| ROUTED / in progress | Ink outline square | Solid 2px | Routed to `ocr-node` |
| WAITING_WORKER | Outline square with a small clock | Dashed 2px | Waiting for capability |
| RETRY_PENDING | Outline square with a circular arrow and `1/2` | Dashed 2px | Retry 1 of 2 |
| TRANSPORT_DISCONNECT (v0.2) | Broken route segment | Gap in line | Connection dropped, requeued |
| FAILED | Fail-colored square with an X | Solid 2px | Failed · reason code |

## Typography

- **Archivo** (OFL, variable width and weight). Wordmark and headings at width 112, weight 650 to 700. Body at width 100, weight 400, 17px, line-height 1.55.
- **Martian Mono** (OFL). Job IDs, hashes, state codes, and commands only, 14 to 15px. Never body copy.
- Scale: 15 / 17 / 21 / 27 / 34 / 44 / 56px (about 1.27 ratio). Hero heading clamp(2.25rem, 5vw, 3.5rem), letter-spacing -0.015em, `text-wrap: balance`.
- Prose capped at 68ch. No uppercase except state codes, which are literal values from the manifest.
- The live page self-hosts Latin woff2 subsets of both families with `font-display: swap` and a system fallback. No font is fetched from a third party at runtime.

## Layout

- The first fold holds four things in this order: wordmark plus promise, the cell diagram, one result line taken from the manifest ("2 of 2 synthetic jobs delivered · 1 waited · 1 retried"), and two actions (Run it locally, Inspect the recovery trail).
- The cell diagram spans the full content width (max 1200px). It is never squeezed into a side column.
- Content widths: prose 68ch; diagrams and figures up to 1200px; gutters 24px desktop, 16px mobile.
- At 390px the cell diagram rotates to a vertical route; station labels stay at 15px minimum.
- No cards for unequal content. Stations are plates because they are literally stations; nothing else borrows that treatment.

## Diagram language

- **Primary diagram:** `controlled input → coordinator → capability-routed workers → validation → checked output`, drawn inside the yellow boundary. The recovery path runs underneath in dashed line and rejoins at the coordinator: WAITING_WORKER (clock) and RETRY_PENDING (circular arrow).
- Arrows are labeled with what they carry: "input hash", "manifest event", "result hash", "delivery hash". An unlabeled arrow means the diagram is unfinished.
- The v0.2 diagram is a separate figure with the same grammar: SQLite queue as a shelf, two OCR plates, one validation plate, and the broken-segment disconnect with "requeued" label.
- Every diagram ships as SVG with `<title>` and `<desc>`, plus a text equivalent in the README directly below it.
- The text "one computer · fictional inputs" sits on a solid yellow label tab cut into the boundary line, set in `--boundary-ink`, so the limit is part of the picture.

## Media treatment

- **README hero:** a rendered PNG of the cell diagram with wordmark and promise, in a light and a dark version served through `<picture>` with `prefers-color-scheme`. 1600 × 720 source, about 160KB each at most.
- **Social preview:** 1280 × 640 PNG on a graphite field with the boundary, mark, wordmark, promise, and "Python · local synthetic proof". Text sits at least 64px inside every edge.
- **Demonstration:** one job's recovery path (enters, waits for a worker, retries once, delivers) as a 10 to 15 second loop. GIF for the README (under 2.5MB, 960px wide), MP4 for the Pages site with a poster frame. Generated from the real manifest; no cursor wandering, no loading screens.
- **Product views:** three annotated captures (route and result, recovery trail, v0.2 report). Each annotation names the outcome ("the job resumed at OCR after one retry"), placed outside the screenshot so the UI stays legible. No browser chrome frames.

## Motion

- Only state transitions move: a job token travels between stations along the route at 220ms per hop, ease-out-quart. The waiting state holds still with the dashed outline; nothing pulses.
- Under `prefers-reduced-motion: reduce`, the token is replaced by the complete static route with every state already drawn.
- All content renders without JavaScript. Animation enhances an already visible diagram.

## Do

- Put real values from `out/` and `docs/v2-sample-report.json` in every figure.
- Keep the boundary on every hero, preview, and diagram.
- Name the capability on each station ("ocr-node"), never a hostname.

## Don't

- Robots, brains, sparkles, neural meshes, glowing nodes, or purple.
- Green-on-black terminals or fake log scrolls.
- Fleet counters, uptime figures, or anything implying several machines.
- Yellow for warning, gradients, glass panels, rounded corners above 6px, or side-stripe callouts.
- A dashboard screenshot as the hero.
