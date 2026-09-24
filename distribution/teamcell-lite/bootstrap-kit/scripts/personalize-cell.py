#!/usr/bin/env python3
"""Personalize an installed Cell from verified facts — non-interactive.

An installed Cell must be usable the moment installation finishes: the project
instructions carry the Cell's real name, repository, governance and entry
paths, and the operational setup files have no leftover template slots. This
script is the one place that produces those outputs. The installer runs it as a
mandatory step of a confirmed install; the same command repairs an existing Cell
and re-running it is safe.

What it does (all inside this Cell, nothing outside it):

  1. Derive facts from the Cell itself: repository (installation receipt, then
     the verified Git remote), Cell name (explicit setup value, then a real
     PROJECT.md title, then the repository name), governance profile, owner
     binding and roles that are still unbound (.bcos/CELL-GOVERNANCE.yaml),
     installed packages/procedures (what is actually present). An unknown fact
     is written as an explicit "unresolved"; nothing is invented and no role is
     ever bound here.
  2. Render, with scripts/render-instructions.py (the single rendering path):
       instructions/PROJECT-INSTRUCTIONS.md      the ready-to-paste block
       instructions/APP-INSTRUCTIONS-<app>.md    one activation note per app
     These are generated files: never edited by hand, checked by hash.
  3. Fill the install-time slots of ONBOARDING.md ({{CELL_NAME}}, the update
     link, the frontmatter placeholders) and add a marked link to the ready
     instructions in README.md and ONBOARDING.md. Only exact known slots are
     replaced; text a human wrote is never touched.
  4. Write instructions/PERSONALIZATION-MANIFEST.json (which outputs are
     required, their hashes, what is still unresolved) and
     reports/verification/POST-INSTALL-PERSONALIZATION.md (self-reported
     lifecycle: generated / reviewed / activated stay distinct — generation is
     never activation).

Safety. The run is planned first. A generated output that differs from what
would be produced is only replaced if the manifest proves it is an unedited
earlier generation; a hand-edited or unmanaged file is a CONFLICT: nothing is
written, exit 6, and --overwrite PATH is the explicit per-file decision. A
second run with unchanged inputs changes nothing.

Usage:
  personalize-cell.py [--root CELL] [apply|check|plan] [options]
    apply (default)  write the outputs
    check            verify only; exit 1 when a required output is missing,
                     stale, edited or unresolved-token-bearing
    plan             show what apply would do; write nothing

Standard library only; Python 3.9+. Exit codes: 0 ok, 1 check failed, 2 usage,
3 budget refused, 4 invalid inputs, 6 conflict (nothing written).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Never leave compiled bytecode (scripts/__pycache__/) in the Cell this runs from.
sys.dont_write_bytecode = True

VERSION = "1.0"
APP_SURFACES = ("copilot", "chatgpt", "claude", "gemini", "other")
ROLES = ("planner", "executor", "both")
PERSONAL_FACTS = ("tone", "language", "timezone", "role_title")
GENERIC_TITLES = ("Teamcell Lite Project Context",)
RECORD_PATH = "reports/verification/POST-INSTALL-PERSONALIZATION.md"
PROJECT_PATH = "instructions/PROJECT-INSTRUCTIONS.md"
LINK_START = "<!-- personalize:instructions-link:start -->"
LINK_END = "<!-- personalize:instructions-link:end -->"
OPEN_MARK = "<!-- personalize:open:{name} -->"

EXIT_OK, EXIT_CHECK, EXIT_USAGE, EXIT_BUDGET, EXIT_INPUT, EXIT_CONFLICT = 0, 1, 2, 3, 4, 6


class PersonalizeError(Exception):
    def __init__(self, message: str, code: int = EXIT_INPUT):
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------------------
# Renderer (the single rendering path) and small readers
# --------------------------------------------------------------------------


def load_renderer() -> Any:
    path = Path(__file__).resolve().with_name("render-instructions.py")
    if not path.is_file():
        raise PersonalizeError(f"renderer not found next to this script: {path}")
    spec = importlib.util.spec_from_file_location("render_instructions", path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["render_instructions"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".personalize-tmp")
    tmp.write_bytes(text.encode("utf-8"))
    os.replace(tmp, path)


def parse_yaml_subset(text: str, renderer: Any) -> Dict[str, Any]:
    """Nested mappings, lists of scalars and lists of mappings — the shapes of
    .bcos/CELL-GOVERNANCE.yaml and the installation receipt (PyYAML-free)."""
    lines: List[Tuple[int, str]] = []
    for raw in text.splitlines():
        stripped = renderer._strip_comment(raw)
        if not stripped.strip() or stripped.strip() == "---":
            continue
        lines.append((len(stripped) - len(stripped.lstrip(" ")), stripped.strip()))

    def block(i: int, indent: int) -> Tuple[Any, int]:
        if i >= len(lines):
            return {}, i
        if lines[i][1] == "-" or lines[i][1].startswith("- "):
            out: List[Any] = []
            while i < len(lines) and lines[i][0] == indent and (lines[i][1] == "-" or lines[i][1].startswith("- ")):
                body = lines[i][1][1:].strip()
                if not body:
                    i += 1
                    if i < len(lines) and lines[i][0] > indent:
                        value, i = block(i, lines[i][0])
                        out.append(value)
                    else:
                        out.append(None)
                elif re.match(r"^[A-Za-z_][\w.-]*:(\s|$)", body):
                    lines[i] = (indent + 2, body)
                    value, i = block(i, indent + 2)
                    out.append(value)
                else:
                    out.append(renderer._scalar(body))
                    i += 1
            return out, i
        mapping: Dict[str, Any] = {}
        while i < len(lines) and lines[i][0] == indent and not (lines[i][1] == "-" or lines[i][1].startswith("- ")):
            match = re.match(r"^([^:]+?):(?:\s+(.*))?$", lines[i][1])
            if not match:
                i += 1
                continue
            key, rest = match.group(1).strip().strip("\"'"), match.group(2)
            i += 1
            if rest is not None and rest.strip():
                mapping[key] = renderer._scalar(rest)
            elif i < len(lines) and lines[i][0] > indent:
                mapping[key], i = block(i, lines[i][0])
            elif i < len(lines) and lines[i][0] == indent and (lines[i][1] == "-" or lines[i][1].startswith("- ")):
                mapping[key], i = block(i, indent)
            else:
                mapping[key] = None
        return mapping, i

    value, _ = block(0, lines[0][0] if lines else 0)
    return value if isinstance(value, dict) else {}


def load_yaml_file(path: Path, renderer: Any) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    return parse_yaml_subset(read_text(path), renderer)


def git_remote_repository(root: Path) -> Optional[str]:
    try:
        url = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"],
                             capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"github\.com[:/]+([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", url)
    return f"{match.group(1)}/{match.group(2)}" if match else None


def frontmatter_field(path: Path, key: str) -> Optional[str]:
    if not path.is_file():
        return None
    lines = read_text(path).splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = re.match(rf"^{re.escape(key)}:\s*(.*)$", line)
        if match:
            return match.group(1).strip().strip("\"'")
    return None


# --------------------------------------------------------------------------
# Facts
# --------------------------------------------------------------------------


class Facts:
    def __init__(self) -> None:
        self.values: Dict[str, Optional[str]] = {}
        self.sources: Dict[str, str] = {}
        self.unbound_roles: List[str] = []
        self.bound_human_ids: List[str] = []
        self.unresolved_roles: List[str] = []
        self.packages: List[str] = []

    def set(self, key: str, value: Optional[str], source: str) -> None:
        self.values[key] = value
        self.sources[key] = source


def title_from_slug(repository: str) -> str:
    # identical to scripts/resolve-cell-identity.py's repository-slug fallback
    return re.sub(r"[-_]+", " ", repository.split("/")[-1]).strip().title()


def derive_facts(root: Path, args: argparse.Namespace, renderer: Any,
                 previous: Optional[Dict[str, Any]]) -> Facts:
    facts = Facts()
    receipt = load_yaml_file(root / ".installation" / "TEAMCELL-INSTALLATION-RECEIPT.yaml", renderer) or {}
    governance = load_yaml_file(root / ".bcos" / "CELL-GOVERNANCE.yaml", renderer) or {}
    prev_cell = (previous or {}).get("cell") or {}

    # repository
    receipt_repo = ((receipt.get("target") or {}).get("repository")) if isinstance(receipt.get("target"), dict) else None
    remote_repo = git_remote_repository(root)
    if args.repository:
        facts.set("repository", args.repository, "explicit")
    elif receipt_repo:
        facts.set("repository", str(receipt_repo), "installation_receipt")
    elif remote_repo:
        facts.set("repository", remote_repo, "git_remote")
    elif prev_cell.get("repository"):
        facts.set("repository", prev_cell["repository"], "manifest")
    else:
        facts.set("repository", None, "unresolved")

    # Cell name
    project_title = frontmatter_field(root / "PROJECT.md", "title")
    if args.cell_name:
        facts.set("cell_name", args.cell_name, "explicit")
    elif prev_cell.get("name") and prev_cell.get("name_source") in ("explicit", "project_title"):
        # keep the original source: a re-run must reproduce the manifest byte for byte
        facts.set("cell_name", prev_cell["name"], prev_cell["name_source"])
    elif project_title and project_title not in GENERIC_TITLES and "{{" not in project_title:
        facts.set("cell_name", project_title, "project_title")
    elif facts.values.get("repository"):
        facts.set("cell_name", title_from_slug(str(facts.values["repository"])), "repository_name")
    else:
        facts.set("cell_name", None, "unresolved")

    # A provenance label describes where a value was first derived. While the
    # value is unchanged the recorded label is kept, so that the receipt
    # appearing after the install (or a later --repository) does not make the
    # manifest differ on an otherwise identical re-run.
    for key, name_key, source_key in (("repository", "repository", "repository_source"),
                                      ("cell_name", "name", "name_source")):
        recorded = prev_cell.get(source_key)
        if recorded and prev_cell.get(name_key) == facts.values.get(key):
            facts.sources[key] = recorded

    # created date (deterministic: a re-run must not change it)
    installed_at = receipt.get("installed_at")
    if args.created_date:
        facts.set("created_date", args.created_date, "explicit")
    elif (previous or {}).get("created_date"):
        facts.set("created_date", previous["created_date"], "manifest")  # type: ignore[index]
    elif installed_at:
        facts.set("created_date", str(installed_at)[:10], "installation_receipt")
    else:
        facts.set("created_date", _dt.date.today().isoformat(), "today")

    # governance and owner binding — read, never written or defaulted
    profile = governance.get("governance_profile")
    facts.set("governance_profile", str(profile) if profile else None,
              "cell_governance" if profile else "unresolved")
    owner_role = governance.get("cell_owner_role")
    bindings = governance.get("role_bindings") if isinstance(governance.get("role_bindings"), dict) else {}
    owner_binding = bindings.get(owner_role) if owner_role and isinstance(bindings, dict) else None
    facts.set("bound_human_role", str(owner_role) if owner_role else None,
              "cell_governance" if owner_role else "unresolved")
    if isinstance(owner_binding, dict) and owner_binding.get("human_id"):
        facts.set("bound_human_id", str(owner_binding["human_id"]), "cell_governance")
        facts.set("bound_human_display", str(owner_binding.get("display_name") or owner_binding["human_id"]),
                  "cell_governance")
    else:
        facts.set("bound_human_id", None, "unresolved")
        facts.set("bound_human_display", None, "unresolved")
    referenced: List[str] = []
    if owner_role:
        referenced.append(str(owner_role))
    decision_roles = governance.get("decision_owner_roles")
    if isinstance(decision_roles, dict):
        for value in decision_roles.values():
            if value and str(value) != "unresolved" and str(value) not in referenced:
                referenced.append(str(value))
        facts.unresolved_roles = sorted(k for k, v in decision_roles.items() if not v or str(v) == "unresolved")
    for role in referenced:
        binding = bindings.get(role) if isinstance(bindings, dict) else None
        if not (isinstance(binding, dict) and binding.get("human_id")):
            facts.unbound_roles.append(role)
    if isinstance(bindings, dict):
        facts.bound_human_ids = sorted({str(b["human_id"]) for b in bindings.values()
                                        if isinstance(b, dict) and b.get("human_id")})

    # personal preferences: explicit, else what an earlier run recorded
    prev_personal = (((previous or {}).get("facts") or {}).get("personal")) or {}
    for key in PERSONAL_FACTS:
        value = args_facts(args).get(key) or prev_personal.get(key)
        if value:
            facts.set(key, str(value), "explicit" if args_facts(args).get(key) else "manifest")

    # Packages actually installed. Precedence: explicit (the installer), the receipt,
    # what an earlier run recorded, else derived later from the procedures that
    # exist. Always sorted, so the same Cell yields the same list whether it is
    # read at install time, after the receipt exists or by a later `check`.
    if args.installed_package:
        facts.packages = sorted(set(args.installed_package))
    elif isinstance(receipt.get("installed_packages"), list):
        facts.packages = sorted({str(p.get("package_id")) for p in receipt["installed_packages"] if isinstance(p, dict)})
    elif isinstance((previous or {}).get("installed_packages"), list):
        facts.packages = sorted({str(p) for p in previous["installed_packages"]})  # type: ignore[index]
    return facts


def provenance_identity(candidate: Optional[str], facts: Facts) -> Optional[str]:
    """`on_behalf_of_human_id` for the files this step writes. Only a person the Cell's
    governance actually binds is recorded; anyone else (an installer operator who is
    not bound, an agent) stays explicitly null — never a guessed or leaked identity."""
    if candidate and candidate in facts.bound_human_ids:
        return candidate
    return None


def args_facts(args: argparse.Namespace) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for pair in args.fact:
        if "=" not in pair:
            raise PersonalizeError(f"--fact needs key=value, got {pair!r}", EXIT_USAGE)
        key, value = pair.split("=", 1)
        out[key.strip()] = value
    return out


# --------------------------------------------------------------------------
# Plan
# --------------------------------------------------------------------------


class Action:
    def __init__(self, path: str, kind: str, text: Optional[str], state: str, required: bool = False,
                 note: str = ""):
        self.path, self.kind, self.text, self.state = path, kind, text, state
        self.required, self.note = required, note

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"path": self.path, "kind": self.kind, "state": self.state}
        if self.required:
            out["required"] = True
        if self.note:
            out["note"] = self.note
        return out


def classify(root: Path, rel: str, new_text: str, prev_sha: Optional[str], overwrite: List[str]) -> Tuple[str, str]:
    path = root / rel
    if not path.is_file():
        return "create", ""
    current = read_text(path)
    if current == new_text:
        return "unchanged", ""
    if prev_sha and sha256_text(current) == prev_sha:
        return "update", "unedited earlier generation; inputs changed"
    if rel in overwrite:
        return "update", "explicit --overwrite"
    if prev_sha:
        return "conflict", "differs from what was generated and from what would be generated now (edited by hand?)"
    return "conflict", "exists but is not a managed generated output (no matching manifest entry)"


def link_block(surfaces: List[str], prefix: str = "") -> str:
    notes = ", ".join(f"[{s}]({prefix}instructions/APP-INSTRUCTIONS-{s}.md)" for s in surfaces)
    lines = [
        LINK_START,
        f"> **Ready-to-paste agent instructions for this Cell:** open "
        f"[`instructions/PROJECT-INSTRUCTIONS.md`]({prefix}instructions/PROJECT-INSTRUCTIONS.md) and copy "
        "the fenced block into your ChatGPT, Claude, Copilot or Gemini project."
        + (f" Where to paste it, per app: {notes}." if notes else "")
        + " Generated from this Cell's own facts; it is not active in any app until you paste it.",
        LINK_END,
    ]
    return "\n".join(lines)


def insert_link_block(text: str, block: str, anchor_re: str) -> Tuple[str, str]:
    """Replace an existing managed block, else insert after the anchor line."""
    pattern = re.compile(re.escape(LINK_START) + r".*?" + re.escape(LINK_END), re.S)
    if pattern.search(text):
        return pattern.sub(lambda _: block, text, count=1), "replaced"
    match = re.search(anchor_re, text, re.M)
    if not match:
        return text, "anchor_missing"
    end = match.end()
    return text[:end] + "\n\n" + block + text[end:], "inserted"


ONBOARDING_FRONTMATTER = (
    (r"^created: YYYY-MM-DD$", lambda f: f"created: {f['created_date']}"),
    (r"^created_by: human-or-agent$", lambda f: "created_by: personalize-cell"),
    (r"^created_by_type: human \| agent \| system$", lambda f: "created_by_type: system"),
    (r"^created_by_id: human:<id> \| agent:<id>$", lambda f: "created_by_id: system:personalize-cell"),
    (r'^created_by_display: "Display Name"$', lambda f: 'created_by_display: "Teamcell personalization"'),
    (r"^created_by_github: <github-username> \| null$", lambda f: "created_by_github: null"),
    (r"^on_behalf_of_human_id: human:<id> \| null$", lambda f: f"on_behalf_of_human_id: {f['confirmed_by'] or 'null'}"),
    (r"^agent_id: agent:<id> \| null$", lambda f: "agent_id: null"),
    (r"^agent_model: human-or-model$", lambda f: "agent_model: personalize-cell"),
    (r"^agent_capability_class: local-worker \|.*\| null$", lambda f: "agent_capability_class: null"),
)


def plan_onboarding(text: str, cell_name: Optional[str], repository: Optional[str], purpose: Optional[str],
                    created_date: str, confirmed_by: Optional[str], surfaces: List[str],
                    unresolved: List[Dict[str, str]]) -> str:
    """Fill known install-time slots; touch nothing else."""
    out = text
    parts = out.split("\n---\n", 1) if out.startswith("---\n") else None
    if parts and len(parts) == 2:
        head, body = parts
        info = {"created_date": created_date, "confirmed_by": confirmed_by}
        for pattern, make in ONBOARDING_FRONTMATTER:
            head = re.sub(pattern, lambda _m, make=make: make(info), head, flags=re.M)
        if cell_name:
            head = head.replace("{{CELL_NAME}}", cell_name.replace('"', "'"))
        out = head + "\n---\n" + body
    if cell_name:
        out = out.replace("{{CELL_NAME}}", cell_name)

    if "{{CELL_NAME}}" in out:
        unresolved.append({"fact": "cell_name", "where": "ONBOARDING.md", "reason": "Cell name not resolvable"})

    purpose_mark = OPEN_MARK.format(name="cell_purpose")
    if "{{CELL_PURPOSE_ONE_SENTENCE}}" in out or purpose_mark in out:
        if purpose:
            out = out.replace("{{CELL_PURPOSE_ONE_SENTENCE}}", purpose)
            out = re.sub(r"^.*" + re.escape(purpose_mark) + r".*$", lambda _: purpose, out, flags=re.M)
        else:
            open_line = ("_OPEN — this Cell's purpose is not defined yet. The Cell owner sets it in "
                         f"`PROJECT.md`; until then nothing here is guessed._ {purpose_mark}")
            out = out.replace("{{CELL_PURPOSE_ONE_SENTENCE}}", open_line)
    if purpose_mark in out:
        unresolved.append({"fact": "cell_purpose", "where": "ONBOARDING.md section 1",
                           "reason": "no verified purpose statement; pass --cell-purpose or edit PROJECT.md"})

    update_mark = OPEN_MARK.format(name="cell_update_link")
    if "{{LATEST_CELL_UPDATE_LINK}}" in out or update_mark in out:
        if repository:
            link = (f"All Cell Updates: [github.com/{repository}/issues](https://github.com/{repository}"
                    "/issues?q=is%3Aissue+label%3Acell-update)")
            out = out.replace("{{LATEST_CELL_UPDATE_LINK}}", link)
            out = out.replace(update_mark, "").replace("  \n", "\n")
        else:
            out = out.replace("{{LATEST_CELL_UPDATE_LINK}}",
                              f"_OPEN — repository not resolved, so no Cell Update link yet._ {update_mark}")
            unresolved.append({"fact": "cell_update_link", "where": "ONBOARDING.md section 6",
                               "reason": "repository could not be resolved"})

    # one managed comment at the top: the shipped INSTALL TODO, later our own OPEN note
    todo = re.compile(r"<!-- (?:INSTALL TODO:|OPEN: still to be defined).*?-->\n\n?", re.S)
    open_items = [m for m in (purpose_mark, update_mark) if m in out]
    if todo.search(out):
        if open_items:
            names = ", ".join(sorted(re.findall(r"personalize:open:(\w+)", " ".join(open_items))))
            replacement = (f"<!-- OPEN: still to be defined by the Cell owner: {names}. Filled by "
                           "scripts/personalize-cell.py once the fact exists; nothing here is guessed. -->\n\n")
        else:
            replacement = ""
        out = todo.sub(lambda _: replacement, out, count=1)
    if not open_items and "{{" not in out:
        out = re.sub(r"^status: draft$", "status: active", out, count=1, flags=re.M)
    return out


def build_plan(root: Path, args: argparse.Namespace, renderer: Any, facts: Facts,
               previous: Optional[Dict[str, Any]], surfaces: List[str], role: str
               ) -> Tuple[List[Action], Dict[str, Any], List[Dict[str, str]]]:
    cell = renderer.Cell(root, Path(args.profile), Path(args.core))
    entries, excluded, errors = cell.collect_procedures()
    if errors:
        raise PersonalizeError("; ".join(errors))
    prev_sha: Dict[str, str] = {}
    for item in ((previous or {}).get("outputs") or []):
        if isinstance(item, dict) and item.get("path") and item.get("sha256"):
            prev_sha[str(item["path"])] = str(item["sha256"])

    render_facts: Dict[str, str] = {}
    for key in ("cell_name", "repository", "governance_profile", "bound_human_role", "bound_human_display",
                "bound_human_id", "created_date") + PERSONAL_FACTS:
        value = facts.values.get(key)
        if value:
            render_facts[key] = str(value)
    render_facts.update({k: v for k, v in args_facts(args).items() if k == "target_path"})
    surface_for_budget = "chatgpt" if "chatgpt" in surfaces else "generic"
    request = renderer.RenderRequest(surface_for_budget, role, None, render_facts)
    try:
        project_text, report = renderer.render_project_file(cell, request, entries)
    except renderer.BudgetRefused as exc:
        raise PersonalizeError(str(exc), EXIT_BUDGET)

    actions: List[Action] = []
    overwrite = list(args.overwrite)

    def add(rel: str, kind: str, text: str, required: bool) -> None:
        state, note = classify(root, rel, text, prev_sha.get(rel), overwrite)
        actions.append(Action(rel, kind, text, state, required, note))

    add(PROJECT_PATH, "project_block", project_text, True)
    for surface in surfaces:
        template = root / "templates" / f"APP-INSTRUCTIONS-{surface}.template.md"
        if not template.is_file():
            raise PersonalizeError(f"activation-note template missing: templates/APP-INSTRUCTIONS-{surface}.template.md")
        add(f"instructions/APP-INSTRUCTIONS-{surface}.md", "app_note",
            renderer.fill_template(read_text(template), cell, request), True)

    unresolved: List[Dict[str, str]] = []
    for role_name in facts.unbound_roles:
        unresolved.append({"fact": f"role_binding:{role_name}", "where": ".bcos/CELL-GOVERNANCE.yaml",
                           "reason": "role is named but no human is bound; left unbound by design"})
    if not facts.values.get("governance_profile"):
        unresolved.append({"fact": "governance_profile", "where": ".bcos/CELL-GOVERNANCE.yaml",
                           "reason": "no governance profile selected"})
    if not facts.values.get("repository"):
        unresolved.append({"fact": "repository", "where": "instructions/", "reason": "repository not resolvable"})
    if not facts.values.get("cell_name"):
        unresolved.append({"fact": "cell_name", "where": "instructions/",
                           "reason": "no verified Cell name; pass --cell-name"})

    # slot fills / links in human-facing files (never conflicts: exact slots only)
    onboarding = root / "ONBOARDING.md"
    if onboarding.is_file():
        current = read_text(onboarding)
        text = plan_onboarding(current, facts.values.get("cell_name"), facts.values.get("repository"),
                               args.cell_purpose, str(facts.values["created_date"]),
                               provenance_identity(args.confirmed_by, facts), surfaces, unresolved)
        anchor = r"^_A one-page guide\..*_$" if re.search(r"^_A one-page guide\..*_$", text, re.M) else r"^# .*$"
        text, _ = insert_link_block(text, link_block(surfaces), anchor)
        actions.append(Action("ONBOARDING.md", "slot_fill", text, "unchanged" if text == current else "update"))
    readme = root / "README.md"
    if readme.is_file():
        current = read_text(readme)
        text, how = insert_link_block(current, link_block(surfaces), r"^## Start here[ \t]*$")
        note = "anchor '## Start here' missing; link not added" if how == "anchor_missing" else ""
        actions.append(Action("README.md", "link_block", text, "unchanged" if text == current else "update",
                              note=note))

    entries_info = [{"id": e["id"], "kind": e["kind"], "path": e["path"], "package": e["package"]} for e in entries]
    packages = facts.packages or sorted({e["package"] for e in entries if e["package"] and not e["package"].startswith(("host:", "repo"))})
    context = {
        "cell": cell, "entries": entries_info, "excluded": excluded, "packages": packages,
        "report": report, "request": request, "index_version": renderer.index_version(entries),
        "budget_line": renderer.budget_line(report),
    }
    return actions, context, unresolved


# --------------------------------------------------------------------------
# Manifest, record, link check
# --------------------------------------------------------------------------


def build_manifest(renderer: Any, facts: Facts, actions: List[Action], context: Dict[str, Any],
                   surfaces: List[str], role: str, unresolved: List[Dict[str, str]],
                   personal: Dict[str, str]) -> Dict[str, Any]:
    outputs = [{"path": a.path, "kind": a.kind, "required": True, "sha256": sha256_text(a.text or "")}
               for a in actions if a.kind in ("project_block", "app_note")]
    return {
        "schema": "teamcell-personalization/1",
        "generator": {"script": "scripts/personalize-cell.py", "version": VERSION,
                      "renderer": "scripts/render-instructions.py", "renderer_version": renderer.RENDERER_VERSION},
        "created_date": facts.values["created_date"],
        "cell": {
            "name": facts.values.get("cell_name"), "name_source": facts.sources.get("cell_name"),
            "repository": facts.values.get("repository"), "repository_source": facts.sources.get("repository"),
        },
        "governance": {
            "profile": facts.values.get("governance_profile"),
            "cell_owner_role": facts.values.get("bound_human_role"),
            "bound_human": {"role": facts.values.get("bound_human_role"),
                            "id": facts.values.get("bound_human_id"),
                            "display": facts.values.get("bound_human_display")},
            "unbound_roles": facts.unbound_roles,
            "unresolved_decision_classes": facts.unresolved_roles,
        },
        "installed_packages": context["packages"],
        "procedures": context["entries"],
        "procedure_index_version": context["index_version"],
        "agent_role": role,
        "surfaces": surfaces,
        "facts": {"personal": personal},
        "outputs": outputs,
        "unresolved": unresolved,
    }


def read_lifecycle(record: Path) -> Dict[str, str]:
    out = {"reviewed": "false", "activated_self_reported": "false"}
    if record.is_file():
        text = read_text(record)
        for key in out:
            match = re.search(rf"^\s*{key}:\s*(true|false)\s*$", text, re.M)
            if match:
                out[key] = match.group(1)
    return out


def build_record(facts: Facts, actions: List[Action], context: Dict[str, Any], surfaces: List[str],
                 role: str, unresolved: List[Dict[str, str]], lifecycle: Dict[str, str],
                 personal: Dict[str, str], confirmed_by: Optional[str]) -> str:
    generated = [a.path for a in actions if a.kind in ("project_block", "app_note")]
    lines = [
        "---", "bcos_type: report", "kind: post_install_personalization_record", "surface: history",
        "id: POST-INSTALL-PERSONALIZATION", 'title: "Post-Install Personalization Record"',
        "created_by: personalize-cell", "created_by_type: system", "created_by_id: system:personalize-cell",
        'created_by_display: "Teamcell personalization (non-interactive)"', "created_by_github: null",
        f"on_behalf_of_human_id: {confirmed_by or 'null'}", "agent_model: personalize-cell",
        f"created: {facts.values['created_date']}", "status: draft", "---", "",
        "# Post-Install Personalization Record", "",
        "Written by `scripts/personalize-cell.py`. It records what was generated from which verified",
        "facts. It is self-reported and generated locally: it is not proof that any external app was",
        "configured, and `generated` is not `activated` and not `team-ready`.", "", "```yaml",
        "generator: scripts/personalize-cell.py",
        f'resolved_repository: "{facts.values.get("repository") or "unresolved"}"',
        f'resolved_repository_source: {facts.sources.get("repository")}',
        f'resolved_cell_name: "{facts.values.get("cell_name") or "unresolved"}"',
        f'resolved_cell_name_source: {facts.sources.get("cell_name")}',
        f'selected_surfaces: "{" ".join(surfaces) if surfaces else "none"}"',
        "generated_files:",
    ]
    lines += [f"  - {p}" for p in generated] or ["  []"]
    lines += [
        "instruction_lifecycle:", "  generated: true", f"  reviewed: {lifecycle['reviewed']}",
        f"  activated_self_reported: {lifecycle['activated_self_reported']}",
        f"user_confirmed_pasted: {lifecycle['activated_self_reported']}", "verification: self-reported",
        "render:", "  renderer: scripts/render-instructions.py", f"  agent_role: {role}",
        f'  budget: "{context["budget_line"].replace(chr(34), chr(39))}"',
        f"  procedure_index: {context['index_version']}",
        "installed_packages:",
    ]
    lines += [f"  - {p}" for p in context["packages"]] or ["  []"]
    lines += ["personalization_facts:"]
    for key in PERSONAL_FACTS:
        lines.append(f'  {key}: "{personal.get(key, "Not specified")}"')
    lines += ["open_items:"]
    for u in unresolved:
        lines += [f'  - fact: {u["fact"]}', f'    where: "{u["where"]}"', f'    reason: "{u["reason"]}"']
    if not unresolved:
        lines.append("  []")
    lines += ["```", ""]
    return "\n".join(lines)


def check_links(root: Path, rels: List[str]) -> List[str]:
    problems = []
    for rel in rels:
        path = root / rel
        if not path.is_file() or not rel.endswith(".md"):
            continue
        text = read_text(path)
        if rel in ("README.md", "ONBOARDING.md"):
            match = re.search(re.escape(LINK_START) + r".*?" + re.escape(LINK_END), text, re.S)
            text = match.group(0) if match else ""
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            file_part = target.split("#", 1)[0]
            if file_part and not (path.parent / file_part).exists():
                problems.append(f"{rel}: link target does not exist: {target}")
    return problems


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Personalize an installed Cell from verified facts (non-interactive).")
    p.add_argument("command", nargs="?", default="apply", choices=("apply", "check", "plan"))
    p.add_argument("--root", default=None, help="Cell root (default: parent of this script's directory)")
    p.add_argument("--profile", default=".bcos/CELL-PROFILE.yaml")
    p.add_argument("--core", default="templates/PROJECT-INSTRUCTIONS.template.md")
    p.add_argument("--surface", action="append", default=[],
                   help=f"app surface for an activation note ({', '.join(APP_SURFACES)}, all, none); repeatable; "
                        "default: the surfaces of the previous run, else all")
    p.add_argument("--role", choices=ROLES, default=None, help="agent role of the rendered block (default: both)")
    p.add_argument("--cell-name", default=None, help="verified Cell display name (setup value)")
    p.add_argument("--cell-purpose", default=None, help="one-sentence purpose for ONBOARDING.md; never guessed")
    p.add_argument("--repository", default=None, help="OWNER/REPO override (default: receipt, then git remote)")
    p.add_argument("--confirmed-by", default=None, help="human:<id> or agent:<id> who confirmed the install")
    p.add_argument("--created-date", default=None, help="YYYY-MM-DD; default: install date, kept stable across runs")
    p.add_argument("--fact", action="append", default=[],
                   help="key=value: tone, language, timezone, role_title (or target_path, machine-specific; not default)")
    p.add_argument("--installed-package", action="append", default=[], help="package id actually installed (installer)")
    p.add_argument("--overwrite", action="append", default=[],
                   help="PATH: explicit decision to replace a conflicting generated file; repeatable")
    p.add_argument("--reviewed", choices=("true", "false"), default=None, help="self-reported lifecycle flag")
    p.add_argument("--activated", choices=("true", "false"), default=None,
                   help="self-reported: instructions pasted into the app(s); never inferred")
    p.add_argument("--json", action="store_true", help="machine-readable result")
    return p


def resolve_surfaces(args: argparse.Namespace, previous: Optional[Dict[str, Any]]) -> List[str]:
    if not args.surface:
        prev = (previous or {}).get("surfaces")
        return list(prev) if isinstance(prev, list) else list(APP_SURFACES)
    chosen: List[str] = []
    for value in args.surface:
        for part in value.split(","):
            part = part.strip()
            if part == "all":
                chosen.extend(APP_SURFACES)
            elif part == "none" or not part:
                continue
            elif part in APP_SURFACES:
                chosen.append(part)
            else:
                raise PersonalizeError(f"unknown surface {part!r} (known: {', '.join(APP_SURFACES)}, all, none)",
                                       EXIT_USAGE)
    return [s for s in APP_SURFACES if s in chosen]


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    renderer = load_renderer()
    for required in (args.profile, args.core):
        target = root / required
        if not target.is_file():
            raise PersonalizeError(f"this Cell predates the shared instruction renderer (missing {required}); "
                                   "update its Teamcell baseline first. Nothing was written.")
    previous, problem = renderer.load_personalization_manifest(root)
    if problem:
        raise PersonalizeError(problem)
    surfaces = resolve_surfaces(args, previous)
    role = args.role or (previous or {}).get("agent_role") or "both"
    facts = derive_facts(root, args, renderer, previous)
    personal = {k: str(facts.values[k]) for k in PERSONAL_FACTS if facts.values.get(k)}
    actions, context, unresolved = build_plan(root, args, renderer, facts, previous, surfaces, role)

    manifest = build_manifest(renderer, facts, actions, context, surfaces, role, unresolved, personal)
    manifest_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    manifest_path = root / renderer.PERSONALIZATION_MANIFEST
    if not manifest_path.is_file():
        manifest_state = "create"
    else:
        manifest_state = "unchanged" if read_text(manifest_path) == manifest_text else "update"

    lifecycle = read_lifecycle(root / RECORD_PATH)
    if args.reviewed:
        lifecycle["reviewed"] = args.reviewed
    if args.activated:
        lifecycle["activated_self_reported"] = args.activated
    record_text = build_record(
        facts, actions, context, surfaces, role, unresolved, lifecycle, personal,
        provenance_identity(args.confirmed_by or frontmatter_field(root / RECORD_PATH, "on_behalf_of_human_id"), facts))
    record_state, record_note = classify(root, RECORD_PATH, record_text,
                                         None, list(args.overwrite))
    if record_state == "conflict":
        if frontmatter_field(root / RECORD_PATH, "created_by_id") == "system:personalize-cell":
            record_state, record_note = "update", "own record; lifecycle flags preserved"
        else:
            record_note = ("exists and was written by another tool (the interactive wizard?); "
                           "review it, then pass --overwrite " + RECORD_PATH)
    actions.append(Action(RECORD_PATH, "record", record_text, record_state, note=record_note))
    actions.append(Action(renderer.PERSONALIZATION_MANIFEST.as_posix(), "manifest", manifest_text, manifest_state))

    conflicts = [a for a in actions if a.state == "conflict"]
    result: Dict[str, Any] = {
        "command": args.command, "root": str(root), "surfaces": surfaces,
        "cell_name": facts.values.get("cell_name"), "cell_name_source": facts.sources.get("cell_name"),
        "repository": facts.values.get("repository"), "repository_source": facts.sources.get("repository"),
        "actions": [a.to_dict() for a in actions], "unresolved": unresolved,
        "required_outputs": [a.path for a in actions if a.required],
        "budget": context["budget_line"], "conflicts": [a.path for a in conflicts],
    }

    def finish(code: int, lines: List[str]) -> int:
        if args.json:
            result["exit_code"] = code
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("\n".join(lines))
        return code

    summary = [f"Personalization plan for {root} — {facts.values.get('cell_name') or 'unresolved'} "
               f"({facts.values.get('repository') or 'repository unresolved'})"]
    for a in actions:
        summary.append(f"  {a.state:9} {a.path}" + (f"  — {a.note}" if a.note else ""))
    for u in unresolved:
        summary.append(f"  OPEN      {u['fact']}: {u['reason']} ({u['where']})")

    if conflicts:
        summary.append("CONFLICT: nothing was written. Review the file(s) above; pass --overwrite PATH per file "
                       "to replace a generated file on purpose.")
        return finish(EXIT_CONFLICT, summary)
    if args.command == "plan":
        return finish(EXIT_OK, summary)
    if args.command == "check":
        pending = [a for a in actions if a.state in ("create", "update") and a.kind != "record"]
        fails, warns, _ = renderer.run_check(renderer.Cell(root, Path(args.profile), Path(args.core)))
        for message in fails:
            summary.append(f"FAIL: {message}")
        for message in warns:
            summary.append(f"WARN: {message}")
        for a in pending:
            summary.append(f"FAIL: {a.path} is {'missing' if a.state == 'create' else 'out of date'}; "
                           "run: python3 scripts/personalize-cell.py")
        return finish(EXIT_CHECK if (fails or pending) else EXIT_OK, summary)

    changed: List[str] = []
    for a in actions:
        if a.state in ("create", "update") and a.text is not None:
            write_text(root / a.path, a.text)
            changed.append(a.path)
    result["written"] = changed
    fails, warns, check_summary = renderer.run_check(renderer.Cell(root, Path(args.profile), Path(args.core)))
    fails += check_links(root, [a.path for a in actions if a.kind in ("project_block", "app_note", "record")]
                         + ["README.md", "ONBOARDING.md"])
    result["check"] = {"fail": fails, "warn": warns, "summary": check_summary}
    summary.append(f"Written: {len(changed)} file(s)." if changed else "Nothing to change — already up to date.")
    summary.append(context["budget_line"])
    summary.append(f"Ready to paste: {PROJECT_PATH}"
                   + (" (ChatGPT: instructions/APP-INSTRUCTIONS-chatgpt.md)" if "chatgpt" in surfaces else ""))
    for message in fails:
        summary.append(f"FAIL: {message}")
    for message in warns:
        summary.append(f"WARN: {message}")
    return finish(EXIT_CHECK if fails else EXIT_OK, summary)


def main(argv: List[str]) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    try:
        return run(args)
    except PersonalizeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
