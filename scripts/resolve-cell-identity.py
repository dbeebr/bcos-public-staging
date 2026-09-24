#!/usr/bin/env python3
"""Canonical repository/Cell/provenance identity resolution.

BRIEF-20260717-004 / FAIL-PATTERN-20260717-011: `personalize-team-cell.sh`
and `teamcell-install-preview.py` each had their own ad hoc, divergent (or
absent) resolution logic for "what repository is this", "what is this
Cell/project called", and "who is this artifact on behalf of". That produced
`Repository: unknown`, Cell name `To be confirmed.`, and a raw
`human:{{CELL_OWNER_ID}}` template token surviving into real, committed
Cells.

This module is the single deterministic resolver both scripts call instead
of re-implementing their own fallback chains. It never invents a person and
never falls back to brittle prose-line matching against TEAM-PROFILE.md
body text.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - same soft dependency as the scripts calling this
    yaml = None


@dataclass
class Resolution:
    value: Optional[str]
    source: str
    resolved: bool

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "source": self.source, "resolved": self.resolved}


def _load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists() or yaml is None:
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _read_frontmatter(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return None
    if yaml is None:
        return None
    try:
        data = yaml.safe_load("\n".join(lines[1:end_idx]))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def normalize_remote_to_owner_repo(remote_url: str) -> Optional[str]:
    """`git@github.com:owner/repo.git` / `https://github.com/owner/repo.git` -> `owner/repo`."""
    remote_url = remote_url.strip()
    if not remote_url:
        return None
    m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", remote_url)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    if not owner or not repo:
        return None
    return f"{owner}/{repo}"


def _git_remote_owner_repo(target_path: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(target_path), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return normalize_remote_to_owner_repo(result.stdout)


def resolve_repository(target_path: Path) -> Resolution:
    """Deterministic order (BRIEF-20260717-004 Scope A):
    1. installation receipt target.repository
    2. verified git remote.origin.url, normalized
    3. explicit structured repository field in PROJECT.md/TEAM-PROFILE.md frontmatter
    4. unresolved
    """
    receipt = _load_yaml(target_path / ".installation" / "TEAMCELL-INSTALLATION-RECEIPT.yaml")
    if receipt:
        repo = (receipt.get("target") or {}).get("repository")
        if repo:
            return Resolution(str(repo), "installation_receipt", True)

    remote_repo = _git_remote_owner_repo(target_path)
    if remote_repo:
        return Resolution(remote_repo, "git_remote", True)

    for fname, key in (("PROJECT.md", "repository"), ("TEAM-PROFILE.md", "repository")):
        fm = _read_frontmatter(target_path / fname)
        if fm and fm.get(key):
            return Resolution(str(fm[key]), f"{fname}_frontmatter", True)

    return Resolution(None, "unresolved", False)


_GENERIC_TITLES = {
    "teamcell lite project context",
    "team profile",
}


def resolve_display_name(target_path: Path, repository: Optional[str] = None) -> Resolution:
    """Deterministic order (BRIEF-20260717-004 Scope A; 0 added by TASK-20260921-003):
    0. an explicit setup name recorded in instructions/PERSONALIZATION-MANIFEST.json
    1. canonical PROJECT.md structured title
    2. canonical TEAM-PROFILE.md structured cell_name field, if present
    3. repository slug, transformed, as an explicit display fallback
    4. unresolved
    """
    # A display name confirmed at setup (--cell-name) and recorded by the
    # mandatory personalization step outranks derived names.
    manifest_path = target_path / "instructions" / "PERSONALIZATION-MANIFEST.json"
    if manifest_path.exists():
        try:
            manifest_cell = (json.loads(manifest_path.read_text(encoding="utf-8")) or {}).get("cell") or {}
        except (ValueError, OSError):
            manifest_cell = {}
        if manifest_cell.get("name") and manifest_cell.get("name_source") == "explicit":
            return Resolution(str(manifest_cell["name"]), "personalization_manifest", True)

    project_fm = _read_frontmatter(target_path / "PROJECT.md")
    if project_fm and project_fm.get("title"):
        title = str(project_fm["title"]).strip()
        if title and title.lower() not in _GENERIC_TITLES:
            return Resolution(title, "project_md_title", True)

    profile_fm = _read_frontmatter(target_path / "TEAM-PROFILE.md")
    if profile_fm and profile_fm.get("cell_name"):
        name = str(profile_fm["cell_name"]).strip()
        if name:
            return Resolution(name, "team_profile_cell_name", True)

    if repository is None:
        repository = resolve_repository(target_path).value

    if repository:
        slug = repository.split("/")[-1]
        display = re.sub(r"[-_]+", " ", slug).strip().title()
        if display:
            return Resolution(display, "repository_slug_fallback", True)

    return Resolution(None, "unresolved", False)


_HUMAN_ID_RE = re.compile(r"^human:[A-Za-z0-9._-]+$")


def resolve_on_behalf_of_human_id(
    target_path: Path, confirmed_by_override: Optional[str] = None
) -> Resolution:
    """Deterministic order (BRIEF-20260717-004 Scope A, "on-behalf-of identity"):

    `on_behalf_of_human_id` is a per-artifact provenance field (who this was
    created/confirmed for), not the same identity as `cell_owner_role` /
    `role_bindings` (ownership authority) -- see
    docs/architecture/BCOS-PUBLIC-CELL-TARGET-STRUCTURE-20260705.md and
    kernel/schemas/teamcell-cell-ownership.schema.md. It must never be invented from
    display text and must never equal `cell_owner_role` by assumption.

    1. an explicit confirmed_by value the caller already has at install time
       (e.g. `--confirmed-by`), if it is a `human:<id>` identity;
    2. the installation receipt's `preview_confirmed.confirmed_by`, if it is
       a `human:<id>` identity;
    3. the installation receipt's `governance.selected_by`, if it is a
       `human:<id>` identity;
    4. unresolved (`None` / YAML `null`) -- never a raw `{{CELL_OWNER_ID}}`
       token and never a guessed person.
    """
    if confirmed_by_override and _HUMAN_ID_RE.match(confirmed_by_override):
        return Resolution(confirmed_by_override, "confirmed_by_override", True)

    receipt = _load_yaml(target_path / ".installation" / "TEAMCELL-INSTALLATION-RECEIPT.yaml")
    if receipt:
        confirmed_by = (receipt.get("preview_confirmed") or {}).get("confirmed_by")
        if confirmed_by and _HUMAN_ID_RE.match(str(confirmed_by)):
            return Resolution(str(confirmed_by), "receipt_confirmed_by", True)

        selected_by = (receipt.get("governance") or {}).get("selected_by")
        if selected_by and _HUMAN_ID_RE.match(str(selected_by)):
            return Resolution(str(selected_by), "receipt_governance_selected_by", True)

    return Resolution(None, "unresolved", False)


def resolve_all(target_path: Path, confirmed_by_override: Optional[str] = None) -> Dict[str, Any]:
    repository = resolve_repository(target_path)
    display_name = resolve_display_name(target_path, repository.value)
    on_behalf_of = resolve_on_behalf_of_human_id(target_path, confirmed_by_override)
    return {
        "repository": repository.to_dict(),
        "display_name": display_name.to_dict(),
        "on_behalf_of_human_id": on_behalf_of.to_dict(),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-path", required=True, type=Path)
    parser.add_argument(
        "--field",
        choices=["repository", "display_name", "on_behalf_of_human_id", "all"],
        default="all",
    )
    parser.add_argument(
        "--confirmed-by",
        default=None,
        help="Install-time confirmed_by value, if known (e.g. teamcell-install-preview.py's --confirmed-by).",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON (default for --field all).")
    args = parser.parse_args(argv)

    target_path = args.target_path
    if not target_path.is_dir():
        print(f"ERROR: target path does not exist or is not a directory: {target_path}", file=sys.stderr)
        return 1

    if args.field == "all":
        result = resolve_all(target_path, args.confirmed_by)
        print(json.dumps(result, indent=2))
        return 0

    if args.field == "repository":
        result = resolve_repository(target_path)
    elif args.field == "display_name":
        result = resolve_display_name(target_path)
    else:
        result = resolve_on_behalf_of_human_id(target_path, args.confirmed_by)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(result.value if result.value is not None else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
