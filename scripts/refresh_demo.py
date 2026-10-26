"""Refresh the committed static landing view from the same synthetic workflow."""

from pathlib import Path
from tempfile import TemporaryDirectory
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from workcell.cli import demo

WORK_TEMP = ROOT / "_tmp"
WORK_TEMP.mkdir(exist_ok=True)
with TemporaryDirectory(dir=WORK_TEMP) as temporary:
    generated = Path(temporary) / "run"
    demo(generated)
    (ROOT / "index.html").write_bytes((generated / "index.html").read_bytes())
print("STATIC_DEMO_OK index.html refreshed from synthetic run")
