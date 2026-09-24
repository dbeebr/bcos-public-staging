# Security Policy

## Scope

BCOS v0.1 is a documentation and template standard, but this repository also
ships an installable Teamcell Lite Cell package: executable Python and shell
tools (`scripts/`) that write files, install a Cell, and generate a
governance/receipt configuration on the user's own machine. Security concerns
relevant to this release include:

- Installer, renderer or validator behavior that writes outside its declared
  target, mishandles confirmation, or misrepresents what it wrote (see
  `docs/teamcell-install-semantics.md` for the contract it must satisfy)
- Template or example content that inadvertently encourages insecure practices
- Privacy issues in examples that reference real people or organizations
- Documentation that misrepresents the security posture of BCOS-based systems
  or of the shipped installer tools

## Reporting a Security Issue

Avoid putting exploit detail in a public GitHub issue where possible.

This repository does not currently have GitHub's private vulnerability
reporting enabled, and no other confidential channel is configured yet — that
is a disclosed, open gap in this policy, not a feature we are choosing not to
document. Until a confidential channel exists, the least-bad option is a
public GitHub issue with only the minimum detail needed to get a maintainer's
attention (nature of the concern and affected file, not full exploit detail);
ask in the issue for a private follow-up channel before disclosing specifics.

Please still include, once a channel is agreed:

1. The nature of the concern
2. Which file or section is affected
3. The potential impact
4. Any suggested remediation

Maintainers will acknowledge the report within a reasonable timeframe and
coordinate disclosure.

## What This Policy Does Not Cover

- Security of downstream systems built using BCOS patterns (not our responsibility)
- Security of third-party tools, agents, or platforms referenced in examples,
  or of any external app (ChatGPT, Claude, Copilot, Gemini, a local model
  host) a user pastes generated instructions into
- Security of a Cell a user has installed and then modified themselves

## Operational Contact Details

This policy does not include internal contact details, private queues, or
operational access information. BCOS v0.1 is a community project with public
GitHub-based contribution and issue tracking.

## Status

BCOS v0.1 the concept is experimental; this release additionally ships a
real, installable Cell package (see `README.md` "Status"). The security
posture above is scoped to that actual shipped surface — docs, templates and
the installer/renderer/validator tools — not to a docs-only release.
