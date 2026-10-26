"""Recreate three original synthetic PNG inputs for the v0.2 OCR proof."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fixtures" / "v2"
OUT.mkdir(parents=True, exist_ok=True)
FONT = Path("C:/Windows/Fonts/arial.ttf")
if not FONT.exists():
    raise SystemExit("FIXTURE_FAIL Arial font is required for byte-identical fixture regeneration")

for ordinal, word in enumerate(("ONE", "TWO", "THREE"), 1):
    image = Image.new("RGB", (1200, 230), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT), 64)
    draw.text((55, 65), f"SYNTHETIC WORKCELL {word}", font=font, fill="black")
    image.save(OUT / f"synthetic-{ordinal}.png", optimize=False)
print("FIXTURE_OK count=3 public synthetic PNG inputs")
