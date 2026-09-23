# Teamcell Lite distribution

`bootstrap-kit/` is the installable Teamcell Lite v0.4 template (release candidate 5): the complete
baseline Cell plus the source material of the two optional packages under
`bootstrap-kit/profiles/plus/` (installed only when selected, never copied
into a Cell as `profiles/`).

Do not copy this folder by hand. Install a Cell with the preview-first
installer from the repository root — see `docs/create-a-cell.md`
("Install path") and `docs/teamcell-install-semantics.md`.

`SOURCE-MANIFEST.json` records where the kit and the installer tools came
from, the release `version_label`, every kit file's sha256 and the kit's tree
hash. The installer recomputes the tree hash at preview time and reports
`kit_integrity: verified`, or records the version as
`<version_label>+local-modifications` when the kit was changed locally.

| Package | Installed | Selected with |
|---|---|---|
| `teamcell-lite-baseline` | always | — |
| `teamcell-plus-profile` | optional | `--optional-package teamcell-plus-profile` |
| `team-capability-pack` | optional, selects Plus too | `--optional-package team-capability-pack` |

## License

This kit is MIT-licensed (`../../LICENSE`, `../../LICENSES/MIT.txt`) as part
of the operative Teamcell Lite Cell package. `bootstrap-kit/LICENSE` carries
the same MIT text and ships at the root of every Cell created from it
(baseline package, always installed); the two optional packages under
`bootstrap-kit/profiles/plus/` are covered by that same root `LICENSE` once
installed into a Cell that already carries it (see
`bootstrap-kit/profiles/plus/README.md`).
