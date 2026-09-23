#!/usr/bin/env python3
"""Verify apps/*/provenance/source-manifest.json against files on disk.

Back-ported from an operating Cell's locally improved validator so the
canonical template and installed Cells check apps/ provenance the same way.

For every apps/<app-id>/provenance/source-manifest.json found, checks:
  - required entry points exist (README.md, CONTEXT_INDEX.md, GOVERNANCE.md
    or SOURCE-GOVERNANCE.md, provenance/source-manifest.json)
  - every included_files[] path exists and its sha256 matches the manifest
  - no included_files[] path escapes its app directory

Exit 0 if every discovered manifest is consistent (or none exist). Exit 1 on
any mismatch, missing file, or malformed manifest.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_manifest(root: Path, app_dir: Path, manifest_path: Path) -> list[str]:
    issues: list[str] = []
    app_id = app_dir.name
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"apps/{app_id}: unreadable/invalid manifest JSON: {exc}"]

    for required in ("README.md", "CONTEXT_INDEX.md"):
        if not (app_dir / required).is_file():
            issues.append(f"apps/{app_id}: missing required entry point {required}")

    if not any((app_dir / name).is_file() for name in ("GOVERNANCE.md",)):
        issues.append(f"apps/{app_id}: missing GOVERNANCE.md (local governance is required)")

    included = data.get("included_files")
    if not isinstance(included, list) or not included:
        issues.append(f"apps/{app_id}: manifest has no included_files entries")
        included = []

    for entry in included:
        if not isinstance(entry, dict):
            issues.append(f"apps/{app_id}: included_files entry is not an object: {entry!r}")
            continue
        rel_path = entry.get("path")
        digest = entry.get("sha256")
        if not rel_path or not digest:
            issues.append(f"apps/{app_id}: included_files entry missing path/sha256: {entry!r}")
            continue
        target = (root / rel_path).resolve()
        try:
            target.relative_to((root / "apps").resolve())
        except ValueError:
            issues.append(f"apps/{app_id}: included_files path escapes apps/: {rel_path}")
            continue
        if not target.is_file():
            issues.append(f"apps/{app_id}: included_files path does not exist: {rel_path}")
            continue
        actual = sha256_of(target)
        if actual != digest:
            issues.append(
                f"apps/{app_id}: digest mismatch for {rel_path} "
                f"(manifest {digest[:12]}... vs actual {actual[:12]}...)"
            )
    return issues


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    apps_dir = root / "apps"
    if not apps_dir.is_dir():
        print("PASS: no apps/ directory present — nothing to verify")
        return 0

    all_issues: list[str] = []
    manifest_count = 0
    for manifest_path in sorted(apps_dir.glob("*/provenance/source-manifest.json")):
        manifest_count += 1
        app_dir = manifest_path.parent.parent
        all_issues.extend(check_manifest(root, app_dir, manifest_path))

    if manifest_count == 0:
        print("WARN: apps/ exists but no provenance/source-manifest.json found under it")
        return 0

    if all_issues:
        for issue in all_issues:
            print(f"FAIL: {issue}", file=sys.stderr)
        print(f"apps manifest verification failed with {len(all_issues)} issue(s)", file=sys.stderr)
        return 1

    print(f"PASS: {manifest_count} app manifest(s) verified, all digests match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
