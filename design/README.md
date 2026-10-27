# Presentation assets

Everything in `docs/brand/` is generated. Nothing in it is drawn by hand, and every number comes from a fresh synthetic run or `docs/v2-sample-report.json`.

| File | What it is |
| --- | --- |
| `hero-light.png`, `hero-dark.png` | README hero, served through `<picture>` by GitHub theme |
| `social-preview.png` | 1280 × 640 GitHub social preview |
| `replay.gif`, `replay.mp4`, `replay-poster.png` | Job `480a7caaea1a` replayed from its manifest, one frame per event; the poster is the reduced-motion fallback |
| `view-trail.png`, `view-v2.png`, `view-mobile.png` | Annotated captures of the committed status page |

## Regenerate

Requires Python 3.11+, Node.js 20+, Chrome or Edge, and FFmpeg on `PATH`.

```bash
python scripts/refresh_demo.py      # status page first, because the views capture it
python design/compose.py            # writes design/build/*.html
npm install --prefix design         # playwright-core, development only
node design/render.mjs              # writes docs/brand/*
```

`compose.py` imports the same `workcell/diagram.py` the status page uses, so the README hero, the replay, and the page can't drift apart. Review the PNGs at 100% before committing; the renderer reports file sizes.
