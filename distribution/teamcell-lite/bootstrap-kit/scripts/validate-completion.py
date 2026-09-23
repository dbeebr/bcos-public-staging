#!/usr/bin/env python3
"""Honest-completion and status-synchronicity check for Teamcell Lite work items.

Called by scripts/validate-cell.sh; can also run on its own:

    python3 scripts/validate-completion.py [CELL_ROOT]

Format check before execution (the Cell profile's task_check):

    python3 scripts/validate-completion.py --ready work/TASK-...md [--fix] [--root CELL_ROOT]

A persisted task is ready for execution when it follows the Cell's current
task template (.bcos/CELL-PROFILE.yaml task_template, default
work/TEMPLATE.task.md): every template frontmatter field is present with a
real value, the required sections (Objective, Procedures, Handoff, Start
Prompt, Definition Of Done) are filled instead of copied from the template,
no "OPEN:" marker or template placeholder is left, named procedures exist in
the Procedure Index and work_status is open or in-progress. --fix fills only
technical fields a fixed rule derives (constants, the ID from the file name,
the created date from the ID, the title from the H1, the task's own path in
the start prompt) and marks other missing fields "OPEN: ..."; it never
invents content, identity, IDs or approvals. Exit 0 ready, 1 not ready (a
draft, not executable), 2 usage.

Scope: every Markdown file under work/ with `bcos_type: task`, except
templates (TEMPLATE*.md) and README.md. Rules (AGENTS.md "Completion"):

1. `work_status` is one of open | in-progress | needs-review | done.
2. A work item with `work_status: done` has a Completion Record whose
   `status` is done, with every required field present and free of template
   placeholders; its Definition Of Done has no unchecked `- [ ]` item.
3. Commit evidence is real: `substantive_commit_sha` (and a non-`same`
   `completion_record_commit_sha`) are full 40-character SHAs that exist in
   this repository; `remote_head_verified_at_completion` is a full SHA that
   exists and contains the substantive commit, or `local-only` when (and
   only when) no `origin` remote is configured.
4. A filled-in Completion Record that says done while `work_status` is not
   done is status drift and fails. The template's unfilled Completion Record
   (still carrying its placeholders) in an open work item is not a claim.
5. Procedure evidence (AGENTS.md "Procedures"): each `procedures_applied`
   entry is `none: <reason>` or `<ID>: loaded <path>...; applied: <evidence>`
   (or `; not applied: <reason>`). Claiming `applied` without `loaded`, or
   naming a procedure that is neither in the Procedure Index nor an existing
   path, fails. `closing_learning` is `none` or a routed pattern. Records
   written before these two fields existed only warn.

Output: one `FAIL: <identity>` / `WARN: <text>` line per finding and a final
`SUMMARY:` line. Exit code 1 when any FAIL was printed. Standard library only.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WORK_STATUSES = ("open", "in-progress", "needs-review", "done")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RECORD_HEADING_RE = re.compile(r"^##+\s+Completion Record(?!.*[Tt]emplate)(?!.*<)[^\n]*$")
DOD_HEADING_RE = re.compile(r"^##+\s+Definition Of Done\b", re.IGNORECASE)
# Required keys; a tuple means "any one of these spellings".
REQUIRED_RECORD_KEYS: List[Tuple[str, ...]] = [
    ("status",),
    ("completed_by", "agent"),
    ("completed_date",),
    ("substantive_commit_sha", "commit_sha"),
    ("completion_record_commit_sha",),
    ("remote_head_verified_at_completion", "remote_head_verification_sha"),
    ("changed_files",),
    ("validation",),
    ("build_drift",),
    ("follow_up_routing", "follow_up_tasks"),
    ("human_gate_required",),
    ("recommendation_only_ending",),
    ("handoff_anchor",),
    ("accepted_risks",),
    ("notes",),
]
# Values copied unchanged from work/TEMPLATE.task.md are not evidence.
PLACEHOLDER_PATTERNS = [
    re.compile(r"<[^>]+>"),
    re.compile(r"YYYY"),
    re.compile(r"full-sha", re.IGNORECASE),
    re.compile(r"agent-or-human-id"),
    re.compile(r"\s\|\s"),
]


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def is_git_repo(root: Path) -> bool:
    return run_git(root, "rev-parse", "--show-toplevel").returncode == 0


def has_origin(root: Path) -> bool:
    return run_git(root, "remote", "get-url", "origin").returncode == 0


def commit_exists(root: Path, sha: str) -> bool:
    return run_git(root, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return run_git(root, "merge-base", "--is-ancestor", ancestor, descendant).returncode == 0


def split_frontmatter(text: str) -> Tuple[Dict[str, str], List[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, lines
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            fields: Dict[str, str] = {}
            for line in lines[1:idx]:
                match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
                if match and match.group(1) not in fields:
                    fields[match.group(1)] = match.group(2).strip().strip('"').strip("'")
            return fields, lines[idx + 1 :]
    return {}, lines


def section(body: List[str], heading_re: re.Pattern, last: bool) -> Optional[List[str]]:
    starts = [i for i, line in enumerate(body) if heading_re.match(line)]
    if not starts:
        return None
    start = starts[-1] if last else starts[0]
    level = len(body[start]) - len(body[start].lstrip("#"))
    out: List[str] = []
    for line in body[start + 1 :]:
        stripped = line.lstrip("#")
        if line.startswith("#") and stripped.startswith(" ") and len(line) - len(stripped) <= level:
            break
        out.append(line)
    return out


def parse_record(lines: List[str]) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    """Top-level `- key: value` / `key: value` pairs plus indented child lines."""
    values: Dict[str, str] = {}
    children: Dict[str, List[str]] = {}
    current: Optional[str] = None
    for raw in lines:
        if raw.strip().startswith("```") or not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        match = re.match(r"^\s*(?:-\s+)?([a-z_][a-z0-9_]*):\s*(.*)$", raw)
        if match and indent <= 2:
            current = match.group(1)
            if current not in values:
                values[current] = match.group(2).strip().strip('"').strip("'")
                children[current] = []
            continue
        if current is not None and indent > 2:
            children[current].append(raw.strip())
    return values, children


def first_value(values: Dict[str, str], keys: Tuple[str, ...]) -> Tuple[Optional[str], Optional[str]]:
    for key in keys:
        if key in values:
            return key, values[key]
    return None, None


def has_placeholder(value: str) -> bool:
    return any(pattern.search(value) for pattern in PLACEHOLDER_PATTERNS)


INDEX_ROW_RE = re.compile(r"^\|\s*([A-Z0-9][A-Z0-9_-]*)\s*\|")


def indexed_procedures(root: Path) -> Optional[Dict[str, str]]:
    """ID -> path from the generated Procedure Index in CONTEXT_INDEX.md."""
    index = root / "CONTEXT_INDEX.md"
    if not index.is_file():
        return None
    text = index.read_text(encoding="utf-8")
    start, end = text.find("<!-- procedure-index:start"), text.find("<!-- procedure-index:end -->")
    if start < 0 or end < start:
        return None
    out: Dict[str, str] = {}
    for line in text[start:end].splitlines():
        match = INDEX_ROW_RE.match(line)
        if match and match.group(1) not in ("ID",):
            path = re.search(r"`([^`]+)`", line)
            out[match.group(1)] = path.group(1) if path else ""
    return out


def check_procedures(root: Path, rel: str, record: Dict[str, str], children: Dict[str, List[str]],
                     index: Optional[Dict[str, str]]) -> Tuple[List[str], List[str]]:
    fails: List[str] = []
    warns: List[str] = []
    if "procedures_applied" not in record:
        warns.append(f"{rel}: Completion Record has no procedures_applied (selection/loading/application evidence)")
    else:
        entries = [line.lstrip("- ").strip() for line in children.get("procedures_applied", []) if line.strip()]
        inline = record.get("procedures_applied", "").strip()
        if inline and inline not in ("[]",):
            entries.insert(0, inline)
        if not entries:
            fails.append(f"Completion Record procedures_applied in {rel} is empty (use 'none: <reason>')")
        for entry in entries:
            if has_placeholder(entry):
                fails.append(f"Completion Record field procedures_applied in {rel} still contains a template placeholder")
                continue
            match = re.match(r"^([A-Za-z0-9][A-Za-z0-9_.-]*):\s*(.*)$", entry)
            if not match:
                fails.append(f"procedures_applied entry in {rel} is not '<ID>: loaded ...' or 'none: <reason>': {entry}")
                continue
            pid, detail = match.group(1), match.group(2).strip()
            if pid == "none":
                if not detail:
                    fails.append(f"procedures_applied 'none' in {rel} gives no reason")
                continue
            loaded = re.search(r"\bloaded\s+(\S+)", detail)
            applied = re.search(r"(?<!not )\bapplied:\s*(\S.*)", detail)
            not_applied = re.search(r"\bnot applied:\s*(\S.*)", detail)
            if not loaded:
                fails.append(f"procedure {pid} in {rel} is recorded without 'loaded <path>' — naming or applying a procedure without loading it is not evidence")
            if not applied and not not_applied:
                fails.append(f"procedure {pid} in {rel} records neither 'applied: <evidence>' nor 'not applied: <reason>'")
            known = index is not None and pid in index
            loaded_path = loaded.group(1).split("@", 1)[0].strip("`;,") if loaded else ""
            if not known and not (loaded_path and (root / loaded_path).is_file()):
                fails.append(f"procedure {pid} in {rel} is not in the Procedure Index and its loaded path does not exist in this Cell")
    if "closing_learning" not in record:
        warns.append(f"{rel}: Completion Record has no closing_learning")
    else:
        value = record.get("closing_learning", "").strip()
        extra = children.get("closing_learning", [])
        if not value and not extra:
            fails.append(f"Completion Record closing_learning in {rel} is empty (use 'none')")
        elif any(has_placeholder(v) for v in [value] + extra if v):
            fails.append(f"Completion Record field closing_learning in {rel} still contains a template placeholder")
    return fails, warns


def check_item(root: Path, path: Path, git: bool, origin: bool,
               index: Optional[Dict[str, str]] = None) -> Tuple[List[str], List[str], str]:
    rel = path.relative_to(root).as_posix()
    fails: List[str] = []
    warns: List[str] = []
    fields, body = split_frontmatter(path.read_text(encoding="utf-8"))
    work_status = fields.get("work_status", "")

    if work_status not in WORK_STATUSES:
        fails.append(f"invalid work_status '{work_status}' in {rel} (allowed: {' | '.join(WORK_STATUSES)})")

    record_lines = section(body, RECORD_HEADING_RE, last=True)
    record, children = parse_record(record_lines) if record_lines is not None else ({}, {})
    record_status = record.get("status", "")
    record_says_done = record_status in ("done", "complete")

    if work_status != "done":
        unfilled_template = any(
            has_placeholder(value) for value in list(record.values()) + [c for lst in children.values() for c in lst] if value
        )
        if record_says_done and not unfilled_template:
            fails.append(
                f"status drift in {rel}: Completion Record says '{record_status}' but work_status is '{work_status}'"
            )
        return fails, warns, work_status

    if record_lines is None:
        fails.append(f"work_status done without a Completion Record in {rel}")
        return fails, warns, work_status
    if record_status != "done":
        fails.append(f"work_status done but Completion Record status is '{record_status or 'missing'}' in {rel}")

    for keys in REQUIRED_RECORD_KEYS:
        key, value = first_value(record, keys)
        label = " or ".join(keys)
        if key is None:
            fails.append(f"Completion Record in {rel} lacks {label}")
            continue
        entries = [value] + children.get(key, [])
        if any(has_placeholder(entry) for entry in entries if entry):
            fails.append(f"Completion Record field {key} in {rel} still contains a template placeholder")

    completed_date = record.get("completed_date", "")
    if completed_date and not DATE_RE.match(completed_date):
        fails.append(f"Completion Record completed_date in {rel} is not YYYY-MM-DD")

    if record.get("recommendation_only_ending", "") not in ("", "false"):
        fails.append(f"Completion Record in {rel} must set recommendation_only_ending: false")

    validation_lines = [line.lstrip("- ").strip() for line in children.get("validation", [])]
    for required in ("validate-cell.sh", "git diff --check"):
        if not any(required in line for line in validation_lines):
            fails.append(f"Completion Record validation in {rel} does not record {required}")
    for line in validation_lines:
        if re.search(r":\s*fail\b", line):
            fails.append(f"Completion Record in {rel} records a failed validation: {line}")

    proc_fails, proc_warns = check_procedures(root, rel, record, children, index)
    fails.extend(proc_fails)
    warns.extend(proc_warns)

    dod_lines = section(body, DOD_HEADING_RE, last=False) or []
    if any(re.match(r"^\s*[-*]\s+\[ \]", line) for line in dod_lines):
        fails.append(f"work_status done but Definition Of Done has unchecked items in {rel}")

    _, substantive = first_value(record, ("substantive_commit_sha", "commit_sha"))
    record_sha = record.get("completion_record_commit_sha", "")
    _, remote_head = first_value(record, ("remote_head_verified_at_completion", "remote_head_verification_sha"))

    if substantive and not has_placeholder(substantive) and not SHA_RE.match(substantive):
        fails.append(f"substantive commit SHA in {rel} is not a full 40-character SHA")
    if record_sha and record_sha != "same" and not has_placeholder(record_sha) and not SHA_RE.match(record_sha):
        fails.append(f"completion_record_commit_sha in {rel} is neither 'same' nor a full 40-character SHA")
    if remote_head and not has_placeholder(remote_head):
        if remote_head == "local-only":
            if origin:
                fails.append(f"remote head in {rel} is 'local-only' but an origin remote is configured")
        elif not SHA_RE.match(remote_head):
            fails.append(f"remote head SHA in {rel} is neither 'local-only' nor a full 40-character SHA")

    if git:
        for label, sha in (("substantive commit", substantive), ("completion record commit", record_sha), ("remote head", remote_head)):
            if sha and SHA_RE.match(sha) and not commit_exists(root, sha):
                fails.append(f"{label} {sha} in {rel} does not exist in this repository (fetch first, or the SHA is wrong)")
        if (
            substantive
            and remote_head
            and SHA_RE.match(substantive)
            and SHA_RE.match(remote_head)
            and commit_exists(root, substantive)
            and commit_exists(root, remote_head)
            and not is_ancestor(root, substantive, remote_head)
        ):
            fails.append(f"remote head in {rel} does not contain the substantive commit")
    else:
        warns.append(f"{rel}: not a Git repository — commit evidence could not be checked")

    return fails, warns, work_status


# --------------------------------------------------------------------------
# Format check before execution (--ready)
# --------------------------------------------------------------------------

READY_WORK_STATUSES = ("open", "in-progress")
READY_SECTIONS = ("Objective", "Procedures", "Handoff", "Start Prompt", "Definition Of Done")
TASK_ID_RE = re.compile(r"\b((?:TASK|WORK)-\d{8}-\d{3})\b")
PROCEDURE_TOKEN_RE = re.compile(r"\b([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\b")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
ANGLE_RE = re.compile(r"<[^<>\n]+>")
OPEN_MARK = "OPEN:"
# An open item is "OPEN:" as written by a planner — not a quoted mention of the
# marker itself (e.g. a start prompt saying: stop if "OPEN:" remains).
OPEN_RE = re.compile(r"(?<![\"'`\w])OPEN:")
PATH_TOKEN_RE = re.compile(r"work/[^\s`'\"),;]+\.md")
TEMPLATE_TASK_PATH = "work/TASK-YYYYMMDD-NNN-<slug>.md"
# Technical fields: a fixed rule gives the value; they are never a fact about
# the work, its owner or an approval.
TECHNICAL_RULES = {
    "bcos_type": ("task", "constant for work items"),
    "kind": ("work", "constant for work items"),
    "surface": ("work", "constant for files under work/"),
    "status": ("draft", "artifact trust of a new task"),
    "work_status": ("open", "work state of a task that has not started"),
    "created_by_github": ("null", "an unknown GitHub account is recorded as null"),
    "decision_owner_role": ("unresolved", "the template's visible unresolved default"),
}
CANONICAL_CLASSES = ("local-worker", "git-only-worker", "chat-reviewer", "read-only-observer", "automation")


def frontmatter_blocks(text: str) -> Tuple[Optional[List[Tuple[str, List[str]]]], str]:
    """Top-level frontmatter keys with their raw lines (continuations kept);
    None when the file has no frontmatter."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            blocks: List[Tuple[str, List[str]]] = []
            for line in lines[1:idx]:
                match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):", line)
                if match:
                    blocks.append((match.group(1), [line]))
                elif blocks:
                    blocks[-1][1].append(line)
                else:
                    blocks.append(("", [line]))
            return blocks, "".join(lines[idx + 1 :])
    return None, text


def block_value(raw: List[str]) -> str:
    value = raw[0].split(":", 1)[1].strip() if ":" in raw[0] else ""
    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
        value = value[1:-1]
    return value


def body_sections(body: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    current: Optional[str] = None
    for line in body.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match and not line.startswith("###"):
            current = match.group(1)
            out.setdefault(current, "")
            continue
        if current is not None:
            out[current] += line + "\n"
    return out


def normalized(text: str) -> str:
    return " ".join(COMMENT_RE.sub("", text).split())


def cell_task_template(root: Path) -> Path:
    profile = root / ".bcos" / "CELL-PROFILE.yaml"
    if profile.is_file():
        match = re.search(r"^task_template:\s*\"?([^\s\"#]+)", profile.read_text(encoding="utf-8"), re.M)
        if match:
            return root / match.group(1)
    return root / "work" / "TEMPLATE.task.md"


def open_marker(value: str) -> Optional[str]:
    match = OPEN_RE.search(value)
    return value[match.start():].strip() if match else None


def path_task_id(token: str) -> Optional[str]:
    """The ID part of a work/<ID>-<slug>.md path, valid or placeholder (e.g. TASK-YYYYMMDD-NNN)."""
    match = re.match(r"^work/((?:TASK|WORK)-[^-/]+-[^-/]+)-.+\.md$", token)
    return match.group(1) if match else None


def placeholder_in(value: str) -> Optional[str]:
    marker = open_marker(value)
    if marker:
        return marker
    for pattern in PLACEHOLDER_PATTERNS:
        match = pattern.search(value)
        if match:
            return match.group(0).strip()
    return None


def check_ready(root: Path, rel: str, fix: bool = False) -> Tuple[List[str], List[str], List[str], str]:
    """Return (blocking, fixable-or-fixed, notes, template description)."""
    path = root / rel
    template_path = cell_task_template(root)
    if not template_path.is_file():
        return [f"task template {template_path.relative_to(root).as_posix()} not found (Cell profile task_template)"], [], [], "missing"
    template_text = template_path.read_text(encoding="utf-8")
    template_blocks, template_body = frontmatter_blocks(template_text)
    template_fields = [(k, block_value(v)) for k, v in (template_blocks or []) if k]
    template_values = dict(template_fields)
    template_sections = body_sections(template_body)
    template_desc = (f"{template_path.relative_to(root).as_posix()} "
                     f"(sha256 {hashlib.sha256(template_text.encode('utf-8')).hexdigest()[:16]})")

    text = path.read_text(encoding="utf-8")
    blocks, body = frontmatter_blocks(text)
    blocking: List[str] = []
    fixes: List[str] = []
    notes: List[str] = []
    if blocks is None:
        fixes.append("frontmatter block missing -> added from the task template's field list")
        blocks = []
    present = {k: v for k, v in blocks if k}
    values = {k: block_value(v) for k, v in present.items()}
    sections = body_sections(body)
    new_values: Dict[str, str] = {}

    def is_missing(key: str) -> bool:
        if key not in values:
            return True
        value = values[key]
        if value == "" or placeholder_in(value):
            return True
        if key == "id" and not TASK_ID_RE.fullmatch(value) and re.search(r"NNN|XXX|\?", value):
            return True  # a partly filled placeholder such as TASK-20260922-NNN
        return value == template_values.get(key) and key not in TECHNICAL_RULES

    name_id = TASK_ID_RE.search(path.name)
    id_placeholder = ""  # a partly filled ID (e.g. TASK-20260922-NNN) replaced from the file name
    h1 = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ")), "")
    template_h1 = next((line[2:].strip() for line in template_body.splitlines() if line.startswith("# ")), "")

    for key, template_value in template_fields:
        current = values.get(key)
        if current is not None and open_marker(current):
            # A planner's explicit open item is kept, never replaced by a rule default.
            blocking.append(f"frontmatter {key} is marked open: {current}")
            continue
        if not is_missing(key):
            continue
        state = "missing" if current is None else f"not filled ({current!r})"
        if key in TECHNICAL_RULES:
            value, rule = TECHNICAL_RULES[key]
            new_values[key] = value
            fixes.append(f"frontmatter {key} {state} -> {value} (rule: {rule})")
        elif key == "id" and name_id:
            new_values[key] = name_id.group(1)
            fixes.append(f"frontmatter id {state} -> {name_id.group(1)} (rule: the ID allocated in the file name)")
            if current and current != template_values.get("id") and re.fullmatch(r"(?:TASK|WORK)-[0-9A-Z]{8}-[0-9A-Z]{3}", current):
                id_placeholder = current
        elif key == "created" and (name_id or TASK_ID_RE.search(new_values.get("id", ""))):
            source = new_values.get("id") or name_id.group(1)
            digits = re.search(r"-(\d{8})-", source).group(1)
            value = f"{digits[:4]}-{digits[4:6]}-{digits[6:]}"
            new_values[key] = value
            fixes.append(f"frontmatter created {state} -> {value} (rule: the date in the task ID)")
        elif key == "title" and h1 and h1 != template_h1 and not placeholder_in(h1):
            new_values[key] = json.dumps(h1, ensure_ascii=False)
            fixes.append(f"frontmatter title {state} -> {h1!r} (rule: the task's H1 heading)")
        else:
            blocking.append(f"frontmatter {key} {state}: not derivable by rule — the planner or author must supply it")
            if current is None or not current.startswith(OPEN_MARK):
                new_values[key] = f'"{OPEN_MARK} {key} not recorded — supply it"'

    merged = dict(values)
    merged.update({k: v.strip('"') for k, v in new_values.items()})
    task_id = merged.get("id", "")
    if task_id and not placeholder_in(task_id):
        if not TASK_ID_RE.fullmatch(task_id):
            blocking.append(f"id {task_id!r} is not TASK-YYYYMMDD-NNN (or legacy WORK-...)")
        elif name_id and name_id.group(1) != task_id:
            blocking.append(f"id {task_id} differs from the ID in the file name ({name_id.group(1)}); the file name is the allocation — resolve which is right")
        else:
            for other in sorted((root / "work").rglob("*.md")):
                if other.resolve() == path.resolve() or other.name.startswith("TEMPLATE"):
                    continue
                other_fields, _ = split_frontmatter(other.read_text(encoding="utf-8"))
                if other_fields.get("id") == task_id:
                    blocking.append(f"id {task_id} is already used by {other.relative_to(root).as_posix()}")
    work_status = merged.get("work_status", "")
    if work_status and work_status not in READY_WORK_STATUSES and not placeholder_in(work_status):
        blocking.append(f"work_status {work_status!r}: only open or in-progress work items are started")
    created = merged.get("created", "")
    if created and not placeholder_in(created) and not DATE_RE.match(created):
        blocking.append(f"created {created!r} is not YYYY-MM-DD")
    creator_type = merged.get("created_by_type", "")
    if creator_type and not placeholder_in(creator_type):
        if creator_type not in ("human", "agent", "system"):
            blocking.append(f"created_by_type {creator_type!r} is not human | agent | system")
        if creator_type == "agent":
            for key in ("agent_id", "agent_model", "agent_capability_class", "on_behalf_of_human_id"):
                value = merged.get(key, "")
                if value in ("", "null") and key in template_values:
                    blocking.append(f"{key} is {value or 'empty'} although created_by_type is agent — record who planned it")
    capability = merged.get("agent_capability_class", "")
    if capability and capability != "null" and not placeholder_in(capability) and capability not in CANONICAL_CLASSES:
        blocking.append(f"agent_capability_class {capability!r} is not one of {' | '.join(CANONICAL_CLASSES)}")

    for key, value in values.items():
        if open_marker(value) and not any(item.startswith(f"frontmatter {key} ") for item in blocking):
            blocking.append(f"frontmatter {key} is marked open: {value}")

    index = indexed_procedures(root)
    new_body = body
    for name in READY_SECTIONS:
        if name not in sections:
            blocking.append(f"section '## {name}' missing (task template {template_path.name})")
            continue
        content = sections[name]
        visible = COMMENT_RE.sub("", content)
        if not visible.strip():
            blocking.append(f"section '## {name}' is empty")
            continue
        if name in template_sections and normalized(content) == normalized(template_sections[name]):
            blocking.append(f"section '## {name}' is still the template text")
            continue
        if name == "Start Prompt":
            for token in sorted(set(PATH_TOKEN_RE.findall(visible))):
                token_id = path_task_id(token)
                if token == rel or token_id is None:
                    continue
                if not TASK_ID_RE.fullmatch(token_id):
                    fixes.append(f"Start Prompt names the placeholder path {token} -> {rel} (rule: the task's own path)")
                    new_body = new_body.replace(token, rel)
                    visible = visible.replace(token, rel)
                else:
                    notes.append(f"Start Prompt also names {token}")
            if rel not in visible:
                blocking.append(f"section '## Start Prompt' does not name this work item's path ({rel})")
        for line in visible.splitlines():
            if open_marker(line):
                blocking.append(f"section '## {name}' has an open item: {line.strip()}")
            elif name != "Definition Of Done":  # its items may document usage forms such as `--baseline <file>`
                found = ANGLE_RE.search(line) or re.search(r"YYYY", line)
                if found:
                    blocking.append(f"section '## {name}' still contains the placeholder {found.group(0)!r}: {line.strip()}")
        if name == "Procedures":
            items = [line.strip()[2:].strip() for line in visible.splitlines() if line.strip().startswith(("- ", "* "))]
            if not items:
                blocking.append("section '## Procedures' names no procedure and no 'none — <reason>'")
            for item in items:
                if re.match(r"^`?none`?\b", item, re.I):
                    reason = re.sub(r"^`?none`?\s*[—:-]*\s*", "", item, flags=re.I).strip()
                    if not reason or reason.lower() == "reason":
                        blocking.append("Procedures 'none' gives no reason (template line left unchanged?)")
                    continue
                tokens = [tok for tok in PROCEDURE_TOKEN_RE.findall(item) if not TASK_ID_RE.fullmatch(tok)]
                if not tokens:
                    blocking.append(f"Procedures line names no procedure ID: {item}")
                elif index is None:
                    notes.append(f"no Procedure Index in CONTEXT_INDEX.md to confirm {tokens[0]}")
                elif tokens[0] not in index:
                    blocking.append(f"Procedures names {tokens[0]}, which is not in this Cell's Procedure Index — no invented or uninstalled procedure")
        if name == "Definition Of Done" and not re.search(r"^\s*[-*]\s+\[[ xX]\]", visible, re.M):
            blocking.append("section '## Definition Of Done' has no checklist item")

    if id_placeholder and id_placeholder in new_body:
        count = new_body.count(id_placeholder)
        fixes.append(f"placeholder ID {id_placeholder} in the body ({count}x) -> {new_values['id']} (rule: the ID allocated in the file name)")
        new_body = new_body.replace(id_placeholder, new_values["id"])
    if fix and (new_values or new_body != body or not text.startswith("---")):
        out_lines = ["---\n"]
        used = set()
        for key, _ in template_fields:
            used.add(key)
            if key in new_values:
                out_lines.append(f"{key}: {new_values[key]}\n")
            elif key in present:
                out_lines.extend(present[key])
        for key, raw in blocks:
            if key not in used:
                out_lines.extend(raw)
        out_lines.append("---\n")
        path.write_text("".join(out_lines) + new_body, encoding="utf-8")
    return blocking, fixes, notes, template_desc


def ready_main(args: List[str]) -> int:
    fix = "--fix" in args
    args = [a for a in args if a != "--fix"]
    root = Path(__file__).resolve().parents[1]
    if "--root" in args:
        idx = args.index("--root")
        if idx + 1 >= len(args):
            print("usage: validate-completion.py --ready TASK_PATH [--fix] [--root CELL_ROOT]", file=sys.stderr)
            return 2
        root = Path(args[idx + 1]).resolve()
        del args[idx : idx + 2]
    if not args:
        print("usage: validate-completion.py --ready TASK_PATH [--fix] [--root CELL_ROOT]", file=sys.stderr)
        return 2
    worst = 0
    for raw in args:
        path = Path(raw)
        path = path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()
        if not path.is_file():
            path = (root / raw).resolve()
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            print(f"FAIL: {raw} is not inside the Cell {root}", file=sys.stderr)
            return 2
        if not path.is_file():
            print(f"FAIL: task not found: {rel}", file=sys.stderr)
            return 2
        blocking, fixes, notes, template_desc = check_ready(root, rel, fix=fix)
        if fix and fixes:
            again, _, notes, _ = check_ready(root, rel, fix=False)
            for item in fixes:
                print(f"FIXED: {item}")
            blocking = again
        else:
            for item in fixes:
                print(f"FIXABLE: {item}")
        for item in blocking:
            print(f"OPEN: {item}")
        for item in notes:
            print(f"NOTE: {item}")
        pending_fixes = [] if fix else fixes
        if blocking or pending_fixes:
            worst = 1
            reason = f"{len(blocking)} open item(s) need the planner or decision owner" if blocking else "technical fields only"
            hint = " — run with --fix for the technical ones" if pending_fixes else ""
            print(f"RESULT: NOT READY {rel} (template {template_desc}): {reason}; "
                  f"{len(pending_fixes)} fixable{hint}. A draft, not executable.")
        else:
            print(f"RESULT: READY {rel} (template {template_desc})")
    return worst


def main(argv: List[str]) -> int:
    if "--ready" in argv[1:]:
        return ready_main([a for a in argv[1:] if a != "--ready"])
    root = Path(argv[1] if len(argv) > 1 else Path(__file__).resolve().parents[1]).resolve()
    work_dir = root / "work"
    items = []
    if work_dir.is_dir():
        for path in sorted(work_dir.rglob("*.md")):
            if path.name.startswith("TEMPLATE") or path.name == "README.md":
                continue
            fields, _ = split_frontmatter(path.read_text(encoding="utf-8"))
            if fields.get("bcos_type") == "task":
                items.append(path)

    git = is_git_repo(root)
    origin = git and has_origin(root)
    index = indexed_procedures(root)
    total_fails = 0
    counts: Dict[str, int] = {}
    for path in items:
        fails, warns, status = check_item(root, path, git, origin, index)
        counts[status or "missing"] = counts.get(status or "missing", 0) + 1
        for message in fails:
            print(f"FAIL: {message}")
        for message in warns:
            print(f"WARN: {message}")
        total_fails += len(fails)

    breakdown = ", ".join(f"{key}: {value}" for key, value in sorted(counts.items())) or "none"
    print(f"SUMMARY: {len(items)} work item(s) checked ({breakdown})")
    return 1 if total_fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
