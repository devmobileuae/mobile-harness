# mobile-harness

A Claude Code plugin for running a small mobile studio (iOS, Android/KMP, growth and content) with
Claude agents as the team:

- **Skills**: working methods for mobile engineering, releases, ASO, app sites, analytics, design rounds
  and short-form content. Each rule says why it exists.
- **Role agents** with narrow jobs and narrow tool access.
- **Conclave**: a multi-round debate between agents for decisions that have no single right answer.
- **Delivery workflows** for mobile features, content series and the skill audit.
- **Evals** that turn a past mistake into a regression test, scored *with vs without* the skill.

The plugin is generic. Your apps, IDs, keys and your own case history live in a git-ignored `local/`
folder that `setup` fills (see below).

```
mobile-harness/
├── .claude-plugin/   plugin.json + marketplace.json (one-command install)
├── skills/           skills + registry.yaml (owner, reviewed, born_from, eval globs)
├── agents/           17 agents: mobile, growth, conclave debaters, audit
├── workflows/        conclave · feature-delivery · reel-pipeline · skill-audit
├── evals/            cases in `claude plugin eval` format (prompt.md + graders/)
├── scripts/          run_evals.py (with/without runner) · check_registry.py (CI gate) · setup.py
├── local.example/    template for your git-ignored local/ (links, IDs, keys)
└── docs/             EVALS · FLOWS · SKILL-REVIEW-RESEARCH · examples/
```

## Install

```bash
git clone <this repo> mobile-harness && cd mobile-harness
pip install -r requirements.txt
claude plugin marketplace add "$PWD"
claude plugin install mobile-harness@borodin-harness --scope user
```

For development without installing: `claude --plugin-dir <path to the clone>`.
Skills are invoked as `/mobile-harness:<skill>`, workflows as `/mobile-harness:<workflow>` or with
`Workflow({scriptPath})`.

## Setup: your apps, IDs and keys

Skills never name a specific app. When one needs a value, it reads it from `local/`, which git ignores:

- `local/apps.yaml`: one block per app (platforms, repo path, bundle ID, store and site links, App Store
  Connect / PostHog / RevenueCat / Firebase / Vercel / Figma IDs, social handles);
- `local/secrets.env`: API keys and tokens, and paths to key files;
- `local/skills/<skill>/`: your own case notes. Skills append the outcome of each design round, incident
  or audit there and read it first next time, so they learn your preferences privately.

To fill it, ask Claude Code in the repo "set up the harness for my apps" (the `setup` skill asks about
your apps and never asks you to paste a key into chat), or run:

```bash
python3 scripts/setup.py                         # add apps interactively
python3 scripts/setup.py --check                 # what is filled, what is empty
python3 scripts/setup.py --get myapp.posthog_project_id
```

Details: [local.example/README.md](local.example/README.md). `scripts/check_private.py` blocks personal
values: in CI it checks generic patterns (home paths, keys and tokens, store / RevenueCat / Vercel / Figma
id formats); on your machine, as a pre-commit hook (`python3 scripts/check_private.py --install-hook`), it
also checks every value in `local/apps.yaml` and the names in `local/private-terms.txt`.

## Skills in this plugin

| Skill | What it does | Why it exists |
|---|---|---|
| `setup` | Fills `local/` with your apps, IDs and keys; keeps personal values out of the repo | one plugin, many users' apps |
| `conclave` | Multi-round role debate with mandatory self-doubt; the verdict keeps the dissent | one model anchors on its first answer |
| `frame-qa` | Gate before any visual ships: anatomy, safe zones, voice-over vs frame, covers | generated frames ship with extra fingers and text under platform UI |
| `mobile-feature-delivery` | Feature from criteria to a build verified on device; risk tiers; migration traps | a schema change without migration crashes upgrade installs |
| `agent-orchestration` | Splitting work across agents, briefs, stall recovery, verifying reports | parallel agents stall and report work they did not do |
| `metric-iteration` | One change, one metric with a baseline, a read-out, the next change | redesign rounds that ship nothing |
| `design-review` | Taste rules: lean screens, concentric radii, one icon set, anti-slop | screens get overloaded one label at a time |
| `session-handoff` | Handoff doc, spec and memory pointers for a fresh session | long chats lose state between sessions |
| `eval-driven-skills` | Incident → failing eval case → skill edit → regression run | rules that are never tested never fire |
| `skill-audit` | Every line of a skill proves its place or is deleted | skills only grow |
| `mobile-design-iteration` | Figma rounds: real-app references in the file, small rounds, explicit picks | big concept rounds with no pick |
| `aso-playbook` | Cheap keyword stack, metadata rules, real-UI screenshots, Apple Search Ads stop rules | spend without installs, keywords nobody searches |
| `app-site-seo` | SERP-first keyword picks, page types that rank, content gate, Search Console retargeting | pages that render thin or never get indexed |
| `social-research` | Outlier math (plays ÷ followers, series median), data stack, comment mining | one-hit "formats" copied as trends |
| `social-account-ops` | New-account rules, cadence, formats that distribute, the learning loop | new accounts throttled on day one |
| `app-pulse` | Daily anomaly check across PostHog, RevenueCat and Firebase vs the same weekday | regressions found weeks late |
| `ios-engineering` | How to write iOS here: xcodegen, SwiftData migrations, Swift 6, StoreKit/RevenueCat, analytics facade, widgets, demo seeds, commands, traps | generic framework advice that crashes real installs |
| `android-kmp-engineering` | Android/KMP: modules, DI graph checks, Room migrations, expect/actual seams, push wake, update gate, Play release | KMP and push-wake traps |

## Works with generic skills

The engineering skills say when to override generic framework skills (SwiftData, concurrency,
StoreKit, Room) that give advice which breaks shipped apps. Growth skills complement generic ASO and
content skills with stop rules and measured methods.

## Routines

Suggested scheduled tasks (Claude desktop app or any scheduler):
- **Morning pulse**, daily: the `app-pulse` skill checks every app in `local/apps.yaml` and writes
  `reports/pulse/<date>.md` with a one-line-per-app digest.
- **Skill audit**, twice a month: the registry gate, the with/without evals, a prosecutor-vs-defender
  audit of a few skills, and edits on a local `audit/<date>` branch for approval.

## MCP servers

The tools agents actually call — Figma, AppKittie, Northstar, PostHog, RevenueCat, Firebase,
Supabase, Vercel, Higgsfield, ElevenLabs, vidIQ, Claude in Chrome — with what each is for
and its limits (credits, quotas, quirks): [docs/MCP.md](docs/MCP.md).

## Workflows

Details and diagrams: [docs/FLOWS.md](docs/FLOWS.md).

- **Conclave**: isolated openings, then rounds. In each round every role steelmans, doubts its
  *own* position, attacks or concedes by argument id, and updates with `moved_by`. A moderator
  tracks cruxes, a red team attacks the verdict, and the verdict ships with the dissent and its
  reverse-if conditions. A real run with a retro is in
  [docs/examples/conclave-kmp-port-vs-ios-growth.md](docs/examples/conclave-kmp-port-vs-ios-growth.md).
- **Feature delivery**: a risk-tier plan, iOS and Android engineers on slices of 1–3 files in
  dependency order (a slice whose dependency failed is skipped), a reviewer who sees only the diff,
  simulator/emulator QA with an upgrade install. Blockers and any criterion that is not PASS go back
  to the engineers for up to two fix rounds; a missing review or QA result counts as not ready.
- **Reel pipeline**: research, then a conclave picks the hypothesis, N scenarios, an adversarial
  script review, and the frame-QA gate.
- **Skill audit**: registry freshness, with/without evals, prosecutor vs defender per line, and a
  judge's ruling.

## Evals

What they are and how I use them: [docs/EVALS.md](docs/EVALS.md).

```bash
python3 scripts/check_registry.py                    # gate: freshness, evals exist, size
python3 scripts/run_evals.py --runs 1 -j 6           # whole suite, WITH vs WITHOUT, delta
python3 scripts/run_evals.py --tag frame-qa --runs 3 # one skill, 3 runs
claude plugin eval . --ablation with-without         # official runner (early access)
```

CI (`.github/workflows/ci.yml`) runs the registry gate, frontmatter parsing, Python and workflow syntax
checks and the personal-data scan on every push. Eval runs cost money and need a Claude login, so they
run locally, not in CI.

### Status and known gaps

- **Coverage**: 38 cases, at least two positive cases per skill plus negatives; the registry gate requires
  two positives per skill. The second positive case of each skill has not been run yet.
- **Not every skill meets its own targets** (score ≥ 0.9, Δ > 0.2). In the last runs the frame-QA
  narration case had Δ 0 (a generic skill already catches the same flaws), the keyword-field case
  Δ −0.25 and the Figma references case Δ 0. Most cases ran once (k = 1), which is noise for Δ < 0.3.
- The runner never scores a crashed `claude` run: it is reported as an error and excluded, so a negative
  case cannot pass on an empty run.

The first real run caught a "protection" that never fired. The SwiftData-migration rule existed, but a
generic skill out-competed its trigger, and the model produced exactly the code that crashes upgrade
installs. Score 0.0, fixed in the trigger, not the rule text. That is the case for evals in one sentence.

## Principles

1. **Every rule was born from an incident** and says why it exists (`born_from`, `<!-- why: -->`).
2. **A rule without a test is a hope.** Write the failing eval case first, then edit the skill.
3. **Every line must justify its place.** A monthly prosecutor-vs-defender audit runs; when Δ ≈ 0,
   the line is deleted.
4. **Reviewers never see the author's reasoning.** Judges and reviewers get the code or diff, with
   read-only tools.
5. **An agent's report is a claim, not proof.** The lead re-runs the build and the tests.
6. **The human decides.** The conclave advises and keeps the dissent on record.

