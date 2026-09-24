#!/usr/bin/env python3
"""Generate a durable Teamcell installation receipt and registry entry.

After a confirmed, completed install (see `scripts/teamcell-install-preview.py`),
this script writes `.installation/TEAMCELL-INSTALLATION-RECEIPT.yaml` into the
target per `kernel/schemas/teamcell-installation-receipt.schema.md`, and
appends/creates the target's row in `control-plane/registries/BCOS-CELL-REGISTRY.md`.

Two input paths are supported:

1. `--from-manifest PATH` (default) — consumes the
   `.installation/INSTALL-PREVIEW-MANIFEST.json` written by
   `teamcell-install-preview.py`'s confirmed run. This is the normal path and
   guarantees the receipt matches exactly what the preview displayed (the
   install-semantics contract's consistency rule), because both files share
   the same underlying data.
2. Explicit `--field key=value` overrides / a hand-authored manifest JSON —
   for retroactive receipt generation against an already-completed install
   that predates this mechanism, where no fresh preview run exists.

This script never commits anything itself — writing `.installation/
TEAMCELL-INSTALLATION-RECEIPT.yaml` into the target repo and appending a row
to `control-plane/registries/BCOS-CELL-REGISTRY.md` are both working-tree-only writes. The
invoking agent/task commits through the standard AGENTS.md Git Write
Protocol ladder, per this task's Gate ("must not weaken AGENTS.md's existing
Git Write Protocol ladder — the receipt generator commits through the same
protocol as any other BCOS write").
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

MODES = ("new_from_template", "hydrate_existing_repo", "clone_existing_cell")
GOVERNANCE_PROFILES = ("quick_build", "operating_team", "compliance_safety")
DECISION_CLASSES = (
    "routine_work",
    "material_scope_change",
    "priority_change",
    "budget_change",
    "customer_promise",
    "legal_privacy",
    "people_impacting",
    "irreversible_action",
    "security_change",
    "external_visibility",
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PERSONALIZATION_STATUSES = ("generated", "not_applicable")


class ReceiptError(RuntimeError):
    """Actionable, user-facing generation failure."""


def load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ReceiptError(
            f"Manifest not found: {path}\n"
            "Repair: run scripts/teamcell-install-preview.py ... --confirm first "
            "(it writes this manifest), or pass --from-manifest with a hand-authored "
            "manifest matching the same JSON shape (see kernel/schemas/"
            "teamcell-installation-receipt.schema.md)."
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReceiptError(f"Manifest is not valid JSON: {path}\n{exc}") from exc


def apply_field_overrides(data: Dict[str, Any], overrides: List[str]) -> Dict[str, Any]:
    """Applies dotted-path key=value overrides, e.g. governance.governance_profile=quick_build."""
    for item in overrides:
        if "=" not in item:
            raise ReceiptError(f"--field expects DOTTED.PATH=VALUE, got: {item!r}")
        path, value = item.split("=", 1)
        keys = path.split(".")
        cursor = data
        for key in keys[:-1]:
            if key not in cursor or not isinstance(cursor[key], dict):
                cursor[key] = {}
            cursor = cursor[key]
        parsed_value: Any = value
        if value in ("null", "None"):
            parsed_value = None
        elif value in ("true", "false"):
            parsed_value = value == "true"
        cursor[keys[-1]] = parsed_value
    return data


def validate_manifest(data: Dict[str, Any]) -> List[str]:
    """Returns a list of validation error strings (empty = valid)."""
    errors: List[str] = []

    mode = data.get("installation_mode")
    if mode not in MODES:
        errors.append(f"installation_mode must be one of {MODES}, got: {mode!r}")

    source = data.get("source") or {}
    sha = source.get("commit_sha")
    if not sha or not SHA_RE.match(str(sha)):
        errors.append(f"source.commit_sha must be a well-formed 40-character SHA, got: {sha!r}")

    clone_source = source.get("clone_source") or {}
    if mode == "clone_existing_cell":
        if not clone_source.get("repository") or not clone_source.get("commit_sha"):
            errors.append(
                "source.clone_source.repository and .commit_sha must both be non-null "
                "when installation_mode is clone_existing_cell"
            )
        elif not SHA_RE.match(str(clone_source.get("commit_sha"))):
            errors.append(
                f"source.clone_source.commit_sha must be a well-formed 40-character SHA, "
                f"got: {clone_source.get('commit_sha')!r}"
            )
    else:
        if clone_source.get("repository") is not None or clone_source.get("commit_sha") is not None:
            errors.append(
                "source.clone_source must be fully null unless installation_mode is "
                "clone_existing_cell"
            )

    governance = data.get("governance") or {}
    profile = governance.get("governance_profile")
    legacy_unresolved = governance.get("legacy_unresolved")
    if profile is not None and profile not in GOVERNANCE_PROFILES:
        errors.append(f"governance.governance_profile must be one of {GOVERNANCE_PROFILES} or null, got: {profile!r}")
    if (profile is None) != bool(legacy_unresolved):
        errors.append(
            "governance.governance_profile must be null if and only if "
            f"governance.legacy_unresolved is true (profile={profile!r}, "
            f"legacy_unresolved={legacy_unresolved!r})"
        )
    decision_owner_roles = governance.get("decision_owner_roles") or {}
    missing_classes = [c for c in DECISION_CLASSES if c not in decision_owner_roles]
    if missing_classes:
        errors.append(f"governance.decision_owner_roles is missing keys: {missing_classes}")

    for pkg in data.get("installed_packages") or []:
        pkg_sha = pkg.get("source_commit_sha")
        if not pkg_sha or not SHA_RE.match(str(pkg_sha)):
            errors.append(
                f"installed_packages entry {pkg.get('package_id')!r} has a non-well-formed "
                f"source_commit_sha: {pkg_sha!r}"
            )

    personalization = data.get("personalization")
    if personalization is not None:
        status = (personalization or {}).get("status")
        if status not in PERSONALIZATION_STATUSES:
            errors.append(f"personalization.status must be one of {PERSONALIZATION_STATUSES}, got: {status!r}")
        elif status == "generated":
            required = personalization.get("required_outputs")
            if not isinstance(required, list) or not required or not all(isinstance(x, str) and x for x in required):
                errors.append("personalization.required_outputs must be a non-empty list of paths when status is generated")
            elif "instructions/PROJECT-INSTRUCTIONS.md" not in required:
                errors.append("personalization.required_outputs must include instructions/PROJECT-INSTRUCTIONS.md")
        elif status == "not_applicable" and not str(personalization.get("reason") or "").strip():
            errors.append("personalization.reason is required when status is not_applicable")

    rollback = data.get("rollback") or {}
    if rollback.get("method") not in ("git_revert", "git_reset_to_ref", "manual"):
        errors.append(f"rollback.method must be one of git_revert|git_reset_to_ref|manual, got: {rollback.get('method')!r}")
    if rollback.get("method") == "manual" and not (rollback.get("notes") or "").strip():
        errors.append("rollback.notes must be non-empty when rollback.method is manual")

    preview_confirmed = data.get("preview_confirmed") or {}
    if not preview_confirmed.get("confirmed_by"):
        errors.append("preview_confirmed.confirmed_by is required")
    confirmed_at = preview_confirmed.get("confirmed_at")
    installed_at = data.get("installed_at")
    if confirmed_at and installed_at and confirmed_at > installed_at:
        errors.append(
            f"preview_confirmed.confirmed_at ({confirmed_at}) must not be later than "
            f"installed_at ({installed_at})"
        )

    return errors


# Structural presence rules a package implies in an installed Cell. Kept in
# sync with the template kit's packages/PACKAGES.yaml "Reconciliation rule"
# by construction (both describe the same three packages) rather
# than by shared code, since one runs at receipt-generation time in Python
# against a real target filesystem and the other runs inside every
# installed Cell in POSIX sh with no repo-root context to read the source
# manifest from.
PACKAGE_MUST_BE_PRESENT = {
    "teamcell-plus-profile": ["ONBOARDING.md", "docs/CONTRACTS-V1.md"],
    "team-capability-pack": ["apps/team-capability-pack", "playbooks/onboarding/SKILL-PLAYGROUND.html"],
}
PACKAGE_MUST_BE_ABSENT_UNLESS_INSTALLED = PACKAGE_MUST_BE_PRESENT


def reconcile_package_tree(target: Path, installed_packages: List[Dict[str, Any]]) -> List[str]:
    """Returns a list of mismatch strings (empty = receipt matches the tree)."""
    errors: List[str] = []
    installed_ids = {pkg.get("package_id") for pkg in installed_packages}

    if (target / "profiles").exists():
        errors.append(
            "profiles/ is present in the installed tree — it is distribution source "
            "material in the template repository and must never appear in an "
            "installed Cell (baseline or optional)"
        )

    for package_id, must_be_present_paths in PACKAGE_MUST_BE_PRESENT.items():
        installed = package_id in installed_ids
        for rel in must_be_present_paths:
            exists = (target / rel).exists()
            if installed and not exists:
                errors.append(
                    f"installed_packages declares {package_id!r} but {rel} is absent from the tree"
                )
            if not installed and exists:
                errors.append(
                    f"{rel} is present in the tree but installed_packages does not declare {package_id!r}"
                )
    return errors


def reconcile_file_list(target: Path, files: Dict[str, Any]) -> List[str]:
    """Every path the manifest records as created/changed must exist in the
    installed tree -- a receipt must never list files the Cell lacks."""
    errors: List[str] = []
    for bucket in ("created", "changed"):
        for rel in (files or {}).get(bucket) or []:
            if not (target / rel).exists():
                errors.append(f"files.{bucket} lists {rel} but it is absent from the installed tree")
    return errors


def reconcile_personalization(target: Path, personalization: Optional[Dict[str, Any]], files: Dict[str, Any]) -> List[str]:
    """A receipt that declares required personalized outputs must not be written
    when one is absent from the tree or was never recorded as created (fail
    closed: no successful first-use completion without the outputs)."""
    errors: List[str] = []
    if not personalization or personalization.get("status") != "generated":
        return errors
    created = set((files or {}).get("created") or []) | set((files or {}).get("changed") or [])
    paths = list(personalization.get("required_outputs") or [])
    if personalization.get("manifest"):
        paths.append(personalization["manifest"])
    for rel in paths:
        if not (target / rel).is_file():
            errors.append(f"personalization declares required output {rel} but it is absent from the installed tree")
        elif rel not in created:
            errors.append(f"personalization output {rel} is not listed under files.created — the receipt must match the confirmed preview")
    return errors


def build_receipt(data: Dict[str, Any], installation_id: Optional[str]) -> Dict[str, Any]:
    receipt = {
        "schema_version": "0.1",
        "installation_id": installation_id or data.get("installation_id"),
        "installed_at": data.get("installed_at") or now_iso(),
        "installation_mode": data["installation_mode"],
        "source": data["source"],
        "target": data["target"],
        "governance": data["governance"],
        "installed_packages": data.get("installed_packages") or [],
        "files": data.get("files") or {"created": [], "changed": []},
        "rollback": data.get("rollback"),
        "preview_confirmed": data.get("preview_confirmed"),
    }
    if data.get("personalization") is not None:
        receipt["personalization"] = data["personalization"]
    return receipt


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore

        with path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, default_flow_style=False)
    except ImportError:
        path.write_text(_manual_yaml_dump(data), encoding="utf-8")


def _manual_yaml_dump(data: Any, indent: int = 0) -> str:
    pad = "  " * indent
    lines: List[str] = []
    if isinstance(data, dict):
        if not data:
            return "{}\n"
        for key, value in data.items():
            if isinstance(value, (dict, list)) and value:
                lines.append(f"{pad}{key}:")
                lines.append(_manual_yaml_dump(value, indent + 1).rstrip("\n"))
            else:
                lines.append(f"{pad}{key}: {_yaml_scalar(value)}")
    elif isinstance(data, list):
        if not data:
            return "[]\n"
        for item in data:
            if isinstance(item, dict):
                lines.append(f"{pad}-")
                lines.append(_manual_yaml_dump(item, indent + 1).rstrip("\n"))
            else:
                lines.append(f"{pad}- {_yaml_scalar(item)}")
    return "\n".join(lines) + "\n"


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        if value == "" or re.search(r"[:#\n]", value):
            return json.dumps(value)
        return value
    return str(value)


def find_repo_root(explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def registry_row(cell_id: str, receipt: Dict[str, Any], readiness_status: str, verification_report: str, notes: str) -> str:
    target = receipt["target"]
    hosted_repo = target.get("repository") or "local-only"
    installed_date = receipt["installed_at"][:10]
    source_task = "pending"
    hosted_head = receipt["source"].get("commit_sha") or "pending"
    install_status = "installed-via-teamcell-install-preview"
    cell_name = cell_id
    visibility = "private" if target.get("repository") else "local-only"
    return (
        f"| `{cell_id}` | {cell_name} | `{hosted_repo}` | {visibility} | {installed_date} | "
        f"`{source_task}` | `{hosted_head}` | `{install_status}` | `{readiness_status}` | "
        f"{verification_report} | {notes} |"
    )


def update_registry(registry_path: Path, cell_id: str, row: str) -> str:
    if not registry_path.exists():
        raise ReceiptError(f"Registry not found: {registry_path}")
    text = registry_path.read_text(encoding="utf-8")
    marker = f"| `{cell_id}` |"
    if marker in text:
        return "unchanged (row already present for this cell_id)"
    lines = text.splitlines()
    insert_at = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("|---") or re.match(r"^\|[-\s|]+\|$", line.strip()):
            insert_at = idx + 1
    if insert_at is None:
        raise ReceiptError(
            f"Could not find the registry table's header separator row in {registry_path}"
        )
    while insert_at < len(lines) and lines[insert_at].strip().startswith("|") and "---" not in lines[insert_at]:
        insert_at += 1
    lines.insert(insert_at, row)
    registry_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "appended"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("target", help="target Cell local path")
    p.add_argument(
        "--from-manifest",
        default=None,
        help="path to the install manifest (default: TARGET/.installation/INSTALL-PREVIEW-MANIFEST.json)",
    )
    p.add_argument("--field", action="append", default=[], help="DOTTED.PATH=VALUE override, may repeat")
    p.add_argument("--installation-id", default=None)
    p.add_argument("--cell-id", default=None, help="registry cell_id (default: target directory basename)")
    p.add_argument("--registry-path", default=None, help="registry path (default: <repo-root>/registries/BCOS-CELL-REGISTRY.md)")
    p.add_argument("--skip-registry", action="store_true", help="write the receipt only, do not touch the registry")
    p.add_argument("--readiness-status", default="installed-local-only")
    p.add_argument("--verification-report", default="pending")
    p.add_argument("--notes", default="Generated by scripts/generate-teamcell-installation-receipt.py.")
    p.add_argument("--repo-root", default=None, help="bcos repo root (default: this script's repo)")
    return p.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    target = Path(args.target).expanduser().resolve()
    repo_root = find_repo_root(args.repo_root)

    manifest_path = Path(args.from_manifest) if args.from_manifest else target / ".installation" / "INSTALL-PREVIEW-MANIFEST.json"

    try:
        data = load_manifest(manifest_path)
        data = apply_field_overrides(data, args.field)
        errors = validate_manifest(data)
        if errors:
            print("REFUSED — manifest fails schema validation. No receipt was written.", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

        tree_errors = reconcile_package_tree(target, data.get("installed_packages") or [])
        tree_errors += reconcile_file_list(target, data.get("files") or {})
        tree_errors += reconcile_personalization(target, data.get("personalization"), data.get("files") or {})
        if tree_errors:
            print(
                "REFUSED — installed_packages does not match the installed tree. "
                "No receipt was written.",
                file=sys.stderr,
            )
            for err in tree_errors:
                print(f"  - {err}", file=sys.stderr)
            return 1

        receipt = build_receipt(data, args.installation_id)
        receipt_path = target / ".installation" / "TEAMCELL-INSTALLATION-RECEIPT.yaml"
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        write_yaml(receipt_path, receipt)
        print(f"Receipt written: {receipt_path}")

        default_registry = repo_root / "control-plane" / "registries" / "BCOS-CELL-REGISTRY.md"
        if not args.skip_registry and not args.registry_path and not default_registry.exists():
            # A distribution checkout (e.g. the public Teamcell distribution)
            # has no operator registry -- the receipt alone is the record.
            print("Registry: skipped (no operator registry in this checkout; the receipt is the installation record)")
        elif not args.skip_registry:
            registry_path = Path(args.registry_path) if args.registry_path else default_registry
            cell_id = args.cell_id or target.name
            row = registry_row(cell_id, receipt, args.readiness_status, args.verification_report, args.notes)
            result = update_registry(registry_path, cell_id, row)
            print(f"Registry {registry_path}: {result}")
            print(
                "This script did not commit anything. Commit the receipt (in the target "
                "repo) and the registry change (in bcos) through the standard AGENTS.md "
                "Git Write Protocol before claiming completion."
            )
        return 0
    except ReceiptError as exc:
        print("REFUSED — no receipt was written.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
