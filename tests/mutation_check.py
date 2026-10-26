"""A planted output defect must be detected by the checksum validator."""

from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from workcell.core import Workcell, WorkcellError, verify_job

fixture = (Path(__file__).resolve().parent.parent / "fixtures" / "synthetic-a.svg").read_bytes()
work_temp = Path(__file__).resolve().parent.parent / "_tmp"
work_temp.mkdir(exist_ok=True)
with TemporaryDirectory(dir=work_temp) as temporary:
    root = Path(temporary)
    cell = Workcell(root)
    identifier = cell.submit(fixture)["job_id"]
    cell.advance(identifier)
    output = root / "results" / f"{identifier}.json"
    output.write_bytes(output.read_bytes() + b"\nPLANTED_CHANGE")
    try:
        verify_job(root, identifier)
    except WorkcellError as exc:
        if "Checksum mismatch: delivery_sha256" not in str(exc):
            raise
    else:
        raise SystemExit("MUTATION_FAIL checksum defect was not detected")
print("MUTATION_OK delivered-output checksum defect detected")
