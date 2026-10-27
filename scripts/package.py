"""Create a deterministic allowlisted public source ZIP and SHA-256 inventory."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = (".gitattributes", ".gitignore", "README.md", "PRODUCT.md", "DESIGN.md", "LICENSE", "SECURITY.md", "THIRD_PARTY_NOTICES.md", "pyproject.toml", "index.html")
DIRECTORIES = (".github", "assets", "workcell", "fixtures", "tests", "scripts", "docs")
SKIP = {"__pycache__", ".pytest_cache", "test-results"}


def collect() -> list[Path]:
    paths = [ROOT / name for name in FILES]
    for directory in DIRECTORIES:
        paths.extend(path for path in (ROOT / directory).rglob("*") if path.is_file() and not any(part in SKIP for part in path.relative_to(ROOT).parts))
    for path in paths:
        if not path.is_file() or path.is_symlink():
            raise SystemExit(f"PACKAGE_FAIL missing or linked file: {path.relative_to(ROOT)}")
        name = path.relative_to(ROOT).as_posix()
        if not name.isascii() or len(path.read_bytes()) > 50_000_000:
            raise SystemExit(f"PACKAGE_FAIL nonportable or oversized file: {name}")
    return sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit("PACKAGE_FAIL output directory must be empty")
    args.output.mkdir(parents=True, exist_ok=True)
    paths = collect()
    inventory = []
    archive = args.output / "local-ai-workcell-public.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as bundle:
        for path in paths:
            name = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            bundle.writestr(info, data)
            inventory.append(f"{hashlib.sha256(data).hexdigest()}  {name}")
    inv = args.output / "CONTENT_INVENTORY.sha256"
    inv.write_text("\n".join(inventory) + "\n", encoding="utf-8", newline="\n")
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    print(f"PACKAGE_OK files={len(paths)} zip_sha256={digest(archive)} inventory_sha256={digest(inv)}")


if __name__ == "__main__":
    main()
