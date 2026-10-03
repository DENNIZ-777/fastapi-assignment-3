"""Calculate a stable hash of the application source files."""

import hashlib
from pathlib import Path


def get_all_src_py_files_hash() -> str:
    src_dir = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()

    for path in sorted(src_dir.rglob("*.py"), key=lambda item: item.relative_to(src_dir).as_posix()):
        with path.open("rb") as source_file:
            for chunk in iter(lambda: source_file.read(8192), b""):
                digest.update(chunk)

    return digest.hexdigest()
