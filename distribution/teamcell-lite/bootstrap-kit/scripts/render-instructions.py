#!/usr/bin/env python3
"""Render this Cell's project instructions from one shared core.

One source, many budgeted outputs. The rules live only in
templates/PROJECT-INSTRUCTIONS.template.md (the shared instruction core);
the Cell-specific facts live only in the Cell profile
(.bcos/CELL-PROFILE.yaml: session entry, routing, procedure sources); the
procedure catalog is derived from the procedure files' own frontmatter and
persisted as the "Procedure Index" section of CONTEXT_INDEX.md. Nothing here
is a second hand-maintained copy of any of them.

Commands (all accept --root CELL_ROOT, --profile PATH, --core PATH):

  index [--write]      print the generated Procedure Index section, or write
                       it into CONTEXT_INDEX.md between its markers
  block                print the paste block (the text you paste into a
                       project/app instruction field) and a budget report
  generate             write instructions/PROJECT-INSTRUCTIONS.md plus the thin
                       per-surface activation notes and FIRST-RUN-AGENT-PROMPT.md
  refresh              re-render every generated instruction file from the
                       inputs recorded in its own frontmatter
  context-pack         context pack for hosts without file access: rendered
                       block + entry files + full index lines of any group
                       the block routes via a sub-index + (planner/both) the
                       Cell's task template + (with --task) the task and its
                       full procedures. An executor pack is refused while the
                       task fails the Cell's format check (task_check).
  profile-json         machine-readable profile/metadata for hosts with
                       retrieval or tools
  fill                 fill the __SLOT__ placeholders of a thin template
  check                validator entry point (FAIL:/WARN:/SUMMARY: lines)

Render options: --surface chatgpt|claude|copilot|gemini|local|other|generic,
--role planner|executor|both, --caps file_read,git_read,git_write,tools,
network,persistent_memory (declared host capabilities; anything not listed is
unavailable; omit to leave them undeclared), --fact key=value (repeatable).

Budgets. chatgpt: target 7200, hard limit 8000, counted on the exact paste
text as the larger of Unicode code points and UTF-16 code units (this does
not claim which count the platform uses). Over the target the renderer first
routes whole procedure groups through their named sub-index, never cuts a
rule or an entry; over the hard limit it refuses (exit 3). local: token
budget via --token-budget/--reserve-response/--reserve-task, measured with
--tokenizer-cmd when given, otherwise reported as an estimate only.

Standard library only; Python 3.9+. Exit codes: 0 ok, 1 check failures,
2 usage, 3 budget refused, 4 invalid inputs, 5 handoff refused (task not
ready for execution).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

RENDERER_VERSION = "1.0"
DEFAULT_PROFILE = Path(".bcos") / "CELL-PROFILE.yaml"
DEFAULT_CORE = Path("templates") / "PROJECT-INSTRUCTIONS.template.md"
GENERATED_DIR = Path("instructions")
PROJECT_OUT = GENERATED_DIR / "PROJECT-INSTRUCTIONS.md"
FIRST_RUN_TEMPLATE = Path("templates") / "FIRST-RUN-AGENT-PROMPT.template.md"
FIRST_RUN_OUT = Path("FIRST-RUN-AGENT-PROMPT.md")
SURFACES = ("chatgpt", "claude", "copilot", "gemini", "local", "other", "generic")
APP_SURFACES = ("copilot", "chatgpt", "claude", "gemini", "other")
ROLES = ("planner", "executor", "both")
CAPS = ("file_read", "git_read", "git_write", "tools", "network", "persistent_memory")
CHAR_BUDGETS = {"chatgpt": (7200, 8000)}
INDEX_START = "<!-- procedure-index:start"
INDEX_END = "<!-- procedure-index:end -->"
INDEX_HEADING = "## Procedure Index"
BLOCK_START = "<!-- paste-block:start -->"
BLOCK_END = "<!-- paste-block:end -->"
FACT_KEYS = (
    "cell_name", "repository", "target_path", "governance_profile", "bound_human_role",
    "bound_human_display", "bound_human_id", "tone", "language", "timezone", "role_title",
    "created_date",
)
REQUIRED_PROCEDURE_FIELDS = ("id", "use_when", "not_when", "phase")
KINDS = ("skill", "playbook", "workflow")

EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_BUDGET, EXIT_INPUT, EXIT_NOT_READY = 0, 1, 2, 3, 4, 5


class InputError(Exception):
    pass


class HandoffRefused(Exception):
    pass


class BudgetRefused(Exception):
    def __init__(self, message: str, report: Dict[str, Any]):
        super().__init__(message)
        self.report = report


# --------------------------------------------------------------------------
# Small parsers (no PyYAML dependency: Cells validate with a plain python3)
# --------------------------------------------------------------------------


def _scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if value[0] in "\"'" and value[-1] == value[0] and len(value) >= 2:
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [_scalar(part) for part in _split_flow(inner)] if inner else []
    if value.startswith("{") and value.endswith("}"):
        out: Dict[str, Any] = {}
        for part in _split_flow(value[1:-1]):
            if ":" not in part:
                raise InputError(f"invalid flow mapping entry: {part!r}")
            key, val = part.split(":", 1)
            out[key.strip()] = _scalar(val)
        return out
    if value in ("null", "~"):
        return None
    if value in ("true", "false"):
        return value == "true"
    return value


def _split_flow(text: str) -> List[str]:
    parts, depth, quote, current = [], 0, "", ""
    for ch in text:
        if quote:
            current += ch
            if ch == quote:
                quote = ""
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
            continue
        current += ch
    if current.strip():
        parts.append(current.strip())
    return parts


def _strip_comment(line: str) -> str:
    quote = ""
    for idx, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (idx == 0 or line[idx - 1] in " \t"):
            return line[:idx].rstrip()
    return line.rstrip()


def parse_profile_yaml(text: str) -> Dict[str, Any]:
    """Parse the deliberately small Cell-profile shape: top-level scalars,
    top-level lists of scalars, top-level lists of flat mappings whose values
    are scalars or flow collections. Anything else is an input error."""
    data: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_item: Optional[Dict[str, Any]] = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0:
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$", stripped)
            if not match:
                raise InputError(f"profile line {number}: expected 'key: value'")
            key, rest = match.group(1), match.group(2)
            if rest.strip():
                data[key] = _scalar(rest)
                current_key = None
            else:
                data[key] = []
                current_key = key
            current_item = None
            continue
        if current_key is None:
            raise InputError(f"profile line {number}: indented line without a list key")
        if stripped.startswith("- "):
            body = stripped[2:]
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(\s.*|)$", body)
            if match and not body.startswith(("\"", "'", "[", "{")):
                current_item = {match.group(1): _scalar(match.group(2))}
                data[current_key].append(current_item)
            else:
                data[current_key].append(_scalar(body))
                current_item = None
            continue
        if current_item is None:
            raise InputError(f"profile line {number}: mapping continuation outside a list item")
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(\s.*|)$", stripped)
        if not match:
            raise InputError(f"profile line {number}: expected 'key: value' inside a list item")
        current_item[match.group(1)] = _scalar(match.group(2))
    return data


def split_frontmatter(text: str) -> Tuple[Dict[str, str], str, bool]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text, False
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            fields: Dict[str, str] = {}
            for line in lines[1:idx]:
                match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line.rstrip("\n"))
                if match and match.group(1) not in fields:
                    value = match.group(2).strip()
                    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
                        value = value[1:-1]
                    fields[match.group(1)] = value
            return fields, "".join(lines[idx + 1 :]), True
    return {}, text, False


def first_heading(body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure(text: str) -> Dict[str, int]:
    return {
        "unicode_codepoints": len(text),
        "utf16_code_units": len(text.encode("utf-16-le")) // 2,
        "utf8_bytes": len(text.encode("utf-8")),
        "lines": text.count("\n") + (0 if text.endswith("\n") or not text else 1),
    }


# --------------------------------------------------------------------------
# Cell profile and procedures
# --------------------------------------------------------------------------


class Cell:
    def __init__(self, root: Path, profile_path: Path, core_path: Path):
        self.root = root.resolve()
        self.profile_path = profile_path if profile_path.is_absolute() else self.root / profile_path
        self.core_path = core_path if core_path.is_absolute() else self.root / core_path
        if not self.profile_path.is_file():
            raise InputError(f"Cell profile not found: {self.profile_path}")
        if not self.core_path.is_file():
            raise InputError(f"instruction core not found: {self.core_path}")
        self.profile_text = self.profile_path.read_text(encoding="utf-8")
        self.profile = parse_profile_yaml(self.profile_text)
        self.core_text = self.core_path.read_text(encoding="utf-8")
        for key in ("session_entry", "routing", "procedure_sources", "task_path", "closing_record"):
            if key not in self.profile:
                raise InputError(f"Cell profile {self.rel(self.profile_path)} lacks '{key}'")

    def rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def task_template(self) -> str:
        """Path of the Cell's current task template (first word of the
        profile value; the rest may describe it)."""
        return str(self.profile.get("task_template") or "").split(" ")[0]

    def task_check(self) -> str:
        return str(self.profile.get("task_check") or "")

    def index_persisted(self) -> bool:
        return str(self.profile.get("procedure_index") or "CONTEXT_INDEX.md") != "none"

    def procedure_index_file(self) -> Path:
        if not self.index_persisted():
            raise InputError("this Cell profile sets procedure_index: none (no persisted Procedure Index)")
        return self.root / str(self.profile.get("procedure_index") or "CONTEXT_INDEX.md")

    def collect_procedures(self) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
        """Return (available entries, excluded notes, metadata errors)."""
        entries: List[Dict[str, Any]] = []
        excluded: List[str] = []
        errors: List[str] = []
        seen: Dict[str, str] = {}
        for order, source in enumerate(self.profile.get("procedure_sources") or []):
            if not isinstance(source, dict) or "glob" not in source:
                raise InputError("every procedure_sources item needs a 'glob'")
            field_map = source.get("field_map") or {}
            statuses = source.get("available_status") or ["active"]
            if isinstance(statuses, str):
                statuses = [statuses]
            exclude = source.get("exclude") or []
            if isinstance(exclude, str):
                exclude = [exclude]
            for path in sorted(self.root.glob(str(source["glob"]))):
                if not path.is_file() or any(path.match(pattern) for pattern in exclude):
                    continue
                rel = self.rel(path)
                text = path.read_text(encoding="utf-8")
                fields, body, has_fm = split_frontmatter(text)

                def get(name: str) -> str:
                    mapped = field_map.get(name, name)
                    return str(fields.get(mapped, "") or "").strip()

                status = get("status") or ("undeclared" if not has_fm else "")
                if status not in statuses and not (status == "undeclared" and source.get("undeclared") == "list"):
                    excluded.append(f"{rel} (status: {status or 'missing'})")
                    continue
                entry = {
                    "id": get("id") or path.stem.replace(".playbook", "").replace(".skill", "").upper(),
                    "title": get("title") or first_heading(body) or path.stem,
                    "kind": get("procedure_kind") or str(source.get("kind") or ""),
                    "use_when": get("use_when"),
                    "not_when": get("not_when"),
                    "phase": get("phase"),
                    "path": rel,
                    "package": get("package") or str(source.get("package") or ""),
                    "status": status,
                    "version": get("version"),
                    "sha256": sha256_file(path),
                    "source": order,
                    "sub_index": str(source.get("sub_index") or ""),
                    "render": str(source.get("render") or "auto"),
                    "metadata": "complete",
                }
                missing = [name for name in REQUIRED_PROCEDURE_FIELDS if not entry[name]]
                if entry["kind"] not in KINDS:
                    missing.append("procedure_kind")
                if not entry["package"]:
                    missing.append("package")
                if missing:
                    if source.get("require_metadata", True) is False:
                        entry["metadata"] = "partial"
                    else:
                        errors.append(f"procedure {rel} lacks index metadata: {', '.join(missing)}")
                        continue
                if entry["id"] in seen:
                    errors.append(f"duplicate procedure id {entry['id']} in {rel} and {seen[entry['id']]}")
                    continue
                seen[entry["id"]] = rel
                entries.append(entry)
        return entries, excluded, errors

    def check_profile_paths(self) -> List[str]:
        problems = []
        for rel in self.profile.get("session_entry") or []:
            if not (self.root / str(rel)).exists():
                problems.append(f"Cell profile session_entry path does not exist: {rel}")
        template = self.task_template()
        if template and not (self.root / template).exists():
            problems.append(f"Cell profile task_template path does not exist: {template}")
        for item in self.profile.get("routing") or []:
            target = str((item or {}).get("target", "")).split(" ")[0]
            if not target:
                problems.append("Cell profile routing item without target")
            elif not (self.root / target).exists():
                problems.append(f"Cell profile routing target does not exist: {target}")
        return problems


def index_version(entries: List[Dict[str, Any]]) -> str:
    canonical = [
        {k: e[k] for k in ("id", "kind", "use_when", "not_when", "phase", "path", "package", "sha256")}
        for e in entries
    ]
    return sha256_text(json.dumps(canonical, sort_keys=True, ensure_ascii=False))[:12]


def cell_text(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_index_section(entries: List[Dict[str, Any]]) -> str:
    lines = [
        INDEX_START + " — generated by scripts/render-instructions.py index --write"
        " from the procedure files' frontmatter; do not edit rows by hand -->",
        f"index_version: {index_version(entries)} ({len(entries)} available procedure(s))",
        "",
        "| ID | Kind | Use when | Not when | Phase | Path | Package |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in entries:
        lines.append(
            "| " + " | ".join(
                cell_text(v) for v in (
                    e["id"], e["kind"], e["use_when"], e["not_when"] or "—", e["phase"],
                    f"`{e['path']}`", e["package"],
                )
            ) + " |"
        )
    if not entries:
        lines.append("| none | — | — | — | — | — | — |")
    lines.append(INDEX_END)
    return "\n".join(lines) + "\n"


def extract_index_section(text: str) -> Optional[str]:
    start = text.find(INDEX_START)
    end = text.find(INDEX_END)
    if start < 0 or end < 0 or end < start:
        return None
    return text[start : end + len(INDEX_END)] + "\n"


def write_index(cell: Cell, entries: List[Dict[str, Any]]) -> bool:
    target = cell.procedure_index_file()
    text = target.read_text(encoding="utf-8")
    section = render_index_section(entries)
    current = extract_index_section(text)
    if current is not None:
        start = text.find(INDEX_START)
        end = text.find(INDEX_END) + len(INDEX_END)
        tail = text[end:]
        if tail.startswith("\n"):
            tail = tail[1:]
        new_text = text[:start] + section + tail
    else:
        addition = (
            f"\n{INDEX_HEADING}\n\n"
            "Available procedures in this Cell (generated; see `AGENTS.md` \"Procedures\" for when\n"
            "and how to select, load and record them).\n\n" + section
        )
        new_text = text.rstrip("\n") + "\n" + addition
    if new_text != text:
        target.write_text(new_text, encoding="utf-8")
        return True
    return False


# --------------------------------------------------------------------------
# Core rendering
# --------------------------------------------------------------------------


def core_block_source(core_text: str) -> str:
    start = core_text.find(BLOCK_START)
    end = core_text.find(BLOCK_END)
    if start < 0 or end < 0:
        raise InputError(f"instruction core lacks {BLOCK_START} / {BLOCK_END} markers")
    inner = core_text[start + len(BLOCK_START) : end]
    fence = re.search(r"```text\n(.*?)\n```", inner, re.S)
    if not fence:
        raise InputError("instruction core paste block must be one ```text fence")
    return fence.group(1)


def core_outer(core_text: str) -> Tuple[str, str]:
    _, body, _ = split_frontmatter(core_text)
    start = body.find(BLOCK_START)
    end = body.find(BLOCK_END)
    return body[:start].rstrip() + "\n", body[end + len(BLOCK_END) :].lstrip("\n")


SLOT_RE = re.compile(r"__[A-Z][A-Z_]*[A-Z]__")


def require_known_slots(text: str, known: set, where: str) -> None:
    unknown = sorted(set(SLOT_RE.findall(text)) - known)
    if unknown:
        raise InputError(f"unknown slot(s) in {where}: {', '.join(unknown)}")


def substitute(text: str, slots: Dict[str, str]) -> str:
    """Single pass: a substituted value is never scanned again, so user input
    such as '#', '&' or '__X__' is inserted literally."""
    return SLOT_RE.sub(lambda m: slots.get(m.group(0), m.group(0)), text)



def eval_condition(expr: str, ctx: Dict[str, Any]) -> bool:
    expr = expr.strip()
    negate = expr.startswith("!")
    if negate:
        expr = expr[1:]
    if expr.startswith("role="):
        result = ctx["role"] in expr[5:].split(",")
    elif expr.startswith("surface="):
        result = ctx["surface"] in expr[8:].split(",")
    elif expr == "caps=declared":
        result = ctx["caps"] is not None
    elif expr.startswith("cap:"):
        result = ctx["caps"] is not None and expr[4:] in ctx["caps"]
    else:
        raise InputError(f"unknown condition in instruction core: {expr!r}")
    return not result if negate else result


def apply_conditions(text: str, ctx: Dict[str, Any]) -> str:
    out: List[str] = []
    stack: List[bool] = []
    for line in text.split("\n"):
        stripped = line.strip()
        match = re.match(r"^\[\[if (.+)\]\]$", stripped)
        if match:
            stack.append(eval_condition(match.group(1), ctx))
            continue
        if stripped == "[[end]]":
            if not stack:
                raise InputError("unbalanced [[end]] in instruction core")
            stack.pop()
            continue
        if all(stack):
            out.append(line)
    if stack:
        raise InputError("unclosed [[if]] in instruction core")
    return "\n".join(out)


def host_caps_text(caps: Optional[List[str]]) -> Tuple[str, str]:
    if caps is None:
        return "", ""
    listed = ", ".join(caps) if caps else "none"
    if "file_read" in caps and "git_write" in caps and "tools" in caps:
        limit = "At most local-worker, and only if you can actually run the commands."
    elif "git_write" in caps:
        limit = "At most git-only-worker."
    elif "file_read" in caps or "git_read" in caps:
        limit = "At most read-only-observer or chat-reviewer: you may read, never write."
    else:
        limit = ("At most chat-reviewer: work only from pasted context, name missing files,"
                 " never claim to have read or changed one.")
    if "persistent_memory" not in caps:
        limit += " No memory across sessions: persist only via Git or a copy/paste artifact."
    return listed, limit


def format_entry(e: Dict[str, Any]) -> str:
    tag = f"[{e['kind']}; {e['phase']}]"
    parts = [f"- {e['id']} {tag} use: {e['use_when']}"]
    if e["not_when"]:
        parts.append(f"; not: {e['not_when']}")
    parts.append(f" -> {e['path']} ({e['package']})")
    return "".join(parts)


def format_sub_index(group: List[Dict[str, Any]], level: int) -> str:
    """level 1: names + sub-index; level 2: count + sub-index only."""
    head = group[0]
    kind = head["kind"] or "procedure"
    lead = f"- {len(group)} {kind}(s) via sub-index {head['sub_index']} ({head['package']})"
    if level >= 2:
        return lead + ": load it to see names and triggers before choosing."
    names = "; ".join(f"{e['id']} ({e['title']})" if e["title"] and e["title"] != e["id"] else e["id"] for e in group)
    return f"{lead}: {names}. Load the sub-index or file for triggers before choosing."


def group_levels(entries: List[Dict[str, Any]], levels: Dict[int, int]) -> Dict[int, int]:
    """Effective routing level per source: 0 full rows, 1 names, 2 pointer."""
    out: Dict[int, int] = {}
    for e in entries:
        level = levels.get(e["source"], 0)
        if e["render"] == "sub-index" or e["metadata"] != "complete":
            level = max(level, 1)
        out[e["source"]] = max(out.get(e["source"], 0), level)
    return out


def render_index_lines(entries: List[Dict[str, Any]], levels: Dict[int, int]) -> List[str]:
    lines: List[str] = []
    groups: Dict[int, List[Dict[str, Any]]] = {}
    for e in entries:
        groups.setdefault(e["source"], []).append(e)
    effective = group_levels(entries, levels)
    for source in sorted(groups):
        group = groups[source]
        level = effective.get(source, 0)
        if level > 0:
            if not group[0]["sub_index"]:
                raise InputError(f"procedure group {group[0]['path']} needs a sub_index to be routed")
            lines.append(format_sub_index(group, level))
        else:
            lines.extend(format_entry(e) for e in group)
    if not lines:
        lines.append("- none available in this Cell yet")
    return lines


class RenderRequest:
    def __init__(self, surface: str, role: str, caps: Optional[List[str]], facts: Dict[str, str],
                 char_target: Optional[int] = None, char_limit: Optional[int] = None):
        if surface not in SURFACES:
            raise InputError(f"unknown surface {surface!r} (known: {', '.join(SURFACES)})")
        if role not in ROLES:
            raise InputError(f"unknown role {role!r} (known: {', '.join(ROLES)})")
        if caps is not None:
            unknown = [c for c in caps if c not in CAPS]
            if unknown:
                raise InputError(f"unknown capability {unknown} (known: {', '.join(CAPS)})")
            caps = [c for c in CAPS if c in caps]
        self.surface, self.role, self.caps, self.facts = surface, role, caps, facts
        default_target, default_limit = CHAR_BUDGETS.get(surface, (None, None))
        self.char_target = char_target if char_target is not None else default_target
        self.char_limit = char_limit if char_limit is not None else default_limit

    def inputs(self) -> Dict[str, Any]:
        return {
            "surface": self.surface, "role": self.role, "caps": self.caps,
            "facts": {k: self.facts.get(k, "") for k in FACT_KEYS if k in self.facts},
            "char_target": self.char_target, "char_limit": self.char_limit,
        }


def fact(req: RenderRequest, key: str, default: str = "not specified") -> str:
    value = (req.facts.get(key) or "").strip()
    return value or default


def render_block(cell: Cell, req: RenderRequest, entries: List[Dict[str, Any]],
                 levels: Optional[Dict[int, int]] = None) -> str:
    levels = levels or {}
    ctx = {"role": req.role, "surface": req.surface, "caps": req.caps}
    text = apply_conditions(core_block_source(cell.core_text), ctx)
    listed, limit = host_caps_text(req.caps)
    entry = " -> ".join(str(p) for p in cell.profile["session_entry"])
    routing = "\n".join(
        f"  {item.get('intent')} -> {item.get('target')}" for item in cell.profile["routing"]
    )
    # "inputs" identifies the Cell facts, role, surface and declared host
    # capabilities, so two renders with different facts (e.g. governance or
    # bound human) are distinguishable even by a model without file access.
    inputs_id = sha256_text(json.dumps(req.inputs(), sort_keys=True, ensure_ascii=False))[:12]
    snapshot = (f"index {index_version(entries)}, core {sha256_text(cell.core_text)[:12]}, "
                f"profile {sha256_text(cell.profile_text)[:12]}, inputs {inputs_id}")
    # Role names the work step only; capability and authority are separate
    # inputs (TRUTH AND ACCESS). Planning may persist and hand off tasks;
    # implementation is the execution step.
    role_label = {"planner": "planner (plans, persists tasks, hands off authorized execution)",
                  "executor": "executor (runs persisted tasks that pass the format check)",
                  "both": "planner and executor (separate steps)"}[req.role]
    slots = {
        "__CELL_NAME__": fact(req, "cell_name", "unresolved"),
        "__REPOSITORY__": fact(req, "repository", "unresolved"),
        "__TARGET_PATH__": fact(req, "target_path", "not recorded"),
        "__ROLE__": role_label,
        "__GOVERNANCE_PROFILE__": fact(req, "governance_profile", "unresolved"),
        "__BOUND_HUMAN_ROLE__": fact(req, "bound_human_role", "unresolved"),
        "__BOUND_HUMAN_DISPLAY__": fact(req, "bound_human_display", "unresolved"),
        "__BOUND_HUMAN_ID__": fact(req, "bound_human_id", "unresolved"),
        "__TONE__": fact(req, "tone"),
        "__LANGUAGE__": fact(req, "language"),
        "__TIMEZONE__": fact(req, "timezone"),
        "__HOST_CAPS__": listed,
        "__HOST_CLASS_LIMIT__": limit,
        "__SESSION_ENTRY__": entry,
        "__TASK_PATH__": str(cell.profile["task_path"]),
        "__TASK_TEMPLATE__": str(cell.profile.get("task_template") or "(none named in the Cell profile: ask for it)"),
        "__TASK_CHECK__": cell.task_check().replace("{task}", "<task>") or "none named in the Cell profile: ask the host",
        "__CLOSING_RECORD__": str(cell.profile["closing_record"]),
        "__LEARNING_TARGET__": str(cell.profile.get("learning_target") or "a follow-up work item"),
        "__SNAPSHOT__": snapshot,
        "__SNAPSHOT_RULE__": str(cell.profile.get("snapshot_rule") or (
            "If the Cell's CONTEXT_INDEX.md shows another index_version, the Cell wins: say this "
            "block is stale and ask for a fresh render.")),
    }
    require_known_slots(text, set(slots) | {"__PROCEDURE_INDEX__", "__ROUTING__"}, "instruction core")
    out_lines: List[str] = []
    for line in text.split("\n"):
        if line.strip() == "__PROCEDURE_INDEX__":
            out_lines.extend(render_index_lines(entries, levels))
        elif line.strip() == "__ROUTING__":
            out_lines.append(routing)
        else:
            out_lines.append(substitute(line, slots))
    rendered = "\n".join(out_lines)
    rendered = re.sub(r"\n{3,}", "\n\n", rendered).strip("\n") + "\n"
    return rendered


def budget_value(m: Dict[str, int]) -> int:
    return max(m["unicode_codepoints"], m["utf16_code_units"])


def render_within_budget(cell: Cell, req: RenderRequest, entries: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    """Full entries first. Over the target, route the currently largest
    routable group one step further (names + sub-index, then count +
    sub-index), one step at a time; never cut an entry or a rule. Over the
    hard limit after every routing step, refuse."""
    levels: Dict[int, int] = {}
    routable = sorted({e["source"] for e in entries if e["sub_index"]})
    steps = []
    while True:
        block = render_block(cell, req, entries, levels)
        m = measure(block)
        value = budget_value(m)
        steps.append({"levels": dict(sorted(group_levels(entries, levels).items())), "budget_value": value})
        if req.char_target is None or value <= req.char_target:
            break
        effective = group_levels(entries, levels)
        options = []
        for source in routable:
            if effective.get(source, 0) >= 2:
                continue
            group = [e for e in entries if e["source"] == source]
            current = render_index_lines(group, {source: effective.get(source, 0)})
            options.append((-sum(len(line) for line in current), source))
        if not options:
            break
        _, pick = min(options)
        levels[pick] = effective.get(pick, 0) + 1
    report = {
        "surface": req.surface,
        "role": req.role,
        "caps": req.caps,
        "measure": m,
        "budget_value": value,
        "budget_rule": "max(unicode_codepoints, utf16_code_units) of the exact paste text",
        "char_target": req.char_target,
        "char_limit": req.char_limit,
        "within_target": req.char_target is None or value <= req.char_target,
        "within_limit": req.char_limit is None or value <= req.char_limit,
        "routed_via_sub_index": [
            f"{group[0]['sub_index']} ({'names' if level == 1 else 'pointer only'})"
            for source, level in sorted(group_levels(entries, levels).items()) if level > 0
            for group in [[e for e in entries if e["source"] == source]] if group
        ],
        "index_version": index_version(entries),
        "procedures": [e["id"] for e in entries],
        "routed_sources": sorted(s for s, level in group_levels(entries, levels).items() if level > 0),
        "steps": steps,
    }
    if not report["within_limit"]:
        raise BudgetRefused(
            f"rendered block is {value} (code points/UTF-16 max) and exceeds the hard limit "
            f"{req.char_limit} even with every routable procedure group behind its sub-index; "
            "nothing was cut. Shorten Cell facts or split procedures into sub-indexes.",
            report,
        )
    return block, report


# --------------------------------------------------------------------------
# Generated files
# --------------------------------------------------------------------------


def source_hash(cell: Cell, entries: List[Dict[str, Any]], inputs: Dict[str, Any]) -> str:
    payload = {
        "renderer": RENDERER_VERSION,
        "core": sha256_text(cell.core_text),
        "profile": sha256_text(cell.profile_text),
        "index": index_version(entries),
        "inputs": inputs,
    }
    return sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def budget_line(report: Dict[str, Any]) -> str:
    m = report["measure"]
    line = (f"Paste block size: {m['unicode_codepoints']} Unicode code points / "
            f"{m['utf16_code_units']} UTF-16 code units ({m['utf8_bytes']} UTF-8 bytes)")
    if report["char_limit"]:
        state = "within target" if report["within_target"] else "OVER TARGET (within hard limit)"
        line += f" — {report['surface']} target {report['char_target']}, hard limit {report['char_limit']}: {state}"
    if report["routed_via_sub_index"]:
        line += ". Routed via sub-index to fit: " + ", ".join(report["routed_via_sub_index"])
    return line + "."


def render_project_file(cell: Cell, req: RenderRequest, entries: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    block, report = render_within_budget(cell, req, entries)
    inputs = req.inputs()
    head, tail = core_outer(cell.core_text)
    head = fill_template(head, cell, req)
    tail = fill_template(tail, cell, req)
    frontmatter = "\n".join([
        "---",
        "bcos_type: app_instruction_block",
        "id: PROJECT-INSTRUCTIONS",
        f"title: \"Project-Level Instructions — {fact(req, 'cell_name', 'unresolved')}\"",
        "created_by: render-instructions",
        "agent_model: interactive-shell",
        f"created: {fact(req, 'created_date', _dt.date.today().isoformat())}",
        "status: draft",
        "semantic_source: templates/PROJECT-INSTRUCTIONS.template.md",
        "contract_version: \"2.0\"",
        f"render_renderer_version: \"{RENDERER_VERSION}\"",
        f"render_source_sha256: {source_hash(cell, entries, inputs)}",
        f"render_block_sha256: {sha256_text(block)}",
        f"render_inputs: '{json.dumps(inputs, sort_keys=True, ensure_ascii=False)}'",
        "---",
        "",
    ])
    body = (
        head.rstrip("\n") + "\n\n"
        + budget_line(report) + "\n"
        + f"Rendered for surface `{req.surface}`, role `{req.role}`, host capabilities "
        + (", ".join(req.caps) if req.caps else ("none declared as available" if req.caps is not None else "undeclared (unknown = unavailable)"))
        + f"; procedure index {report['index_version']}.\n\n"
        + BLOCK_START + "\n```text\n" + block + "```\n" + BLOCK_END + "\n\n" + tail
    )
    return frontmatter + body, report


def fill_template(text: str, cell: Cell, req: RenderRequest) -> str:
    slots = {
        "__CELL_NAME__": fact(req, "cell_name", "unresolved"),
        "__REPOSITORY__": fact(req, "repository", "unresolved"),
        "__TARGET_PATH__": fact(req, "target_path", "not recorded"),
        "__TONE__": fact(req, "tone"),
        "__LANGUAGE__": fact(req, "language"),
        "__TIMEZONE__": fact(req, "timezone"),
        "__ROLE__": fact(req, "role_title"),
        "__CREATED_DATE__": fact(req, "created_date", _dt.date.today().isoformat()),
        "__GOVERNANCE_PROFILE__": fact(req, "governance_profile", "unresolved"),
        "__BOUND_HUMAN_ID__": fact(req, "bound_human_id", "unresolved"),
        "__BOUND_HUMAN_DISPLAY__": fact(req, "bound_human_display", "unresolved"),
        "__BOUND_HUMAN_ROLE__": fact(req, "bound_human_role", "unresolved"),
        "__SESSION_ENTRY__": " -> ".join(str(p) for p in cell.profile["session_entry"]),
        "__AGENT_ROLE__": req.role,
    }
    require_known_slots(text, set(slots), "template")
    return substitute(text, slots)


def generated_files(cell: Cell) -> List[Path]:
    directory = cell.root / GENERATED_DIR
    if not directory.is_dir():
        return []
    out = []
    for path in sorted(directory.glob("*.md")):
        fields, _, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        if fields.get("render_block_sha256"):
            out.append(path)
    return out


def extract_block(text: str) -> Optional[str]:
    start = text.find(BLOCK_START)
    end = text.find(BLOCK_END)
    if start < 0 or end < 0:
        return None
    match = re.search(r"```text\n(.*?)```\n", text[start:end + len(BLOCK_END)], re.S)
    return match.group(1) if match else None


def request_from_inputs(inputs: Dict[str, Any]) -> RenderRequest:
    return RenderRequest(
        inputs.get("surface", "generic"), inputs.get("role", "both"), inputs.get("caps"),
        dict(inputs.get("facts") or {}), inputs.get("char_target"), inputs.get("char_limit"),
    )


# --------------------------------------------------------------------------
# Context pack and profile JSON
# --------------------------------------------------------------------------


def estimate_tokens(text: str, tokenizer_cmd: Optional[str]) -> Tuple[int, str]:
    if tokenizer_cmd:
        proc = subprocess.run(shlex.split(tokenizer_cmd), input=text, capture_output=True, text=True)
        if proc.returncode != 0:
            raise InputError(f"tokenizer command failed: {proc.stderr.strip()}")
        return int(proc.stdout.strip().split()[0]), f"measured by host tokenizer: {tokenizer_cmd}"
    return math.ceil(len(text.encode("utf-8")) / 3), "ESTIMATE (UTF-8 bytes / 3, no tokenizer) — not a pass guarantee"


def task_procedure_ids(task_text: str, known: List[str]) -> List[str]:
    match = re.search(r"^##\s+Procedures\s*$(.*?)(?=^##\s|\Z)", task_text, re.M | re.S)
    if not match:
        return []
    section = match.group(1)
    return [pid for pid in known if re.search(r"(?<![A-Z0-9-])" + re.escape(pid) + r"(?![A-Z0-9-])", section)]


def git_blob_state(cell: Cell, rel: str) -> str:
    """Git identity of a file: its blob id and whether it equals the blob at HEAD."""
    here = subprocess.run(["git", "-C", str(cell.root), "hash-object", rel], capture_output=True, text=True)
    head = subprocess.run(["git", "-C", str(cell.root), "rev-parse", f"HEAD:{rel}"], capture_output=True, text=True)
    if here.returncode != 0:
        return "git blob unknown (not a Git checkout)"
    blob = here.stdout.strip()
    if head.returncode != 0:
        return f"git blob {blob[:12]}, NOT committed at HEAD"
    same = head.stdout.strip() == blob
    return f"git blob {blob[:12]}" + ("" if same else f", differs from HEAD blob {head.stdout.strip()[:12]}")


def run_task_check(cell: Cell, task_rel: str) -> Tuple[Optional[int], str, str]:
    """Run the Cell profile's task_check for one task ({task} = its path).
    Returns (exit code, command, output); exit code None when the profile
    names no check."""
    command = cell.task_check()
    if not command:
        return None, "", ""
    command = command.replace("{task}", shlex.quote(task_rel))
    proc = subprocess.run(["sh", "-c", command], cwd=str(cell.root), capture_output=True, text=True)
    return proc.returncode, command, (proc.stdout + proc.stderr).strip()


def build_context_pack(cell: Cell, req: RenderRequest, entries: List[Dict[str, Any]], task_rel: Optional[str],
                       extra_ids: List[str], include_entry: bool,
                       allow_draft: bool = False) -> Tuple[str, Dict[str, Any]]:
    if not task_rel and req.role == "executor":
        raise InputError("an executor context pack needs --task (the persisted task to execute)")
    by_id = {e["id"]: e for e in entries}
    wanted: List[str] = []
    task_text = ""
    if task_rel:
        task_path = cell.root / task_rel
        if not task_path.is_file():
            raise InputError(f"task not found: {task_rel}")
        task_text = task_path.read_text(encoding="utf-8")
        wanted = task_procedure_ids(task_text, list(by_id))
    missing: List[str] = []
    for pid in extra_ids:
        if pid in by_id:
            if pid not in wanted:
                wanted.append(pid)
        else:
            missing.append(f"{pid}: not an available procedure in this Cell (not installed, not active, or unknown)")
    check_line = "not applicable (no task in this pack)"
    check: Dict[str, Any] = {"ran": False}
    if task_rel:
        code, command, output = run_task_check(cell, task_rel)
        check = {"ran": code is not None, "command": command, "exit_code": code, "output": output}
        if code is None:
            check_line = "none named in the Cell profile (task_check) — run the Cell's own check before starting"
        elif code == 0:
            check_line = f"`{command}` -> exit 0, READY for execution"
        else:
            check_line = f"`{command}` -> exit {code}, NOT READY: a draft, not executable"
            if req.role in ("executor", "both") and not allow_draft:
                raise HandoffRefused(
                    f"handoff refused: {task_rel} does not pass the Cell's format check ({command}, exit {code}); "
                    "an executor pack is only built for a ready task. Resolve the open items (technical fields: "
                    "the check's --fix, if it offers one; content, IDs or approvals: the planner or decision owner) "
                    "or build a planning pack with --role planner.\n" + output
                )
    block, report = render_within_budget(cell, req, entries)
    head_proc = subprocess.run(["git", "-C", str(cell.root), "rev-parse", "HEAD"], capture_output=True, text=True)
    head = head_proc.stdout.strip() if head_proc.returncode == 0 else "unknown (not a Git checkout)"
    parts: List[Tuple[str, str]] = [("INSTRUCTIONS (rendered block)", block)]
    if include_entry:
        for rel in cell.profile["session_entry"]:
            path = cell.root / str(rel)
            parts.append((f"FILE {rel} (sha256 {sha256_file(path)[:16]})", path.read_text(encoding="utf-8")))
    template_rel = cell.task_template()
    routed = [e for e in entries if e["source"] in report.get("routed_sources", [])]
    if routed:
        parts.append(("PROCEDURE INDEX — full entries of the groups the block above routes via a sub-index",
                      "\n".join(format_entry(e) for e in routed)))
    if req.role in ("planner", "both"):
        if not template_rel:
            missing.append("task template: the Cell profile names none (task_template) — ask for the Cell's task format")
        elif not (cell.root / template_rel).is_file():
            missing.append(f"task template {template_rel}: named in the Cell profile but missing")
        else:
            path = cell.root / template_rel
            parts.append((f"TASK TEMPLATE {template_rel} (sha256 {sha256_file(path)[:16]}, "
                          f"{git_blob_state(cell, template_rel)}) — the current format for a new task",
                          path.read_text(encoding="utf-8")))
    if task_rel:
        parts.append((f"TASK {task_rel} (sha256 {sha256_file(cell.root / task_rel)[:16]}; format check: {check_line})",
                      task_text))
    for pid in wanted:
        e = by_id[pid]
        path = cell.root / e["path"]
        parts.append((f"PROCEDURE {pid} {e['path']} (sha256 {e['sha256'][:16]}, package {e['package']})",
                      path.read_text(encoding="utf-8")))
    header = (
        f"=== CONTEXT PACK — {fact(req, 'cell_name', 'unresolved')} ({fact(req, 'repository', 'unresolved')}) ===\n"
        f"Git HEAD at pack time: {head}. Procedure index {index_version(entries)}. Role: {req.role}.\n"
        "persisted: false — this pack is a copy. The Cell's Git state wins over it.\n"
        "Everything you need to act on is below; a path mentioned but not included is NOT loaded:\n"
        "ask for it instead of assuming its content.\n"
    )
    if task_rel:
        header += f"Task format check at pack time: {check_line}.\n"
    body = header + "".join(f"\n--- {title} ---\n{content.rstrip()}\n" for title, content in parts)
    if missing:
        body += "\n--- NOT INCLUDED ---\n" + "\n".join(f"- {m}" for m in missing) + "\n"
    body += "\n=== END OF CONTEXT PACK ===\n"
    meta = {
        "parts": [{"title": t, **measure(c)} for t, c in parts],
        "task_template": template_rel if req.role in ("planner", "both") and template_rel else None,
        "task_check": check,
        "procedures_included": wanted,
        "not_included": missing,
        "measure": measure(body),
        "block_report": report,
    }
    return body, meta


def profile_json(cell: Cell, req: RenderRequest, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "schema": "bcos-cell-instruction-profile/1",
        "renderer_version": RENDERER_VERSION,
        "cell": {k: req.facts.get(k) for k in ("cell_name", "repository", "target_path") if req.facts.get(k)},
        "core": {"path": cell.rel(cell.core_path), "sha256": sha256_text(cell.core_text)},
        "profile": {"path": cell.rel(cell.profile_path), "sha256": sha256_text(cell.profile_text)},
        "session_entry": cell.profile["session_entry"],
        "task_path": cell.profile["task_path"],
        "task_template": cell.profile.get("task_template"),
        "task_check": cell.task_check() or None,
        "routing": cell.profile["routing"],
        "closing_record": cell.profile["closing_record"],
        "capability_classes": ["local-worker", "git-only-worker", "chat-reviewer", "read-only-observer", "automation"],
        "capability_rule": "classify from actual access; never from product, model, provider or role",
        "host": {"surface": req.surface, "role": req.role, "declared_caps": req.caps,
                 "undeclared_means": "unavailable"},
        "procedure_index": {"version": index_version(entries),
                            "file": cell.rel(cell.procedure_index_file()) if cell.index_persisted() else None,
                            "entries": [{k: e[k] for k in ("id", "title", "kind", "use_when", "not_when", "phase",
                                                            "path", "package", "status", "version", "sha256")}
                                        for e in entries]},
        "loading_rule": "an index entry is not loaded content; load the full procedure before applying it",
    }


# --------------------------------------------------------------------------
# Check (validator entry point)
# --------------------------------------------------------------------------


def receipt_packages(root: Path) -> Optional[List[str]]:
    receipt = root / ".installation" / "TEAMCELL-INSTALLATION-RECEIPT.yaml"
    if not receipt.is_file():
        return None
    ids = re.findall(r"^\s*-?\s*package_id:\s*\"?([A-Za-z0-9_.-]+)\"?\s*$", receipt.read_text(encoding="utf-8"), re.M)
    return ids or None


def run_check(cell: Cell) -> Tuple[List[str], List[str], str]:
    fails: List[str] = []
    warns: List[str] = []
    fails.extend(cell.check_profile_paths())
    entries, excluded, errors = cell.collect_procedures()
    fails.extend(errors)
    if not cell.index_persisted():
        warns.append("Cell profile sets procedure_index: none — no persisted Procedure Index to compare; "
                      "rendered snapshots can only be checked by re-rendering")
        index_file = None
    else:
        index_file = cell.procedure_index_file()
    rel_index = cell.rel(index_file) if index_file else "none"
    if index_file is None:
        pass
    elif not index_file.is_file():
        fails.append(f"procedure index file missing: {rel_index}")
    else:
        current = extract_index_section(index_file.read_text(encoding="utf-8"))
        if current is None:
            fails.append(f"procedure index section missing in {rel_index} (run: python3 scripts/render-instructions.py index --write)")
        elif current != render_index_section(entries):
            fails.append(f"procedure index in {rel_index} is out of date with the procedure files (run: python3 scripts/render-instructions.py index --write)")
    for sub in sorted({e["sub_index"].split("#", 1)[0] for e in entries if e["sub_index"]}):
        if not (cell.root / sub).exists():
            fails.append(f"procedure sub-index {sub} named in the Cell profile does not exist")
    installed = receipt_packages(cell.root)
    if installed is not None:
        for e in entries:
            if e["package"] not in installed and not e["package"].startswith(("host:", "repo")):
                fails.append(f"procedure {e['id']} belongs to package {e['package']} which the installation receipt does not list")
    for path in generated_files(cell):
        rel = cell.rel(path)
        text = path.read_text(encoding="utf-8")
        fields, _, _ = split_frontmatter(text)
        block = extract_block(text)
        if block is None:
            fails.append(f"generated instructions {rel} lost its paste block markers")
            continue
        if sha256_text(block) != fields.get("render_block_sha256"):
            fails.append(f"generated instructions {rel} were edited by hand (paste block differs from its render hash); change the core/profile/facts and re-render instead")
            continue
        try:
            inputs = json.loads(fields.get("render_inputs") or "{}")
            req = request_from_inputs(inputs)
        except (ValueError, InputError) as exc:
            fails.append(f"generated instructions {rel} have unreadable render_inputs: {exc}")
            continue
        m = measure(block)
        if req.char_limit and budget_value(m) > req.char_limit:
            fails.append(f"generated instructions {rel} exceed the {req.surface} hard limit {req.char_limit} ({budget_value(m)})")
        elif req.char_target and budget_value(m) > req.char_target:
            warns.append(f"generated instructions {rel} are over the {req.surface} target {req.char_target} ({budget_value(m)})")
        if source_hash(cell, entries, req.inputs()) != fields.get("render_source_sha256"):
            warns.append(f"generated instructions {rel} are stale (core, profile, procedure index or renderer changed); run: python3 scripts/render-instructions.py refresh — then re-paste; app activation stays self-reported")
    summary = (f"{len(entries)} procedure(s) indexed (index {index_version(entries)}), "
               f"{len(excluded)} not available, {len(generated_files(cell))} generated instruction file(s) checked")
    return fails, warns, summary


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_facts(pairs: List[str]) -> Dict[str, str]:
    facts: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise InputError(f"--fact needs key=value, got {pair!r}")
        key, value = pair.split("=", 1)
        if key not in FACT_KEYS:
            raise InputError(f"unknown fact {key!r} (known: {', '.join(FACT_KEYS)})")
        facts[key] = value
    return facts


def add_render_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--surface", default="generic", choices=SURFACES)
    p.add_argument("--role", default="both", choices=ROLES)
    p.add_argument("--caps", default=None,
                   help="comma-separated declared host capabilities; 'none' = none available; omit = undeclared")
    p.add_argument("--fact", action="append", default=[], help="Cell fact key=value (repeatable)")
    p.add_argument("--char-target", type=int, default=None)
    p.add_argument("--char-limit", type=int, default=None)


def request_from_args(args: argparse.Namespace) -> RenderRequest:
    caps = None
    if args.caps is not None:
        caps = [] if args.caps.strip() in ("", "none") else [c.strip() for c in args.caps.split(",") if c.strip()]
    return RenderRequest(args.surface, args.role, caps, parse_facts(args.fact), args.char_target, args.char_limit)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Render this Cell's instructions from the shared core.")
    p.add_argument("--root", default=None, help="Cell root (default: parent of this script's directory)")
    p.add_argument("--profile", default=str(DEFAULT_PROFILE))
    p.add_argument("--core", default=str(DEFAULT_CORE))
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("index")
    s.add_argument("--write", action="store_true")

    s = sub.add_parser("block")
    add_render_args(s)
    s.add_argument("--report", default=None, help="write the JSON budget report here")

    s = sub.add_parser("generate")
    add_render_args(s)
    s.add_argument("--surfaces", default="", help="comma-separated app surfaces to write activation notes for")

    sub.add_parser("refresh")

    s = sub.add_parser("context-pack")
    add_render_args(s)
    s.add_argument("--task", default=None,
                   help="persisted task to execute; required for --role executor, optional for planner/both")
    s.add_argument("--allow-draft", action="store_true",
                   help="include a task that fails the format check (marked NOT READY) instead of refusing")
    s.add_argument("--procedure", action="append", default=[])
    s.add_argument("--no-entry-files", action="store_true")
    s.add_argument("--token-budget", type=int, default=None)
    s.add_argument("--reserve-response", type=int, default=0)
    s.add_argument("--reserve-task", type=int, default=0)
    s.add_argument("--tokenizer-cmd", default=None)
    s.add_argument("--report", default=None)

    s = sub.add_parser("profile-json")
    add_render_args(s)

    s = sub.add_parser("fill")
    add_render_args(s)
    s.add_argument("--template", required=True)

    sub.add_parser("check")
    return p


def main(argv: List[str]) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    try:
        cell = Cell(root, Path(args.profile), Path(args.core))
        if args.command == "check":
            fails, warns, summary = run_check(cell)
            for message in fails:
                print(f"FAIL: {message}")
            for message in warns:
                print(f"WARN: {message}")
            print(f"SUMMARY: {summary}")
            return EXIT_FAIL if fails else EXIT_OK

        entries, excluded, errors = cell.collect_procedures()
        if errors:
            for message in errors:
                print(f"ERROR: {message}", file=sys.stderr)
            return EXIT_INPUT

        if args.command == "index":
            if args.write:
                changed = write_index(cell, entries)
                print(f"{'updated' if changed else 'unchanged'}: {cell.rel(cell.procedure_index_file())} "
                      f"(index {index_version(entries)}, {len(entries)} procedure(s))")
                for note in excluded:
                    print(f"not indexed: {note}")
            else:
                sys.stdout.write(render_index_section(entries))
            return EXIT_OK

        if args.command == "refresh":
            refreshed = 0
            for path in generated_files(cell):
                fields, _, _ = split_frontmatter(path.read_text(encoding="utf-8"))
                req = request_from_inputs(json.loads(fields.get("render_inputs") or "{}"))
                text, report = render_project_file(cell, req, entries)
                path.write_text(text, encoding="utf-8")
                refreshed += 1
                print(f"refreshed: {cell.rel(path)} — {budget_line(report)}")
            if not refreshed:
                print("no generated instruction files found")
            return EXIT_OK

        req = request_from_args(args)

        if args.command == "block":
            block, report = render_within_budget(cell, req, entries)
            sys.stdout.write(block)
            print(budget_line(report), file=sys.stderr)
            if args.report:
                Path(args.report).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return EXIT_OK

        if args.command == "generate":
            out_dir = cell.root / GENERATED_DIR
            out_dir.mkdir(parents=True, exist_ok=True)
            text, report = render_project_file(cell, req, entries)
            (cell.root / PROJECT_OUT).write_text(text, encoding="utf-8")
            print(f"Generated: {cell.rel(cell.root / PROJECT_OUT)}")
            print(budget_line(report))
            surfaces = [s.strip() for s in args.surfaces.split(",") if s.strip()]
            for surface in surfaces:
                if surface not in APP_SURFACES:
                    raise InputError(f"unknown app surface {surface!r}")
                template = cell.root / "templates" / f"APP-INSTRUCTIONS-{surface}.template.md"
                out = out_dir / f"APP-INSTRUCTIONS-{surface}.md"
                out.write_text(fill_template(template.read_text(encoding="utf-8"), cell, req), encoding="utf-8")
                print(f"Generated: {cell.rel(out)}")
            first_run = cell.root / FIRST_RUN_TEMPLATE
            if surfaces and first_run.is_file():
                out = cell.root / FIRST_RUN_OUT
                out.write_text(fill_template(first_run.read_text(encoding="utf-8"), cell, req), encoding="utf-8")
                print(f"Generated: {cell.rel(out)}")
            return EXIT_OK

        if args.command == "fill":
            template = Path(args.template)
            template = template if template.is_absolute() else cell.root / template
            sys.stdout.write(fill_template(template.read_text(encoding="utf-8"), cell, req))
            return EXIT_OK

        if args.command == "profile-json":
            print(json.dumps(profile_json(cell, req, entries), indent=2, ensure_ascii=False))
            return EXIT_OK

        if args.command == "context-pack":
            pack, meta = build_context_pack(cell, req, entries, args.task, args.procedure, not args.no_entry_files,
                                            args.allow_draft)
            tokens, method = estimate_tokens(pack, args.tokenizer_cmd)
            meta["tokens"] = {"count": tokens, "method": method}
            refused = False
            if args.token_budget is not None:
                available = args.token_budget - args.reserve_response - args.reserve_task
                meta["tokens"].update({"budget": args.token_budget, "reserve_response": args.reserve_response,
                                       "reserve_task": args.reserve_task, "available_for_pack": available,
                                       "within_budget": tokens <= available})
                refused = tokens > available
            if args.report:
                Path(args.report).write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            if refused:
                print(f"REFUSED: context pack needs {tokens} tokens ({method}) but only "
                      f"{meta['tokens']['available_for_pack']} are available after reserves; nothing was cut. "
                      "Parts: " + "; ".join(f"{p['title']}: {p['utf8_bytes']} bytes" for p in meta["parts"]),
                      file=sys.stderr)
                return EXIT_BUDGET
            sys.stdout.write(pack)
            print(f"context pack: {tokens} tokens ({method}); procedures included: "
                  f"{', '.join(meta['procedures_included']) or 'none'}", file=sys.stderr)
            return EXIT_OK
    except HandoffRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return EXIT_NOT_READY
    except BudgetRefused as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        print(json.dumps(exc.report, indent=2, ensure_ascii=False), file=sys.stderr)
        return EXIT_BUDGET
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_INPUT
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
