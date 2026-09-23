#!/usr/bin/env python3
"""Mandatory preview-then-confirm gate for Teamcell Lite installation.

Implements the contract in
`docs/architecture/BCOS-TEAMCELL-INSTALL-SEMANTICS-V1-20260714.md`:

- resolves a target/instruction/flag combination to a candidate set of the
  three installation modes (`new_from_template`, `hydrate_existing_repo`,
  `clone_existing_cell`);
- refuses entirely (preview only, exit non-zero, `--confirm` never honored)
  when more than one mode is plausible and the caller has not disambiguated;
- otherwise renders the full mandatory preview (source, commit SHA, target,
  mode, governance profile, owners, packages, files, rollback) and refuses
  to mutate anything without an explicit, distinct `--confirm` flag;
- on a confirmed, unambiguous install, runs the preflight
  (`scripts/teamcell-install-preflight.sh`), performs the mutation for the
  resolved mode, and writes an install manifest that
  `scripts/generate-teamcell-installation-receipt.py` consumes to produce
  the durable receipt.

This script never writes into the template or any other existing Cell — it
only reads from declared source repositories and writes into the
caller-specified TARGET directory.

Distribution mode: when this script runs from a checkout that carries
`distribution/teamcell-lite/SOURCE-MANIFEST.json` (the public Teamcell
distribution), the default source is that checkout itself — its `origin`
identity (or local path) at its local HEAD, with the manifest's
`version_label`. The vendored kit's content hash is compared with the
manifest; a mismatch is shown in the preview and recorded as
`<version_label>+local-modifications`. No private repository, GitHub CLI
login or network access is needed for a `new_from_template` install.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Never leave compiled bytecode (__pycache__/) in the distribution checkout
# this script runs from: a public clone must stay clean after an install.
sys.dont_write_bytecode = True

# Canonical repository/Cell/provenance resolution (BRIEF-20260717-004),
# shared with scripts/personalize-team-cell.sh. Loaded by path because the
# filename is not a valid Python module identifier.
_resolver_spec = importlib.util.spec_from_file_location(
    "resolve_cell_identity", Path(__file__).resolve().parent / "resolve-cell-identity.py"
)
resolve_cell_identity = importlib.util.module_from_spec(_resolver_spec)
sys.modules["resolve_cell_identity"] = resolve_cell_identity  # required before exec_module: py3.9
# dataclasses._is_type() looks the module up via sys.modules[cls.__module__].
assert _resolver_spec.loader is not None
_resolver_spec.loader.exec_module(resolve_cell_identity)

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
DEFAULT_TEMPLATE_REPO = "dbeebr/bcos-teamcell-lite-template"
# scripts/bootstrap-team-cell.sh's "stable" variant kit (distribution/bootstrap-kit/ at the
# bcos repo root) is authored natively in dbeebr/bcos itself — it is not
# vendored from bcos-teamcell-lite-template (that template only backs the
# "teamcell-lite" variant, via the local distribution/teamcell-lite/bootstrap-kit/
# mirror). Defaulting "stable" installs to the template repo would record a
# false provenance in the receipt, so the two variants default to different
# source repositories.
DEFAULT_STABLE_SOURCE_REPO = "dbeebr/bcos"


def default_source_repo(variant: str) -> str:
    return DEFAULT_TEMPLATE_REPO if variant == "teamcell-lite" else DEFAULT_STABLE_SOURCE_REPO
MANIFEST_RELATIVE_PATH = Path(".installation") / "INSTALL-PREVIEW-MANIFEST.json"
# Distinct from reports/verification/FIRST-RUN-INSTALL-HANDOFF.md, which is
# a separate, pre-existing agent-authored first-real-usage proof contract
# (see personalize-team-cell.sh's FIRST_RUN_PROOF_PATH and templates/
# FIRST-RUN-AGENT-PROMPT.template.md) -- this installer-generated closeout
# proof runs mechanically at confirm time, before any agent session, and
# must never be mistaken for that later, richer proof.
CLOSEOUT_PROOF_RELATIVE_PATH = Path(".installation") / "INSTALL-CLOSEOUT-PROOF.md"
PACKAGES_MANIFEST_RELATIVE_PATH = Path("packages") / "PACKAGES.yaml"
SOURCE_MANIFEST_RELATIVE_PATH = Path("distribution") / "teamcell-lite" / "SOURCE-MANIFEST.json"


# --------------------------------------------------------------------------
# Distribution mode (public Teamcell distribution checkout)
# --------------------------------------------------------------------------


def load_source_manifest(repo_root: Path) -> Optional[Dict[str, Any]]:
    path = repo_root / SOURCE_MANIFEST_RELATIVE_PATH
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def kit_tree_sha256(kit_root: Path) -> str:
    """Order-independent content hash of the vendored kit: sha256 over sorted
    `<relative-path>\0<sha256-of-file>\n` lines. Must match the algorithm
    recorded in SOURCE-MANIFEST.json (`kit.tree_sha256_algorithm`)."""
    digest = hashlib.sha256()
    for rel in list_files(kit_root):
        file_hash = hashlib.sha256((kit_root / rel).read_bytes()).hexdigest()
        digest.update(f"{Path(rel).as_posix()}\0{file_hash}\n".encode("utf-8"))
    return digest.hexdigest()


def normalize_github_remote(url: str) -> Optional[str]:
    match = re.match(r"^(?:git@github\.com:|ssh://git@github\.com/|https?://github\.com/)([^/]+/[^/]+?)(?:\.git)?/?$", url.strip())
    return match.group(1) if match else None


def distribution_source_identity(repo_root: Path) -> str:
    remote = run(["git", "-C", str(repo_root), "remote", "get-url", "origin"])
    if remote.returncode == 0 and remote.stdout.strip():
        return normalize_github_remote(remote.stdout) or remote.stdout.strip()
    return str(repo_root)


def require_pyyaml() -> Optional[str]:
    try:
        import yaml  # noqa: F401
    except ImportError:
        return (
            "Python package PyYAML is required to read packages/PACKAGES.yaml and "
            "TEAM-PROFILE.md frontmatter, but it is not installed for "
            f"{sys.executable}.\n"
            "Repair: python3 -m pip install --user pyyaml   (or install your "
            "platform's python3-yaml package), then re-run this exact command."
        )
    return None


# --------------------------------------------------------------------------
# Package manifest (packages/PACKAGES.yaml) — kernel/schemas/teamcell-package-
# manifest.schema.md. Selective installation for the teamcell-lite variant
# (TASK-20260717-007, FAIL-PATTERN-20260717-015).
# --------------------------------------------------------------------------


def load_package_manifest(kit_root: Path) -> List[Dict[str, Any]]:
    manifest_path = kit_root / PACKAGES_MANIFEST_RELATIVE_PATH
    if not manifest_path.exists():
        return []
    import yaml  # already a soft dependency of this script

    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    return data.get("packages") or []


def find_package(packages: List[Dict[str, Any]], package_id: str) -> Optional[Dict[str, Any]]:
    for pkg in packages:
        if pkg.get("package_id") == package_id:
            return pkg
    return None


def resolve_selected_optional_packages(
    packages: List[Dict[str, Any]], requested: List[str]
) -> List[str]:
    """Validates requested optional package_ids against the manifest and
    auto-includes their depends_on (never refuses on a missing dependency —
    kernel/schemas/teamcell-package-manifest.schema.md rule #2)."""
    optional_ids = {p["package_id"] for p in packages if p.get("optional")}
    selected: List[str] = []

    def add(pid: str) -> None:
        if pid in selected:
            return
        pkg = find_package(packages, pid)
        if pkg is None:
            raise InstallRefused(
                f"--optional-package names an unknown package: {pid!r}\n"
                f"Known optional packages: {', '.join(sorted(optional_ids)) or '(none for this variant)'}"
            )
        for dep in pkg.get("depends_on") or []:
            add(dep)
        selected.append(pid)

    for pid in requested:
        if pid not in optional_ids:
            raise InstallRefused(
                f"--optional-package names an unknown or non-optional package: {pid!r}\n"
                f"Known optional packages: {', '.join(sorted(optional_ids)) or '(none for this variant)'}"
            )
        add(pid)
    return selected


def installer_declared_targets(installer: Path) -> List[str]:
    """A package with its own installer script is the source of truth for
    the files it creates: `<installer> --print-targets` lists them without
    writing anything. The preview shows exactly that list, so it never
    promises a file the installer does not write (or hides one it does)."""
    if not installer.exists():
        raise InstallRefused(f"package installer not found: {installer}")
    result = subprocess.run(["sh", str(installer), "--print-targets"], capture_output=True, text=True)
    if result.returncode != 0:
        raise InstallRefused(
            f"{installer} --print-targets failed (exit {result.returncode}): {result.stderr.strip()}\n"
            "Repair: the package installer must support --print-targets."
        )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def package_target_mapping(kit_root: Path, pkg: Dict[str, Any]) -> Dict[str, Path]:
    """Returns {target-relative-path: absolute-source-path} for every file
    this package owns, honoring exclude_source_roots and (if present) the
    dedicated onboarding_source remap — kernel/schemas/teamcell-package-manifest.
    schema.md."""
    source_root = kit_root / pkg["source_root"]
    if not source_root.exists():
        return {}
    excludes = [kit_root / ex for ex in (pkg.get("exclude_source_roots") or [])]
    onboarding_source = pkg.get("onboarding_source")
    onboarding_source_abs = kit_root / onboarding_source if onboarding_source else None
    target_root = pkg["target_root"]
    mapping: Dict[str, Path] = {}
    for rel in list_files(source_root):
        abs_path = source_root / rel
        if any(_is_under(abs_path, ex) for ex in excludes):
            continue
        if onboarding_source_abs is not None and abs_path == onboarding_source_abs:
            continue
        target_rel = rel if target_root == "." else str(Path(target_root) / rel)
        mapping[target_rel] = abs_path
    if onboarding_source_abs is not None and onboarding_source_abs.exists():
        onboarding_entries = pkg.get("onboarding_entries") or []
        if onboarding_entries:
            mapping[onboarding_entries[0]] = onboarding_source_abs
    return mapping


def resolve_package_plan(
    kit_root: Path, packages: List[Dict[str, Any]], selected_optional_ids: List[str]
) -> Dict[str, Dict[str, Path]]:
    """Returns {package_id: {target-relative-path: absolute-source-path}}
    for the baseline plus every selected optional package."""
    plan: Dict[str, Dict[str, Path]] = {}
    for pkg in packages:
        if pkg.get("optional") and pkg["package_id"] not in selected_optional_ids:
            continue
        plan[pkg["package_id"]] = package_target_mapping(kit_root, pkg)
    return plan

# Exit codes are part of the contract this script implements — callers
# (agents, the NL-routing-guard skill, tests) depend on the distinction.
EXIT_INSTALLED = 0
EXIT_PREVIEW_ONLY_NOT_CONFIRMED = 2
EXIT_AMBIGUOUS_REFUSED = 3
EXIT_REFUSED_NO_CANDIDATE = 4
EXIT_PREFLIGHT_FAILED = 5
EXIT_MUTATION_FAILED = 6
EXIT_CLOSEOUT_FAILED = 7
EXIT_USAGE_ERROR = 64


class InstallRefused(RuntimeError):
    """Raised for any '0 candidates' / precondition-failed refusal."""


class InstallAmbiguous(RuntimeError):
    """Raised when more than one mode is plausible and undisambiguated."""

    def __init__(self, candidates: List[str], reason: str) -> None:
        super().__init__(reason)
        self.candidates = candidates
        self.reason = reason


class MutationFailed(RuntimeError):
    """Raised when a confirmed mutation step fails partway through."""


# --------------------------------------------------------------------------
# Target state
# --------------------------------------------------------------------------


@dataclass
class TargetState:
    path: Path
    exists: bool
    is_populated: bool  # has any tracked/untracked content beyond a bare .git
    is_already_cell: bool
    existing_files: List[str] = field(default_factory=list)
    already_cell_markers: List[str] = field(default_factory=list)

    @property
    def allows_new_from_template(self) -> bool:
        return not self.is_populated


def list_files(root: Path) -> List[str]:
    if not root.exists():
        return []
    out: List[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel_parts = p.relative_to(root).parts
        if rel_parts and rel_parts[0] == ".git":
            continue
        out.append(str(p.relative_to(root)))
    return sorted(out)


CELL_MARKERS = (
    "TEAM-PROFILE.md",
    ".bcos/CELL-GOVERNANCE.yaml",
    ".installation/TEAMCELL-INSTALLATION-RECEIPT.yaml",
)


def compute_target_state(target: Path) -> TargetState:
    exists = target.exists()
    if exists and not target.is_dir():
        raise InstallRefused(
            f"Target path exists and is not a directory: {target}\n"
            "Repair: remove or rename the file, or choose a different target path."
        )
    if not exists:
        return TargetState(path=target, exists=False, is_populated=False, is_already_cell=False)

    entries = list(target.iterdir())
    non_git_entries = [e for e in entries if e.name != ".git"]
    is_populated = len(non_git_entries) > 0
    existing_files = list_files(target)
    markers = [m for m in CELL_MARKERS if (target / m).exists()]
    return TargetState(
        path=target,
        exists=True,
        is_populated=is_populated,
        is_already_cell=bool(markers),
        existing_files=existing_files,
        already_cell_markers=markers,
    )


# --------------------------------------------------------------------------
# Mode candidate resolution
# --------------------------------------------------------------------------


@dataclass
class CandidateResolution:
    candidates: List[str]
    disambiguated: bool
    reason: str


def resolve_candidates(
    explicit_mode: Optional[str],
    clone_source: Optional[str],
    instruction: Optional[str],
    target_state: TargetState,
) -> CandidateResolution:
    if explicit_mode:
        if explicit_mode == "new_from_template" and not target_state.allows_new_from_template:
            # Defect #1 (TASK-20260714-030): an explicit --mode must not
            # bypass new_from_template's own hard target-emptiness
            # precondition -- only the redundant confirm-time check in
            # bootstrap-team-cell.sh caught this before, meaning an
            # explicit-mode preview could render and (if --confirm was
            # supplied) attempt an unsafe install into a populated target.
            return CandidateResolution(
                [],
                False,
                "explicit --mode new_from_template requires an empty target (or bare "
                f".git only); target is populated and unsafe for a fresh-template "
                f"install: {target_state.path}",
            )
        return CandidateResolution([explicit_mode], True, "explicit --mode flag")

    if clone_source:
        # Decision criteria table: an explicit, concrete clone source is the
        # defining signal for clone_existing_cell regardless of target state
        # (target precondition for this mode is "either — source dictates").
        return CandidateResolution(
            ["clone_existing_cell"], True, "explicit --clone-source given"
        )

    instr = (instruction or "").lower()
    mentions_clone = bool(re.search(r"\bclon(e|ed|ing)\b", instr))
    mentions_hydrate = bool(
        re.search(r"\bhydrat(e|ed|ing)\b", instr)
        or re.search(r"\badd\b[^.]*\bexisting\b", instr)
        or re.search(r"\bwithout disturbing\b", instr)
    )

    candidates: List[str] = []
    if target_state.allows_new_from_template:
        candidates.append("new_from_template")
        if mentions_clone:
            # Contract's own worked example: empty target + a "clone"
            # mention with no concrete source is genuinely ambiguous
            # between a fresh template install and cloning a specific
            # (unnamed) existing Cell.
            candidates.append("clone_existing_cell")
    else:
        # Non-empty target rules out new_from_template but is consistent
        # with either of the other two — never narrowed to one by
        # elimination alone.
        candidates.append("hydrate_existing_repo")
        candidates.append("clone_existing_cell")

    if mentions_hydrate and "hydrate_existing_repo" in candidates and len(candidates) > 1:
        return CandidateResolution(
            ["hydrate_existing_repo"],
            True,
            "instruction explicitly names hydrate_existing_repo semantics",
        )

    if not candidates:
        return CandidateResolution([], False, "no candidate mode survives target-state preconditions")

    reason = (
        "narrowed to a single default candidate from target state"
        if len(candidates) == 1
        else "multiple modes remain plausible from target state and/or instruction"
    )
    return CandidateResolution(candidates, len(candidates) == 1, reason)


# --------------------------------------------------------------------------
# Source resolution (commit SHA / version label)
# --------------------------------------------------------------------------


def run(cmd: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def is_local_path(value: str) -> bool:
    return Path(value).expanduser().exists()


def resolve_remote_commit_sha(repo: str, ref: Optional[str]) -> Tuple[Optional[str], str]:
    """Returns (sha_or_None, diagnostic). Uses gh api; never guesses."""
    if ref is None:
        view = run(["gh", "repo", "view", repo, "--json", "defaultBranchRef"])
        if view.returncode != 0:
            return None, f"gh repo view {repo} failed: {view.stderr.strip()}"
        try:
            ref = json.loads(view.stdout)["defaultBranchRef"]["name"]
        except Exception:  # noqa: BLE001 - defensive, reported as diagnostic text
            return None, f"could not determine default branch for {repo}"
    api = run(["gh", "api", f"repos/{repo}/commits/{ref}", "--jq", ".sha"])
    if api.returncode != 0:
        return None, f"gh api repos/{repo}/commits/{ref} failed: {api.stderr.strip()}"
    sha = api.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return None, f"gh api returned a non-SHA value for {repo}@{ref}: {sha!r}"
    return sha, "resolved via gh api"


def resolve_local_commit_sha(path: Path, ref: Optional[str]) -> Tuple[Optional[str], str]:
    target_ref = ref or "HEAD"
    result = run(["git", "-C", str(path), "rev-parse", target_ref])
    if result.returncode != 0:
        return None, f"git rev-parse {target_ref} in {path} failed: {result.stderr.strip()}"
    sha = result.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return None, f"git rev-parse returned a non-SHA value: {sha!r}"
    return sha, "resolved via local git rev-parse"


def resolve_version_label(repo: str) -> str:
    result = run(["gh", "api", f"repos/{repo}/releases/latest", "--jq", ".tag_name"])
    if result.returncode == 0:
        label = result.stdout.strip()
        if label and label != "null":
            return label
    return "unversioned"


# --------------------------------------------------------------------------
# Governance / ownership block construction
# --------------------------------------------------------------------------


def parse_owner_role_flags(values: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise InstallRefused(
                f"--owner-role expects CLASS=ROLE, got: {item!r}\n"
                f"Valid classes: {', '.join(DECISION_CLASSES)}"
            )
        cls, role = item.split("=", 1)
        cls = cls.strip()
        role = role.strip()
        if cls not in DECISION_CLASSES:
            raise InstallRefused(
                f"--owner-role names an unknown decision class: {cls!r}\n"
                f"Valid classes: {', '.join(DECISION_CLASSES)}"
            )
        out[cls] = role
    return out


def parse_bind_role_flags(values: List[str]) -> Dict[str, Dict[str, Optional[str]]]:
    out: Dict[str, Dict[str, Optional[str]]] = {}
    for item in values:
        if "=" not in item:
            raise InstallRefused(f"--bind-role expects ROLE=HUMAN_ID[:DISPLAY_NAME], got: {item!r}")
        role, rest = item.split("=", 1)
        role = role.strip()
        # HUMAN_ID is always itself "human:<id>" or "agent:<id>" (every schema
        # in this repo mandates that shape) — it always contains exactly one
        # colon. A naive split on the *first* colon of `rest` therefore cuts
        # HUMAN_ID's own prefix off instead of separating it from
        # DISPLAY_NAME (found live during TASK-20260714-007's proof testing:
        # --bind-role lead=human:jordan-rivera:"Jordan Rivera" parsed to
        # human_id="human", display_name="jordan-rivera:Jordan Rivera").
        # rsplit with maxsplit=1 splits off DISPLAY_NAME from the *last*
        # colon instead, which is correct as long as DISPLAY_NAME itself
        # never contains a colon (true for every display_name example in
        # kernel/schemas/teamcell-cell-ownership.schema.md).
        if rest.count(":") >= 2:
            human_id, display_name = rest.rsplit(":", 1)
        else:
            human_id, display_name = rest, None
        out[role] = {"human_id": human_id.strip() or None, "display_name": (display_name or None)}
    return out


def build_governance_block(args: argparse.Namespace) -> Dict[str, Any]:
    owner_roles = parse_owner_role_flags(args.owner_role)
    bindings_in = parse_bind_role_flags(args.bind_role)

    cell_owner_role = args.cell_owner_role
    decision_owner_roles = {cls: owner_roles.get(cls, "unresolved") for cls in DECISION_CLASSES}

    referenced_roles = set()
    if cell_owner_role:
        referenced_roles.add(cell_owner_role)
    referenced_roles.update(v for v in decision_owner_roles.values() if v != "unresolved")

    role_bindings: Dict[str, Any] = {}
    for role in sorted(referenced_roles):
        binding = bindings_in.get(role, {"human_id": None, "display_name": None})
        role_bindings[role] = {
            "human_id": binding.get("human_id"),
            "display_name": binding.get("display_name"),
            "bound_at": args.governance_selected_by and binding.get("human_id") and today() or None,
            "bound_by": args.governance_selected_by if binding.get("human_id") else None,
        }
    for role, binding in bindings_in.items():
        if role not in role_bindings:
            role_bindings[role] = {
                "human_id": binding.get("human_id"),
                "display_name": binding.get("display_name"),
                "bound_at": today() if binding.get("human_id") else None,
                "bound_by": args.governance_selected_by if binding.get("human_id") else None,
            }

    governance_profile = args.governance_profile
    legacy_unresolved = governance_profile is None

    if governance_profile and not args.governance_selected_by:
        raise InstallRefused(
            "--governance-profile was supplied without --governance-selected-by.\n"
            "Repair: pass --governance-selected-by human:<id> or agent:<id> naming who "
            "explicitly selected this profile for this install."
        )

    return {
        "governance_profile": governance_profile,
        "legacy_unresolved": legacy_unresolved,
        "cell_owner_role": cell_owner_role,
        "decision_owner_roles": decision_owner_roles,
        "role_bindings": role_bindings,
        "selected_at": today() if governance_profile else None,
        "selected_by": args.governance_selected_by if governance_profile else None,
    }


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# Preview context and rendering
# --------------------------------------------------------------------------


@dataclass
class PreviewContext:
    args: argparse.Namespace
    repo_root: Path
    target: Path
    target_state: TargetState
    mode: str
    source_repo: str
    source_commit_sha: Optional[str]
    source_commit_diagnostic: str
    version_label: str
    clone_source_sha: Optional[str] = None
    clone_source_diagnostic: Optional[str] = None
    governance: Dict[str, Any] = field(default_factory=dict)
    installed_packages: List[Dict[str, Any]] = field(default_factory=list)
    package_plan: Dict[str, Dict[str, Path]] = field(default_factory=dict)
    package_installers: Dict[str, Optional[Path]] = field(default_factory=dict)
    files_created_preview: List[str] = field(default_factory=list)
    files_changed_preview: List[str] = field(default_factory=list)
    files_collision_preview: List[str] = field(default_factory=list)
    rollback_preview: Dict[str, Any] = field(default_factory=dict)
    distribution: Optional[Dict[str, Any]] = None


def resolve_kit_root(repo_root: Path, variant: str) -> Path:
    if variant == "teamcell-lite":
        return repo_root / "distribution" / "teamcell-lite" / "bootstrap-kit"
    return repo_root / "distribution" / "bootstrap-kit"


def compute_hydrate_preview(kit_root: Path, target_state: TargetState, include_existing: List[str]) -> Tuple[List[str], List[str], List[str]]:
    if not kit_root.exists():
        raise InstallRefused(f"Template kit not found: {kit_root}")
    created, changed, collisions = [], [], []
    existing = set(target_state.existing_files)
    for rel in list_files(kit_root):
        if rel in existing:
            if rel in include_existing:
                changed.append(rel)
            else:
                collisions.append(rel)
        else:
            created.append(rel)
    return sorted(created), sorted(changed), sorted(collisions)


def refuse_unvalidated_distribution_mode(repo_root: Path, mode: str, variant: str) -> None:
    """A public distribution checkout (it carries SOURCE-MANIFEST.json) offers
    only the install modes its manifest lists as validated, and refuses the
    others before any preview or mutation. The private operator path (no
    manifest) is unchanged."""
    if variant != "teamcell-lite":
        return
    manifest = load_source_manifest(repo_root)
    if manifest is None:
        return
    validated = manifest.get("validated_install_modes") or []
    if mode in validated:
        return
    reasons = {
        "hydrate_existing_repo": "it has a known defect in this release (its post-install closeout "
                                 "fails after files were written), so it is not offered here",
        "clone_existing_cell": "cloning an existing Cell is not validated in this release",
    }
    raise InstallRefused(
        f"Mode {mode} is not offered by this public Teamcell distribution "
        f"({manifest.get('version_label') or 'unversioned'}): {reasons.get(mode, 'it is not validated in this release')}.\n"
        f"Validated modes here: {', '.join(validated) or 'none'}.\n"
        "Repair: install a new Cell into an empty or absent directory with "
        "--mode new_from_template. Nothing was previewed or written."
    )


def build_context(args: argparse.Namespace, repo_root: Path) -> PreviewContext:
    target = Path(args.target).expanduser().resolve()
    target_state = compute_target_state(target)

    resolution = resolve_candidates(args.mode, args.clone_source, args.instruction, target_state)
    if not resolution.candidates:
        raise InstallRefused(
            "No installation mode's preconditions are satisfied by the given target/source.\n"
            f"Target: {target}\n"
            f"Target state: {'populated' if target_state.is_populated else 'empty-or-absent'}\n"
            f"Reason: {resolution.reason}\n"
            "Repair: pass --mode {new_from_template|hydrate_existing_repo|clone_existing_cell} "
            "explicitly with a target that satisfies that mode's own precondition, or "
            "--clone-source <owner/repo|path> to name a concrete Cell to clone."
        )
    if len(resolution.candidates) > 1:
        raise InstallAmbiguous(resolution.candidates, resolution.reason)

    mode = resolution.candidates[0]
    refuse_unvalidated_distribution_mode(repo_root, mode, args.variant)

    distribution_info: Optional[Dict[str, Any]] = None
    if mode == "clone_existing_cell":
        source_repo = args.clone_source
        if args.source_commit_sha:
            sha, diag = args.source_commit_sha, "explicit --source-commit-sha override"
        elif is_local_path(source_repo):
            sha, diag = resolve_local_commit_sha(Path(source_repo).expanduser().resolve(), args.clone_ref)
        else:
            sha, diag = resolve_remote_commit_sha(source_repo, args.clone_ref)
        version_label = "unversioned" if is_local_path(source_repo) else resolve_version_label(source_repo)
    else:
        source_manifest = load_source_manifest(repo_root) if args.variant == "teamcell-lite" else None
        if source_manifest is not None and not args.source_repo:
            kit_root_for_hash = resolve_kit_root(repo_root, args.variant)
            if not kit_root_for_hash.exists():
                raise InstallRefused(f"Template kit not found: {kit_root_for_hash}")
            expected_hash = (source_manifest.get("kit") or {}).get("tree_sha256")
            actual_hash = kit_tree_sha256(kit_root_for_hash)
            base_label = source_manifest.get("version_label") or "unversioned"
            distribution_info = {
                "manifest": str(SOURCE_MANIFEST_RELATIVE_PATH),
                "expected_kit_tree_sha256": expected_hash,
                "actual_kit_tree_sha256": actual_hash,
                "kit_integrity": "verified" if expected_hash == actual_hash else "MODIFIED",
            }
            source_repo = distribution_source_identity(repo_root)
            if args.source_commit_sha:
                sha, diag = args.source_commit_sha, "explicit --source-commit-sha override"
            else:
                sha, diag = resolve_local_commit_sha(repo_root, args.source_ref)
                diag = f"{diag} (distribution checkout {repo_root})"
            version_label = base_label if expected_hash == actual_hash else f"{base_label}+local-modifications"
        else:
            source_repo = args.source_repo or default_source_repo(args.variant)
    if mode != "clone_existing_cell" and distribution_info is None:
        if args.source_commit_sha:
            sha, diag = args.source_commit_sha, "explicit --source-commit-sha override"
        elif source_repo == DEFAULT_STABLE_SOURCE_REPO and not args.source_repo:
            # The "stable" kit lives natively in this checkout — resolve its
            # provenance from repo_root's own HEAD rather than a remote call.
            sha, diag = resolve_local_commit_sha(repo_root, args.source_ref)
        elif is_local_path(source_repo):
            sha, diag = resolve_local_commit_sha(Path(source_repo).expanduser().resolve(), args.source_ref)
        else:
            sha, diag = resolve_remote_commit_sha(source_repo, args.source_ref)
        version_label = (
            "unversioned"
            if (is_local_path(source_repo) or source_repo == DEFAULT_STABLE_SOURCE_REPO)
            else resolve_version_label(source_repo)
        )

    governance = build_governance_block(args)

    installed_packages = [
        {
            "package_id": "teamcell-lite-baseline" if args.variant == "teamcell-lite" else "teamcell-stable-baseline",
            "source_repository": source_repo,
            "source_commit_sha": sha or "UNRESOLVED",
            "version_label": version_label,
        }
    ]
    for pkg in args.package:
        if "=" not in pkg or "@" not in pkg:
            raise InstallRefused(f"--package expects PACKAGE_ID=REPO@REF, got: {pkg!r}")
        pkg_id, rest = pkg.split("=", 1)
        pkg_repo, pkg_ref = rest.split("@", 1)
        pkg_sha, _ = (
            resolve_local_commit_sha(Path(pkg_repo).expanduser().resolve(), pkg_ref)
            if is_local_path(pkg_repo)
            else resolve_remote_commit_sha(pkg_repo, pkg_ref)
        )
        installed_packages.append(
            {
                "package_id": pkg_id,
                "source_repository": pkg_repo,
                "source_commit_sha": pkg_sha or "UNRESOLVED",
                "version_label": pkg_ref,
            }
        )

    ctx = PreviewContext(
        args=args,
        repo_root=repo_root,
        target=target,
        target_state=target_state,
        mode=mode,
        source_repo=source_repo,
        source_commit_sha=sha,
        source_commit_diagnostic=diag,
        version_label=version_label,
        governance=governance,
        installed_packages=installed_packages,
        distribution=distribution_info,
    )

    if mode == "new_from_template":
        kit_root = resolve_kit_root(repo_root, args.variant)
        if not kit_root.exists():
            raise InstallRefused(
                f"Template kit not found: {kit_root}\n"
                f"The '{args.variant}' variant is not shipped in this checkout. "
                "Repair: use --variant teamcell-lite (the default), or run from a "
                "checkout that contains this variant's kit."
            )
        packages = load_package_manifest(kit_root)
        selected_optional_ids = resolve_selected_optional_packages(packages, args.optional_package)
        if packages:
            package_plan = resolve_package_plan(kit_root, packages, selected_optional_ids)
            ctx.package_plan = package_plan
            ctx.package_installers = {
                pkg_id: (kit_root / find_package(packages, pkg_id)["installer"])
                if find_package(packages, pkg_id).get("installer")
                else None
                for pkg_id in package_plan
            }
            ctx.files_created_preview = sorted(
                {
                    rel
                    for pkg_id, mapping in package_plan.items()
                    for rel in (
                        installer_declared_targets(ctx.package_installers[pkg_id])
                        if ctx.package_installers.get(pkg_id) is not None
                        else mapping
                    )
                }
            )
            for pkg_id in selected_optional_ids:
                installed_packages.append(
                    {
                        "package_id": pkg_id,
                        "source_repository": source_repo,
                        "source_commit_sha": sha or "UNRESOLVED",
                        "version_label": version_label if distribution_info else "bundled-with-teamcell-lite-baseline",
                    }
                )
        else:
            ctx.files_created_preview = [] if not kit_root.exists() else list_files(kit_root)
        ctx.files_created_preview.append(".bcos/CELL-GOVERNANCE.yaml")
        ctx.rollback_preview = {
            "method": "manual",
            "ref": None,
            "notes": f"New target with no prior Git history — roll back by deleting the directory: rm -rf {target}",
        }
    elif mode == "hydrate_existing_repo":
        kit_root = resolve_kit_root(repo_root, args.variant)
        created, changed, collisions = compute_hydrate_preview(kit_root, target_state, args.include_existing)
        if ".bcos/CELL-GOVERNANCE.yaml" not in target_state.existing_files:
            created.append(".bcos/CELL-GOVERNANCE.yaml")
        ctx.files_created_preview = created
        ctx.files_changed_preview = changed
        ctx.files_collision_preview = collisions
        pre_head, _ = resolve_local_commit_sha(target, "HEAD") if (target / ".git").exists() else (None, "no local .git")
        ctx.rollback_preview = (
            {"method": "git_reset_to_ref", "ref": pre_head, "notes": "Reset the target to its pre-install HEAD."}
            if pre_head
            else {
                "method": "manual",
                "ref": None,
                "notes": "Target has no Git history yet — manually delete the newly created files listed above to roll back.",
            }
        )
    else:  # clone_existing_cell
        clone_paths = args.clone_paths or ["(full source tree)"]
        ctx.files_created_preview = clone_paths
        ctx.clone_source_sha = sha
        ctx.clone_source_diagnostic = diag
        pre_head, _ = resolve_local_commit_sha(target, "HEAD") if (target / ".git").exists() else (None, "no local .git")
        ctx.rollback_preview = (
            {"method": "git_reset_to_ref", "ref": pre_head, "notes": "Reset the target to its pre-install HEAD."}
            if pre_head
            else {
                "method": "manual",
                "ref": None,
                "notes": f"New target with no prior Git history — roll back by deleting the directory: rm -rf {target}",
            }
        )

    return ctx


def render_governance_lines(governance: Dict[str, Any]) -> List[str]:
    lines = []
    profile = governance["governance_profile"]
    if profile is None:
        lines.append("  governance_profile: null (legacy_unresolved: true — required and not yet supplied)")
        lines.append("    -> pass --governance-profile {quick_build|operating_team|compliance_safety} "
                      "and --governance-selected-by to set it explicitly.")
    else:
        lines.append(f"  governance_profile: {profile} (selected_by: {governance['selected_by']}, "
                      f"selected_at: {governance['selected_at']})")
    owner_role = governance["cell_owner_role"] or "null (unresolved)"
    lines.append(f"  cell_owner_role: {owner_role}")
    lines.append("  decision_owner_roles:")
    for cls in DECISION_CLASSES:
        lines.append(f"    {cls}: {governance['decision_owner_roles'][cls]}")
    if governance["role_bindings"]:
        lines.append("  role_bindings:")
        for role, binding in governance["role_bindings"].items():
            human = binding["human_id"] or "null (role named, unbound)"
            lines.append(f"    {role}: human_id={human} display_name={binding['display_name']}")
    else:
        lines.append("  role_bindings: {} (no roles referenced)")
    return lines


def render_preview_text(ctx: PreviewContext) -> str:
    lines: List[str] = []
    lines.append("=" * 78)
    lines.append("TEAMCELL INSTALLATION PREVIEW — no files have been written yet")
    lines.append("=" * 78)
    lines.append(f"installation_mode: {ctx.mode}")
    lines.append("")
    lines.append("source:")
    lines.append(f"  repository: {ctx.source_repo}")
    lines.append(f"  commit_sha: {ctx.source_commit_sha or 'UNRESOLVED (' + ctx.source_commit_diagnostic + ')'}")
    lines.append(f"  version_label: {ctx.version_label}")
    if ctx.distribution:
        lines.append(f"  distribution_manifest: {ctx.distribution['manifest']}")
        lines.append(f"  kit_integrity: {ctx.distribution['kit_integrity']} "
                     f"(kit tree sha256 {ctx.distribution['actual_kit_tree_sha256']}"
                     + ("" if ctx.distribution['kit_integrity'] == "verified"
                        else f", manifest expects {ctx.distribution['expected_kit_tree_sha256']}")
                     + ")")
    if ctx.mode == "clone_existing_cell":
        lines.append("  clone_source:")
        lines.append(f"    repository: {ctx.args.clone_source}")
        lines.append(f"    commit_sha: {ctx.clone_source_sha or 'UNRESOLVED (' + str(ctx.clone_source_diagnostic) + ')'}")
        lines.append("    installation_receipt_ref: (resolved at receipt-generation time if the source Cell has one)")
    lines.append("")
    lines.append("target:")
    lines.append(f"  repository: {ctx.args.target_repo or 'null (local-only for now)'}")
    lines.append(f"  path: {ctx.target}")
    lines.append(f"  state: {'already a Cell (' + ', '.join(ctx.target_state.already_cell_markers) + ')' if ctx.target_state.is_already_cell else ('populated' if ctx.target_state.is_populated else 'empty-or-absent')}")
    lines.append("")
    lines.append("governance:")
    lines.extend(render_governance_lines(ctx.governance))
    lines.append("")
    lines.append("installed_packages:")
    for pkg in ctx.installed_packages:
        lines.append(f"  - {pkg['package_id']}: {pkg['source_repository']}@{pkg['source_commit_sha']} ({pkg['version_label']})")
    lines.append("")
    lines.append("files:")
    lines.append(f"  created ({len(ctx.files_created_preview)}):")
    for p in ctx.files_created_preview[:40]:
        lines.append(f"    + {p}")
    if len(ctx.files_created_preview) > 40:
        lines.append(f"    ... and {len(ctx.files_created_preview) - 40} more")
    if ctx.files_changed_preview:
        lines.append(f"  changed ({len(ctx.files_changed_preview)}):")
        for p in ctx.files_changed_preview:
            lines.append(f"    ~ {p}")
    if ctx.files_collision_preview:
        lines.append(f"  SKIPPED — collides with an existing target file, left untouched ({len(ctx.files_collision_preview)}):")
        for p in ctx.files_collision_preview:
            lines.append(f"    ! {p}  (pass --include-existing {p} to explicitly overwrite this one file)")
    lines.append("")
    lines.append("rollback:")
    lines.append(f"  method: {ctx.rollback_preview['method']}")
    lines.append(f"  ref: {ctx.rollback_preview['ref']}")
    lines.append(f"  notes: {ctx.rollback_preview['notes']}")
    lines.append("")
    lines.append("-" * 78)
    lines.append("No mutation has occurred. Re-run this exact command with --confirm and")
    lines.append("--confirmed-by human:<id>|agent:<id> to perform this install.")
    lines.append("-" * 78)
    return "\n".join(lines)


def render_preview_json(ctx: PreviewContext) -> Dict[str, Any]:
    return {
        "installation_mode": ctx.mode,
        "source": {
            "repository": ctx.source_repo,
            "commit_sha": ctx.source_commit_sha,
            "version_label": ctx.version_label,
            "distribution": ctx.distribution,
            "clone_source": (
                {
                    "repository": ctx.args.clone_source,
                    "commit_sha": ctx.clone_source_sha,
                }
                if ctx.mode == "clone_existing_cell"
                else None
            ),
        },
        "target": {
            "repository": ctx.args.target_repo,
            "path": str(ctx.target),
        },
        "governance": ctx.governance,
        "installed_packages": ctx.installed_packages,
        "files": {
            "created": ctx.files_created_preview,
            "changed": ctx.files_changed_preview,
            "skipped_collisions": ctx.files_collision_preview,
        },
        "rollback": ctx.rollback_preview,
        "confirmed": False,
    }


# --------------------------------------------------------------------------
# Preflight invocation
# --------------------------------------------------------------------------


def run_preflight(repo_root: Path, ctx: PreviewContext) -> Tuple[bool, str]:
    preflight = repo_root / "scripts" / "teamcell-install-preflight.sh"
    if not preflight.exists():
        return False, f"preflight script missing: {preflight}"
    # In distribution mode the kit is read from this local checkout, so the
    # preflight checks local readability, not remote access to an identity.
    source_location = str(ctx.repo_root) if ctx.distribution else ctx.source_repo
    cmd = [str(preflight), str(ctx.target), "--mode", ctx.mode, "--source-repo", source_location]
    if ctx.mode == "clone_existing_cell" and ctx.args.clone_source and not is_local_path(ctx.args.clone_source):
        cmd += ["--package-repo", ctx.args.clone_source]
    for pkg in ctx.args.package:
        if "=" in pkg and "@" in pkg:
            _, rest = pkg.split("=", 1)
            pkg_repo = rest.split("@", 1)[0]
            if not is_local_path(pkg_repo):
                cmd += ["--package-repo", pkg_repo]
    result = subprocess.run(cmd)
    return result.returncode == 0, f"exit code {result.returncode}"


# --------------------------------------------------------------------------
# Mutation
# --------------------------------------------------------------------------


@dataclass
class MutationResult:
    created: List[str]
    changed: List[str]
    skipped_collisions: List[str] = field(default_factory=list)
    pre_install_head: Optional[str] = None
    notes: str = ""


def write_governance_file_if_absent(target: Path, governance: Dict[str, Any]) -> Optional[str]:
    gov_path = target / ".bcos" / "CELL-GOVERNANCE.yaml"
    if gov_path.exists():
        return None
    gov_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(governance)
    payload_with_version = {"schema_version": "0.1", **payload}
    write_yaml(gov_path, payload_with_version)
    return ".bcos/CELL-GOVERNANCE.yaml"


def sync_team_profile(
    target: Path, governance: Dict[str, Any], confirmed_by: Optional[str] = None
) -> Optional[str]:
    """Defect #2 (TASK-20260714-030): synchronize the CLI-supplied ownership/
    governance configuration into TEAM-PROFILE.md so it never disagrees with
    the just-written `.bcos/CELL-GOVERNANCE.yaml` -- both are the same
    authoritative `governance` input model, per kernel/schemas/
    teamcell-cell-ownership.schema.md's "Where this model lives".

    Only acts when the CLI actually supplied `cell_owner_role`: an install
    with no ownership input at all leaves the template's own explicitly-
    marked fictional example team (`TEAM-PROFILE.md`'s "not defaults, replace
    with your own team" disclaimer) untouched -- there is nothing CLI-
    supplied to synchronize yet, and overwriting it to all-unresolved would
    make TEAM-PROFILE.md fail `validate-cell.sh`'s pre-existing structural
    requirement of exactly one `decision_authority: true` participant.

    `new_from_template` only, per the task's own scope (`TEAM-PROFILE
    ownership/profile synchronization ... For fresh new_from_template
    installs`) -- `hydrate_existing_repo` targets may already own a
    TEAM-PROFILE.md this script must never overwrite.
    """
    cell_owner_role = governance.get("cell_owner_role")
    if not cell_owner_role:
        return None
    profile_path = target / "TEAM-PROFILE.md"
    if not profile_path.exists():
        return None

    text = profile_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return None

    frontmatter_text = "".join(lines[1:end_idx])
    body_text = "".join(lines[end_idx + 1:])

    import yaml  # already a soft dependency of this script (see write_yaml)

    fm = yaml.safe_load(frontmatter_text) or {}

    role_bindings = governance.get("role_bindings") or {}
    decision_owner_roles = governance.get("decision_owner_roles") or {}

    fm["cell_owner_role"] = cell_owner_role
    fm["decision_owner_roles"] = {
        cls: decision_owner_roles.get(cls, "unresolved") for cls in DECISION_CLASSES
    }
    fm["role_bindings"] = {
        role: {
            "human_id": binding.get("human_id"),
            "display_name": binding.get("display_name"),
            "bound_at": binding.get("bound_at"),
            "bound_by": binding.get("bound_by"),
        }
        for role, binding in role_bindings.items()
    }

    # Defect #1 (BRIEF-20260717-004): a committed real Cell must never
    # retain the raw `human:{{CELL_OWNER_ID}}` template token. This is a
    # per-artifact provenance field (who this was confirmed for), distinct
    # from cell_owner_role/role_bindings (ownership authority) -- see
    # resolve_cell_identity.resolve_on_behalf_of_human_id's docstring. Only
    # ever set from a real confirmed_by identity; explicitly null, never
    # guessed, when unresolved.
    provenance = resolve_cell_identity.resolve_on_behalf_of_human_id(
        target, confirmed_by_override=confirmed_by
    )
    fm["on_behalf_of_human_id"] = provenance.value

    owner_binding = role_bindings.get(cell_owner_role) or {}
    owner_human_id = owner_binding.get("human_id")
    owner_display = owner_binding.get("display_name") or owner_human_id

    participants: Optional[List[Dict[str, Any]]] = None
    if owner_human_id:
        # Legacy flat-field mirroring rule (kernel/schemas/teamcell-cell-ownership.
        # schema.md): non-null exactly when role_bindings[cell_owner_role] is
        # bound; participants[] is derived from every bound role so the
        # human-authored copy and the machine-parsed copy can never disagree.
        fm["decision_owner"] = owner_display
        fm["decision_owner_id"] = owner_human_id
        fm["decision_owner_display"] = owner_display
        participants = []
        for role in sorted(role_bindings):
            binding = role_bindings[role]
            human_id = binding.get("human_id")
            if not human_id:
                continue
            participants.append(
                {
                    "human_id": human_id,
                    "display_name": binding.get("display_name") or human_id,
                    "github": None,
                    "role": "owner" if role == cell_owner_role else "collaborator",
                    "decision_authority": role == cell_owner_role,
                }
            )
        fm["participants"] = participants
    # else: cell_owner_role is named but currently unbound (schema state 2 --
    # "role unbound"). The legacy flat fields and participants[] are left as
    # the template shipped them rather than forced to null/empty, which
    # would make validate-cell.sh's pre-existing "exactly one
    # decision_authority: true participant" structural check unsatisfiable
    # for a Cell that has deliberately named a role without yet appointing a
    # human to it. cell_owner_role/decision_owner_roles/role_bindings above
    # are still synchronized regardless, so the unbound state itself is
    # never hidden.

    new_frontmatter = yaml.safe_dump(fm, sort_keys=False, default_flow_style=False)
    new_text = "---\n" + new_frontmatter + "---\n" + body_text

    if participants is not None:
        new_text = _rewrite_participant_registry_table(new_text, participants)
        new_text = _rewrite_team_members_bullet(new_text, participants)

    profile_path.write_text(new_text, encoding="utf-8")
    return "TEAM-PROFILE.md"


def _rewrite_participant_registry_table(text: str, participants: List[Dict[str, Any]]) -> str:
    lines = text.splitlines(keepends=True)
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("| Human ID |"):
            header_idx = i
            break
    if header_idx is None:
        return text
    data_start = header_idx + 2  # header row, then the "|---|...|" separator row
    data_end = data_start
    while data_end < len(lines) and lines[data_end].lstrip().startswith("|"):
        data_end += 1
    new_rows = [
        f"| `{p['human_id']}` | {p['display_name']} | `{p['github'] or 'null'}` | "
        f"{p['role']} | {'yes' if p['decision_authority'] else 'no'} |\n"
        for p in participants
    ]
    return "".join(lines[:data_start] + new_rows + lines[data_end:])


def _rewrite_team_members_bullet(text: str, participants: List[Dict[str, Any]]) -> str:
    names = ", ".join(f"{p['display_name']} (`{p['human_id']}`)" for p in participants)
    lines = text.splitlines(keepends=True)
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith("- Example members:") or stripped.startswith("- Members:"):
            indent = line[: len(line) - len(stripped)]
            out.append(f"{indent}- Members: {names}.\n")
            i += 1
            # The template's own "Example members: ... and Contributor" bullet
            # wraps onto a following indented continuation line (no leading
            # "-") -- consume it too, or its fictional residue
            # ("(`human:example-contributor`) -- replace with your team.")
            # survives untouched next to the real synced owner above it.
            while (
                i < len(lines)
                and lines[i].strip()
                and not lines[i].lstrip().startswith("-")
                and not lines[i].lstrip().startswith("#")
            ):
                i += 1
            continue
        out.append(line)
        i += 1
    return "".join(out)


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore

        with path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False, default_flow_style=False)
    except ImportError:
        path.write_text(_manual_yaml_dump(data), encoding="utf-8")


def _manual_yaml_dump(data: Any, indent: int = 0) -> str:
    """Minimal, dependency-free YAML dumper for the flat/nested dict shapes
    this script produces. Used only when PyYAML is unavailable."""
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


def capture_pre_install_head(target: Path) -> Optional[str]:
    if not (target / ".git").exists():
        return None
    sha, _ = resolve_local_commit_sha(target, "HEAD")
    return sha


def mutate_new_from_template(ctx: PreviewContext) -> MutationResult:
    bootstrap = ctx.repo_root / "scripts" / "bootstrap-team-cell.sh"
    if not bootstrap.exists():
        raise MutationFailed(f"bootstrap-team-cell.sh not found: {bootstrap}")
    pre_files = set(ctx.target_state.existing_files)
    pre_head = capture_pre_install_head(ctx.target)
    result = subprocess.run(
        [str(bootstrap), "--variant", ctx.args.variant, str(ctx.target)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise MutationFailed(
            f"bootstrap-team-cell.sh --variant {ctx.args.variant} {ctx.target} failed "
            f"(exit {result.returncode}):\n{result.stdout}\n{result.stderr}"
        )
    # bootstrap-team-cell.sh already installed teamcell-lite-baseline (its own
    # exclusion of profiles/ matches that package's manifest entry exactly).
    # Install every OTHER selected package (packages/PACKAGES.yaml) on top —
    # TASK-20260717-007, FAIL-PATTERN-20260717-015. Prefer the package's own
    # installer script (it may have side effects a flat copy would miss,
    # e.g. a CONTEXT_INDEX.md routing append); fall back to the generic
    # path-mapped copy only when no installer is declared.
    for package_id, mapping in ctx.package_plan.items():
        if package_id == "teamcell-lite-baseline":
            continue
        installer = ctx.package_installers.get(package_id)
        if installer is not None:
            if not installer.exists():
                raise MutationFailed(f"package {package_id!r} installer not found: {installer}")
            pkg_result = subprocess.run(
                [str(installer), str(ctx.target)], capture_output=True, text=True
            )
            if pkg_result.returncode != 0:
                raise MutationFailed(
                    f"{installer} {ctx.target} failed (exit {pkg_result.returncode}):\n"
                    f"{pkg_result.stdout}\n{pkg_result.stderr}"
                )
        else:
            for target_rel, src in mapping.items():
                dest = ctx.target / target_rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
    post_files = set(list_files(ctx.target))
    created = sorted(post_files - pre_files)
    gov_written = write_governance_file_if_absent(ctx.target, ctx.governance)
    if gov_written:
        created.append(gov_written)
    sync_team_profile(ctx.target, ctx.governance, confirmed_by=ctx.args.confirmed_by)
    return MutationResult(created=sorted(created), changed=[], pre_install_head=pre_head, notes=result.stdout)


def mutate_hydrate_existing_repo(ctx: PreviewContext) -> MutationResult:
    kit_root = resolve_kit_root(ctx.repo_root, ctx.args.variant)
    if not kit_root.exists():
        raise MutationFailed(f"Template kit not found: {kit_root}")
    pre_head = capture_pre_install_head(ctx.target)
    created: List[str] = []
    changed: List[str] = []
    collisions: List[str] = []
    for rel in list_files(kit_root):
        src = kit_root / rel
        dest = ctx.target / rel
        if dest.exists():
            if rel in ctx.args.include_existing:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                changed.append(rel)
            else:
                collisions.append(rel)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        created.append(rel)
    gov_written = write_governance_file_if_absent(ctx.target, ctx.governance)
    if gov_written:
        created.append(gov_written)
    return MutationResult(
        created=sorted(created),
        changed=sorted(changed),
        skipped_collisions=sorted(collisions),
        pre_install_head=pre_head,
    )


def mutate_clone_existing_cell(ctx: PreviewContext) -> MutationResult:
    source = ctx.args.clone_source
    pre_head = capture_pre_install_head(ctx.target)
    pre_files = set(ctx.target_state.existing_files)

    with tempfile.TemporaryDirectory(prefix="teamcell-clone-source-") as tmp:
        clone_dir = Path(tmp) / "source"
        if is_local_path(source):
            shutil.copytree(
                Path(source).expanduser().resolve(),
                clone_dir,
                ignore=shutil.ignore_patterns(".git"),
            )
        else:
            result = subprocess.run(
                ["gh", "repo", "clone", source, str(clone_dir), "--", "--quiet"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise MutationFailed(
                    f"gh repo clone {source} failed (exit {result.returncode}): {result.stderr}"
                )
            if ctx.args.clone_ref:
                checkout = subprocess.run(
                    ["git", "-C", str(clone_dir), "checkout", "--quiet", ctx.args.clone_ref],
                    capture_output=True,
                    text=True,
                )
                if checkout.returncode != 0:
                    raise MutationFailed(
                        f"git checkout {ctx.args.clone_ref} in cloned source failed: {checkout.stderr}"
                    )
            shutil.rmtree(clone_dir / ".git", ignore_errors=True)

        selected_paths = ctx.args.clone_paths or ["."]
        source_files: List[str] = []
        for sel in selected_paths:
            sel_path = clone_dir / sel
            if sel_path.is_dir():
                source_files.extend(
                    str((Path(sel) / f)) if sel != "." else f for f in list_files(sel_path)
                )
            elif sel_path.is_file():
                source_files.append(sel)

        ctx.target.mkdir(parents=True, exist_ok=True)
        created, changed = [], []
        for rel in sorted(set(source_files)):
            src = clone_dir / rel
            dest = ctx.target / rel
            existed = str(rel) in pre_files
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            (changed if existed else created).append(rel)

    if not ctx.args.carry_over_governance:
        gov_path = ctx.target / ".bcos" / "CELL-GOVERNANCE.yaml"
        was_copied = gov_path.exists() and str(Path(".bcos") / "CELL-GOVERNANCE.yaml") in (created + changed)
        gov_path.parent.mkdir(parents=True, exist_ok=True)
        write_yaml(gov_path, {"schema_version": "0.1", **ctx.governance})
        rel = str(Path(".bcos") / "CELL-GOVERNANCE.yaml")
        if was_copied and rel not in changed:
            changed.append(rel)
        elif rel not in created and rel not in changed:
            created.append(rel)

    if not (ctx.target / ".git").exists():
        subprocess.run(["git", "-C", str(ctx.target), "init", "-b", "main"], capture_output=True, text=True)

    return MutationResult(created=sorted(created), changed=sorted(changed), pre_install_head=pre_head)


MUTATORS = {
    "new_from_template": mutate_new_from_template,
    "hydrate_existing_repo": mutate_hydrate_existing_repo,
    "clone_existing_cell": mutate_clone_existing_cell,
}


# --------------------------------------------------------------------------
# Silent deterministic install closeout (TASK-20260717-007 W1,
# FAIL-PATTERN-20260717-014/015). A confirmed install is not complete until
# this pipeline passes -- a successful installer return must mean the Cell
# is locally ready, not merely that files were copied.
# --------------------------------------------------------------------------


def run_closeout(ctx: "PreviewContext", mutation: "MutationResult") -> Tuple[bool, List[Dict[str, Any]]]:
    target = ctx.target
    steps: List[Dict[str, Any]] = []
    ok = True

    def record(name: str, passed: bool, detail: str) -> None:
        nonlocal ok
        steps.append({"name": name, "passed": passed, "detail": detail.strip()})
        if not passed:
            ok = False

    validate_script = target / "scripts" / "validate-cell.sh"
    if validate_script.exists():
        r = run([str(validate_script), str(target)])
        record("scripts/validate-cell.sh", r.returncode == 0, r.stdout + r.stderr)
    else:
        record("scripts/validate-cell.sh", True, "not present in this Cell — skipped")

    start_script = target / "scripts" / "start-cell.sh"
    if start_script.exists():
        r = subprocess.run(
            [str(start_script)], capture_output=True, text=True, cwd=str(target)
        )
        record(
            "scripts/start-cell.sh (non-interactive smoke test; also refreshes START-HERE.html)",
            r.returncode == 0,
            r.stdout + r.stderr,
        )
    else:
        record("scripts/start-cell.sh", True, "not present in this Cell — skipped")

    if (target / ".git").exists():
        run(["git", "-C", str(target), "add", "-A"])
        r = run(["git", "-C", str(target), "diff", "--cached", "--check"])
        record("git diff --cached --check (whitespace)", r.returncode == 0, r.stdout + r.stderr)

        status = run(["git", "-C", str(target), "status", "--short", "--untracked-files=all"])
        allowed = (
            set(mutation.created)
            | set(mutation.changed)
            | {str(MANIFEST_RELATIVE_PATH), "playbooks/onboarding/START-HERE.html"}
        )
        unexpected = []
        for line in status.stdout.splitlines():
            path = line[3:].strip().strip('"')
            if not path:
                continue
            if path in allowed or str(CLOSEOUT_PROOF_RELATIVE_PATH) == path:
                continue
            unexpected.append(path)
        record(
            "working tree matches the created/changed file set",
            not unexpected,
            ("unexpected path(s) not accounted for by this install: " + ", ".join(unexpected))
            if unexpected
            else "clean — every reported path is accounted for by this install",
        )
    else:
        record("git working-tree reconciliation", True, "target has no .git yet — skipped")

    return ok, steps


def write_closeout_report(ctx: "PreviewContext", steps: List[Dict[str, Any]], ok: bool) -> Path:
    report_path = ctx.target / CLOSEOUT_PROOF_RELATIVE_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "bcos_type: report",
        "kind: install_closeout_proof",
        "surface: installation",
        "id: INSTALL-CLOSEOUT-PROOF",
        'title: "Installer closeout proof"',
        f"status: {'active' if ok else 'draft'}",
        f"created: {today()}",
        "created_by: system:teamcell-install-preview",
        "created_by_type: system",
        "created_by_id: system:teamcell-install-preview",
        'created_by_display: "Teamcell canonical installer"',
        "created_by_github: null",
        f"on_behalf_of_human_id: {ctx.args.confirmed_by or 'null'}",
        "agent_model: interactive-shell",
        "---",
        "",
        "# Installer closeout proof",
        "",
        "Generated automatically by the confirmed installer transaction "
        "(TASK-20260717-007 W1) — durable evidence that the canonical "
        "silent closeout pipeline (validator, start-cell.sh smoke test, "
        "whitespace/tree reconciliation) ran before the installer declared "
        "success. This is distinct from "
        "`reports/verification/FIRST-RUN-INSTALL-HANDOFF.md`, the separate "
        "agent-authored first-real-usage proof that "
        "`scripts/validate-cell.sh` checks for its first-use-pending "
        "signal.",
        "",
        f"Overall: {'PASS' if ok else 'FAIL'}",
        "",
        "| Step | Result |",
        "|---|---|",
    ]
    for step in steps:
        lines.append(f"| {step['name']} | {'PASS' if step['passed'] else 'FAIL'} |")
    lines.append("")
    lines.append("## Detail")
    lines.append("")
    for step in steps:
        lines.append(f"### {step['name']}")
        lines.append("")
        lines.append("```")
        lines.append(step["detail"] or "(no output)")
        lines.append("```")
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def write_manifest(ctx: PreviewContext, mutation: MutationResult) -> Path:
    manifest_path = ctx.target / MANIFEST_RELATIVE_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "0.1",
        "installation_id": ctx.args.installation_id or f"INSTALL-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{ctx.args.installation_seq or '001'}",
        "installed_at": now_iso(),
        "installation_mode": ctx.mode,
        "source": {
            "repository": ctx.source_repo,
            "commit_sha": ctx.source_commit_sha,
            "version_label": ctx.version_label,
            "clone_source": (
                {
                    "repository": ctx.args.clone_source,
                    "commit_sha": ctx.clone_source_sha,
                    "installation_receipt_ref": None,
                }
                if ctx.mode == "clone_existing_cell"
                else {"repository": None, "commit_sha": None, "installation_receipt_ref": None}
            ),
        },
        "target": {"repository": ctx.args.target_repo, "path": str(ctx.target)},
        "governance": ctx.governance,
        "installed_packages": ctx.installed_packages,
        "files": {"created": mutation.created, "changed": mutation.changed},
        "rollback": ctx.rollback_preview,
        "preview_confirmed": {
            "confirmed_by": ctx.args.confirmed_by,
            "confirmed_at": now_iso(),
        },
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return manifest_path


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Mandatory preview-then-confirm gate for Teamcell Lite installation. "
            "Never mutates the target without --confirm; refuses entirely when more "
            "than one installation mode is plausible."
        )
    )
    p.add_argument("target", help="local target path (existing or to-be-created)")
    p.add_argument("--instruction", default=None, help="loose natural-language instruction, e.g. 'install Teamcell Lite'")
    p.add_argument("--mode", choices=MODES, default=None, help="explicit installation mode (disambiguates); a public distribution checkout (with distribution/teamcell-lite/SOURCE-MANIFEST.json) accepts only the modes its manifest lists under validated_install_modes and refuses the others before writing anything")
    p.add_argument("--source-repo", default=None, help="template/source repo; default: this distribution checkout when it carries distribution/teamcell-lite/SOURCE-MANIFEST.json, else " + DEFAULT_TEMPLATE_REPO)
    p.add_argument("--source-ref", default=None, help="branch/tag/ref to resolve to a commit SHA")
    p.add_argument("--source-commit-sha", default=None, help="explicit authoritative source commit SHA override")
    p.add_argument("--variant", choices=("stable", "teamcell-lite"), default="teamcell-lite")
    p.add_argument("--clone-source", default=None, help="owner/repo or local path of the concrete Cell to clone (disambiguates to clone_existing_cell)")
    p.add_argument("--clone-ref", default=None, help="branch/tag/commit within the clone source")
    p.add_argument("--clone-paths", nargs="*", default=None, help="restrict clone copy to these repo-relative paths (default: full tree)")
    p.add_argument("--carry-over-governance", action="store_true", help="clone_existing_cell only: carry over the source Cell's governance/ownership instead of resetting to unresolved")
    p.add_argument("--target-repo", default=None, help="owner/repo the target will have as its GitHub remote")
    p.add_argument("--governance-profile", choices=GOVERNANCE_PROFILES, default=None)
    p.add_argument("--governance-selected-by", default=None, help="human:<id> or agent:<id> — required with --governance-profile")
    p.add_argument("--cell-owner-role", default=None)
    p.add_argument("--owner-role", action="append", default=[], help="CLASS=ROLE, may repeat")
    p.add_argument("--bind-role", action="append", default=[], help="ROLE=HUMAN_ID[:DISPLAY_NAME], may repeat")
    p.add_argument("--package", action="append", default=[], help="PACKAGE_ID=REPO@REF, may repeat")
    p.add_argument(
        "--optional-package",
        action="append",
        default=[],
        help="optional in-template package_id to select for new_from_template installs (e.g. "
        "team-capability-pack), may repeat; depends_on packages are auto-included "
        "(packages/PACKAGES.yaml, kernel/schemas/teamcell-package-manifest.schema.md)",
    )
    p.add_argument("--include-existing", action="append", default=[], help="hydrate_existing_repo only: explicit per-file decision to overwrite a colliding target file, may repeat")
    p.add_argument("--installation-id", default=None)
    p.add_argument("--installation-seq", default=None)
    p.add_argument("--confirm", action="store_true", help="perform the mutation (requires --confirmed-by)")
    p.add_argument("--confirmed-by", default=None, help="human:<id> or agent:<id> — required with --confirm")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of human text")
    p.add_argument(
        "--verbose",
        "--debug",
        dest="verbose",
        action="store_true",
        help="show full closeout diagnostics on success (default: concise "
        "Teamcell installed: PASS block; full detail always available in "
        "reports/verification/FIRST-RUN-INSTALL-HANDOFF.md)",
    )
    p.add_argument("--repo-root", default=None, help="bcos repo root (default: this script's repo)")
    return p.parse_args(argv)


def find_repo_root(explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    repo_root = find_repo_root(args.repo_root)

    missing_dependency = require_pyyaml()
    if missing_dependency:
        print("REFUSED — no files were written.", file=sys.stderr)
        print(missing_dependency, file=sys.stderr)
        return EXIT_PREFLIGHT_FAILED

    if args.confirm and not args.confirmed_by:
        print(
            "REFUSED: --confirm was given without --confirmed-by.\n"
            "Repair: pass --confirmed-by human:<id> or agent:<id> naming who explicitly "
            "confirmed this specific install.",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    target_state = compute_target_state(Path(args.target).expanduser().resolve())
    resolution = resolve_candidates(args.mode, args.clone_source, args.instruction, target_state)

    if len(resolution.candidates) > 1:
        print("=" * 78)
        print("AMBIGUOUS INSTALLATION REQUEST — refusing to proceed. No files were written.")
        print("=" * 78)
        print(f"Reason: {resolution.reason}")
        print(f"Target: {target_state.path}")
        print()
        print("More than one installation mode is plausible from the given input:")
        for mode in resolution.candidates:
            print(f"  - {mode}")
        print()
        print("Disambiguate by re-running with exactly one of:")
        print("  --mode {new_from_template|hydrate_existing_repo|clone_existing_cell}")
        print("  --clone-source <owner/repo|local-path>   (selects clone_existing_cell)")
        print()
        print("--confirm is never accepted while a request is ambiguous, even if supplied.")
        return EXIT_AMBIGUOUS_REFUSED

    try:
        ctx = build_context(args, repo_root)
    except InstallRefused as exc:
        print("=" * 78, file=sys.stderr)
        print("REFUSED — no files were written.", file=sys.stderr)
        print("=" * 78, file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return EXIT_REFUSED_NO_CANDIDATE
    except InstallAmbiguous as exc:  # defensive: build_context can also detect ambiguity
        print("=" * 78)
        print("AMBIGUOUS INSTALLATION REQUEST — refusing to proceed. No files were written.")
        print("=" * 78)
        print(f"Reason: {exc.reason}")
        for mode in exc.candidates:
            print(f"  - {mode}")
        return EXIT_AMBIGUOUS_REFUSED

    if args.json:
        print(json.dumps(render_preview_json(ctx), indent=2))
    else:
        print(render_preview_text(ctx))

    if not args.confirm:
        return EXIT_PREVIEW_ONLY_NOT_CONFIRMED

    print()
    print("Confirmed. Running mandatory preflight before mutation...")
    preflight_ok, preflight_diag = run_preflight(repo_root, ctx)
    if not preflight_ok:
        print(f"REFUSED — preflight failed ({preflight_diag}). No files were written.", file=sys.stderr)
        return EXIT_PREFLIGHT_FAILED

    print(f"Preflight passed. Performing {ctx.mode} mutation...")
    try:
        mutation = MUTATORS[ctx.mode](ctx)
    except MutationFailed as exc:
        print(f"MUTATION FAILED: {exc}", file=sys.stderr)
        print("The target may be left in a partially-written state. Inspect before retrying.", file=sys.stderr)
        return EXIT_MUTATION_FAILED

    manifest_path = write_manifest(ctx, mutation)

    if args.verbose:
        print(
            "Running silent install closeout (validate-cell.sh, start-cell.sh "
            "smoke test, whitespace/tree reconciliation)..."
        )
    closeout_ok, closeout_steps = run_closeout(ctx, mutation)
    report_path = write_closeout_report(ctx, closeout_steps, closeout_ok)

    if args.verbose:
        print()
        print("INSTALL COMPLETE (mutation).")
        print(f"  created: {len(mutation.created)} files")
        print(f"  changed: {len(mutation.changed)} files")
        if mutation.skipped_collisions:
            print(f"  skipped (collisions, left untouched): {len(mutation.skipped_collisions)} files")
        print(f"  manifest written: {manifest_path}")
        print()
        print("Closeout steps:")
        for step in closeout_steps:
            print(f"  [{'PASS' if step['passed'] else 'FAIL'}] {step['name']}")
            if not step["passed"] or args.verbose:
                for line in step["detail"].splitlines():
                    print(f"      {line}")
        print()
        print(f"Closeout proof: {report_path}")

    if not closeout_ok:
        print(f"Teamcell installed: FAIL (closeout)", file=sys.stderr)
        print(f"Repository: {ctx.target}", file=sys.stderr)
        failed = [s["name"] for s in closeout_steps if not s["passed"]]
        print(f"Failed step(s): {', '.join(failed)}", file=sys.stderr)
        print(f"Detail: {report_path}", file=sys.stderr)
        print(
            "The installed Cell was preserved (not deleted). Repair the reported "
            "issue(s) and re-run this exact command to re-run closeout, or inspect "
            f"{report_path} for full diagnostics.",
            file=sys.stderr,
        )
        return EXIT_CLOSEOUT_FAILED

    needs_you = "none from this step."
    if ctx.governance.get("legacy_unresolved"):
        needs_you = "select a governance profile (--governance-profile / --governance-selected-by)."
    print("Teamcell installed: PASS")
    print(f"Repository: {ctx.args.target_repo or '(local-only; no --target-repo given)'}")
    print(f"Start: cd {ctx.target} && ./scripts/start-cell.sh")
    print(f"Needs you: {needs_you}")
    if not args.verbose:
        print()
        print(f"Full diagnostics: {report_path}")
        print("Next step — generate the durable installation receipt:")
        print(f"  python3 {repo_root / 'scripts' / 'generate-teamcell-installation-receipt.py'} \\")
        print(f"    {ctx.target} --from-manifest {manifest_path}")
        print("Then, optionally, generate app instruction blocks (interactive):")
        print(f"  {repo_root / 'scripts' / 'personalize-team-cell.sh'} {ctx.target}")
    return EXIT_INSTALLED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
