"""Verify that the repository still matches the recorded LangChain audit.

The audit document itself is excluded so its stored digest is not recursive.
Tracked files and non-ignored untracked files are both included.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path


AUDIT_PATH = "docs/wiki/_langchain_version_audit.md"


def managed_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    paths = result.stdout.decode().split("\0")
    return sorted(path for path in paths if path and path != AUDIT_PATH)


def inventory_digest(root: Path, paths: list[str]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        path_bytes = path.encode()
        content = (root / path).read_bytes()
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def recorded_value(audit_text: str, key: str) -> str:
    prefix = f"{key}: "
    for line in audit_text.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip().strip('"')
    raise ValueError(f"{key!r} is missing from {AUDIT_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the current inventory with the recorded audit",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    paths = managed_files(root)
    digest = inventory_digest(root, paths)
    print(f"managed_file_count: {len(paths)}")
    print(f"inventory_sha256: {digest}")

    if not args.check:
        return 0

    audit = (root / AUDIT_PATH).read_text()
    expected_count = int(recorded_value(audit, "managed_file_count"))
    expected_digest = recorded_value(audit, "inventory_sha256")
    if len(paths) != expected_count or digest != expected_digest:
        print("audit_status: stale")
        return 1
    print("audit_status: current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
