# Figma files, pages and key nodes per app — format

Keep the real values for your apps in `local/skills/mobile-design-iteration/env.md` (git-ignored); the
file key itself is the app's `figma_file_key` in `local/apps.yaml`, the team is `shared.figma_team_id`.
Ids only, no tokens. On the Pro plan `get_screenshot` / `get_metadata` share ~200 calls/day; `use_figma` is
unlimited. Node ids drift when pages are reorganised: re-read the page list with `use_figma`
(`figma.root.children.map(p => [p.id, p.name])`) before trusting one.

## <App> (<platform>) — `<figma_file_key>`
https://www.figma.com/design/<figma_file_key> · repo `<repo_path>`

| What | Node |
|---|---|
| Page 1 — never rename it (`html_to_figma` without nodeId lands here) | `0:1` |
| App Store screenshots page | `<id>` |
| Current iteration page / board frame | `<id>` / `<id>` |
| Assets frames (image fills named like their files) | `<id>` |
| Kit holder frame «Build kit source» (hidden) / kit source text / pixel lint text | `<id>` / `<id>` / `<id>` |
| Icon sprite | `<id>` |
| Stored builders (one per screen family) | `<id>` … |
| Style reference phones (calibrate the eye) | `<id>` |
| Main components with many instances (don't restyle for one section) | `<id>` |

Data: the app's `posthog_project_id` from `local/apps.yaml`. Specs: `docs/specs/YYYY-MM-DD-<topic>-design.md`.
Exports: `design/figma-YYYY-MM-DD/*.png`; store sets under `marketing/screenshots/<set>/`. Upload:
`aso-playbook/scripts/listing.py`.

## Two files on purpose (apps with a design system)
- Design system file: pages `01 · Foundations`, `02 · Icons`, `03 · Components`, `05 · Explorations`,
  `06 · Onboarding`. Tokens via `scripts/extract_tokens.py` → `tokens.json`; drift check `make_parity.py` → `parity.js`.
- Store screenshots file: one SECTION per locale, frames at a fixed x-pitch; export the section, slice tiles.
  Why separate: Figma publishes libraries per file; moving components later breaks every instance.

Any Android app with its own design system: build only from the project's real icon drawables and DS radii, never invented ones.
