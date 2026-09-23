#!/usr/bin/env python3
"""Deterministic validator for playbooks/onboarding/SKILL-PLAYGROUND.html.

Checks:
  - the page exists and has exactly six prompt <textarea> blocks (three
    use-case prompts, three skill-improvement prompts), each readonly;
  - each copy button's data-copy-target resolves to a real textarea id;
  - required skill and routing references are present as literal text;
  - no external network dependency (no http(s):// src/href, no CDN,
    no external <script src>, no external <link>);
  - no unresolved {{placeholder}} tokens (this page uses a distinct
    [[VARIABLE: ...]] convention for intentionally team-fillable text);
  - a <noscript> fallback banner and readonly textareas are present, so the
    page remains usable with JavaScript disabled;
  - semantic basics: exactly one <h1>, at least one <h2>, aria-labelledby
    present on prompt textareas, real <button> elements for copy actions;
  - every relative link resolves from the file's own location OR is one of
    the documented install-dependent paths (ONBOARDING.md,
    apps/team-capability-pack/**, apps/brand-brain/**,
    history/learning-candidates/) that only exist once a Cell has the
    Teamcell Plus profile and Team Capability Pack installed — those are
    reported as informational skips, not failures, in a bare template repo.

Exit 0 if every check passes (skips allowed). Exit 1 on any real failure.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_TEXT_REFERENCES = [
    "apps/team-capability-pack/CONTEXT_INDEX.md",
    "REQUIREMENTS-ENGINEERING.skill.md",
    "BUSINESS-ANALYST.skill.md",
    "TEAM-EVENT-PLANNER.skill.md",
    "human-gates/",
    "work/",
    "history/learning-candidates/",
]

EXPECTED_PROMPT_IDS = [
    "prompt-re",
    "prompt-ba",
    "prompt-tep",
    "prompt-review",
    "prompt-local",
    "prompt-upstream",
]

# Paths that only exist once a Cell has installed the Teamcell Plus profile
# and the Team Capability Pack app (see profiles/plus/scripts/*). A bare
# canonical template repo will not have these — that is expected, not a
# defect (same precedent as profiles/plus/ONBOARDING.md.template).
INSTALL_DEPENDENT_PREFIXES = (
    "ONBOARDING.md",
    "apps/team-capability-pack/",
    "apps/brand-brain/",
    "history/learning-candidates/",
)

PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")
HREF_RE = re.compile(r'href="([^"]+)"')
EXTERNAL_RE = re.compile(r'^(https?:)?//|^https?://', re.IGNORECASE)


def fail(issues: list[str], msg: str) -> None:
    issues.append(msg)


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    # Installed-Cell location (team-capability-pack selected) takes
    # precedence; falls back to this template repo's own source_root
    # (packages/PACKAGES.yaml onboarding_source) when run against the
    # template repo directly rather than an installed Cell.
    page = root / "playbooks" / "onboarding" / "SKILL-PLAYGROUND.html"
    if not page.is_file():
        source_page = root / "profiles" / "plus" / "apps" / "team-capability-pack" / "onboarding" / "SKILL-PLAYGROUND.html"
        if source_page.is_file():
            page = source_page
    issues: list[str] = []
    skips: list[str] = []

    if not page.is_file():
        print(f"FAIL: {page} does not exist", file=sys.stderr)
        return 1

    text = page.read_text(encoding="utf-8")

    # Six prompt blocks, each readonly.
    for prompt_id in EXPECTED_PROMPT_IDS:
        pattern = re.compile(
            r'<textarea\s+id="' + re.escape(prompt_id) + r'"[^>]*>', re.DOTALL
        )
        match = pattern.search(text)
        if not match:
            fail(issues, f"missing prompt textarea id={prompt_id!r}")
            continue
        if "readonly" not in match.group(0):
            fail(issues, f"prompt textarea id={prompt_id!r} is not readonly (breaks no-JS fallback safety)")
        if "aria-labelledby" not in match.group(0):
            fail(issues, f"prompt textarea id={prompt_id!r} missing aria-labelledby")

    textarea_ids = set(re.findall(r'<textarea\s+id="([^"]+)"', text))
    if len(textarea_ids & set(EXPECTED_PROMPT_IDS)) != 6:
        fail(issues, f"expected exactly six prompt textareas, found ids: {sorted(textarea_ids)}")

    # Copy buttons resolve to real textarea ids.
    copy_targets = re.findall(r'data-copy-target="([^"]+)"', text)
    if not copy_targets:
        fail(issues, "no copy buttons with data-copy-target found")
    for target in copy_targets:
        if target not in textarea_ids:
            fail(issues, f"copy button targets nonexistent textarea id={target!r}")
    if len(copy_targets) != 6:
        fail(issues, f"expected six copy buttons (one per prompt), found {len(copy_targets)}")

    # All copy buttons are real <button> elements, not divs/spans.
    button_like = re.findall(r'<button[^>]*class="copy-btn"', text)
    if len(button_like) != len(copy_targets):
        fail(issues, "not every copy control is a real <button> element")

    # Required text references.
    for ref in REQUIRED_TEXT_REFERENCES:
        if ref not in text:
            fail(issues, f"required reference not found in page text: {ref!r}")

    # No unresolved {{placeholder}} tokens.
    placeholders = PLACEHOLDER_RE.findall(text)
    if placeholders:
        fail(issues, f"unresolved {{...}} placeholder token(s) found: {placeholders}")

    # No external network dependency.
    if re.search(r'<script[^>]+src=', text):
        fail(issues, "external <script src=...> found (must be inline-only)")
    if re.search(r'<link[^>]+href="https?://', text, re.IGNORECASE):
        fail(issues, "external <link href=...> found (no external fonts/stylesheets allowed)")
    for href in HREF_RE.findall(text):
        if href.startswith("#"):
            continue
        if EXTERNAL_RE.match(href):
            fail(issues, f"external href found (page must have no network dependency for operation): {href!r}")

    # No-JS fallback banner present.
    if "<noscript>" not in text:
        fail(issues, "missing <noscript> fallback banner")

    # Semantic basics.
    if len(re.findall(r"<h1[ >]", text)) != 1:
        fail(issues, "page must have exactly one <h1>")
    if not re.search(r"<h2[ >]", text):
        fail(issues, "page must have at least one <h2>")

    # Reduced-motion / color-scheme awareness (accessibility basics).
    if "prefers-reduced-motion" not in text:
        fail(issues, "no prefers-reduced-motion handling found")

    # Relative link resolution. The page's links are always authored
    # relative to its INSTALLED location (playbooks/onboarding/), even when
    # validated from its source_root location in this template repo
    # (profiles/plus/apps/team-capability-pack/onboarding/) — resolve
    # against the virtual installed base, not the physical file location.
    page_dir = root / "playbooks" / "onboarding"
    for href in HREF_RE.findall(text):
        if href.startswith("#") or EXTERNAL_RE.match(href):
            continue
        clean = href.split("#", 1)[0]
        resolved = (page_dir / clean).resolve()
        if resolved.exists():
            continue
        # normalize to a root-relative string for the install-dependent check
        try:
            root_relative = str((page_dir / clean).resolve().relative_to(root))
        except ValueError:
            root_relative = clean
        root_relative_norm = root_relative.rstrip("/")
        clean_norm = clean.rstrip("/")
        if any(
            root_relative_norm.startswith(p.rstrip("/")) or clean_norm.startswith(p.rstrip("/"))
            for p in INSTALL_DEPENDENT_PREFIXES
        ):
            skips.append(f"SKIP (install-dependent, expected absent in bare template): {href}")
        else:
            fail(issues, f"relative link does not resolve: {href} (resolved: {resolved})")

    for skip in skips:
        print(skip)

    if issues:
        for issue in issues:
            print(f"FAIL: {issue}", file=sys.stderr)
        print(f"Skill Playground validation failed with {len(issues)} issue(s)", file=sys.stderr)
        return 1

    print(f"PASS: Skill Playground validated — 6 prompt blocks, required references present, "
          f"no external network dependency, no unresolved placeholders, no-JS fallback present, "
          f"{len(skips)} install-dependent link(s) skipped as expected in a bare template repo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
