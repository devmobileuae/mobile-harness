# How big tech and AI labs review prompts and skills

> Collected by a research agent on 2026-11-25. **[S]** — has a source, **[Synthesis]** — a conclusion.
> Links were collected by an agent; open the 2–3 key ones before citing them.

## 1. Instruction ablation

- **[S] Anthropic, July 2026:** >80% was removed from the Claude Code system prompt for Claude 5 models with no measurable loss on coding evals. What was removed: conflicting instructions (found by searching transcripts), crutches for weaknesses of older models, rules that the model's judgment replaces, tool instructions (moved into tool descriptions), the "obvious" from CLAUDE.md. — https://claude.dev/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models/
- **[S, indirect]** The method "delete the whole prompt and add it back line by line, measuring each" is attributed to Boris Cherny (talk https://www.youtube.com/watch?v=qyPCVqFUyDo, retelling https://dev.to/willianpinho/do-your-agent-system-prompts-do-anything-i-measured-19-of-mine-2ek1). Criticism: the diff and evals were not published.
- **[S] Counterexample:** for 15 of 19 agents, replacing the prompt with "You are a helpful assistant" made results worse. Conclusion: general rules get cut with each model, **facts about your environment do not** (the model cannot know them).
- **[S] skill-creator:** each test runs as a "with skill / baseline" pair, and Δ is computed. Assertions that pass even without the skill are marked as non-discriminating. — https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md

## 2. Prompt registries: versions and owners

- **[S] Uber Prompt Engineering Toolkit:** catalog, versions, auto-eval on commit. https://www.uber.com/blog/introducing-the-prompt-engineering-toolkit
- **[S] LinkedIn:** "Prompt Source of Truth", gradual rollout of versions. https://blog.bytebytego.com/p/the-evolution-of-linkedins-generative
- **[S] LangSmith:** commit hashes, `staging`/`production` tags only via promotion, only owners promote. https://docs.langchain.com/langsmith/manage-prompts
- **[S] Braintrust:** a GitHub Action blocks merge on regression; result classes improvement / regression / tradeoff / tie. https://www.braintrust.dev/articles/llm-eval-pipeline-github-actions
- **[S] GitHub Copilot Evals (preview, 2026-11-17):** evals for skills, custom agents and MCP tools before and after a change. https://github.blog/changelog/2026-11-17-github-copilot-evals-is-now-in-public-preview
- **Not found:** scheduled calendar reviews. Everywhere the trigger is an event (commit, PR, model change).

## 3. Eval-driven development

- **[S] Anthropic, "Demystifying evals for AI agents":**
  - capability evals start with a low pass rate, regression evals stay near 100%; mastered cases "graduate" into regression;
  - start with 20–50 tasks from real failures, plus cases where the behavior should not trigger;
  - run on every agent change and every model change; the eval set is a "living artifact" with an owner.
  - https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- **[S] OpenAI:** continuous evaluation on every change. https://developers.openai.com/api/docs/guides/evaluation-best-practices
- **[S] Hamel Husain:** L1 — cheap assertions on every change; L2 — trace review and LLM-judge on a schedule; L3 — A/B. https://hamel.dev/blog/posts/evals/
- **[S] Eugene Yan:** label a small dataset, align the judge to a human, binary labels beat a 1–5 scale. https://eugeneyan.com/writing/product-evals/
- **[S] Shankar et al., "Who Validates the Validators?":** criteria drift — evaluation criteria are refined only after seeing outputs, so judges need review too. https://arxiv.org/abs/2404.12272

## 4. Analogues from classic engineering

- **[S] Google docs freshness:** a document has an `owner` and `reviewed`; after ~3 months without edits an automatic email arrives. When GooWiki was shut down, ~90% of documents had neither views nor edits. https://abseil.io/resources/swe-book/html/ch10.html
- **[S] Google Sensenmann:** finds dead code and sends the owner a CL to delete it — >1000 CLs a week. The main difficulty is cultural. https://testing.googleblog.com/2023/04/
- **[S] Uber Piranha:** automatically removes code for stale feature flags (~2000 flags). https://eng.uber.com/piranha/
- **[S] Fowler, "Feature Toggles":** a removal task is created together with the flag; expiration date; time-bomb test; a limit on the number of flags. https://martinfowler.com/articles/feature-toggles.html
- **[Synthesis] Chesterton's fence vs "prove it or delete it":** every non-trivial line has a recorded reason (an incident or an eval). A line with no reason and no test can be deleted. A line with a reason only if ablation showed that nothing breaks without it.

## 5. Anthropic on Agent Skills

- **[S]** "The context window is a public good". Ask of every paragraph: "Does this paragraph justify its token cost?" SKILL.md < 500 lines; dated material goes in an "Old patterns" section. https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **[S] Evaluation-driven:** run tasks without the skill → collect 3 scenarios → take a baseline → write minimal instructions → iterate; test on Haiku, Sonnet and Opus.
- **[S]** The Claude A / Claude B pairing: one writes the skill, the other uses it. If a bundled file is never read, it may not be needed.
- **[S]** A skill description is optimized on ~20 queries (half should trigger, half are near misses), with a held-out split. ALWAYS/NEVER in caps is a "yellow flag".

## 6. Cadence and deletion criteria (summary)

- **Described cadences:** on every change and on a model change (Anthropic, OpenAI); "on a cadence" (Hamel L2); ~3 months (Google docs).
- **Deletion criteria:**
  - a crutch for an old model;
  - conflicts with another instruction;
  - derivable from the code;
  - "the model already knows";
  - the assertion passes even without the skill;
  - the file is never read;
  - dated.

## How this shaped `skill-audit` [Synthesis]

- `skills/registry.yaml`: owner, `reviewed`, `born_from`, `last_triggered` (Google freshness + LangSmith owners).
- `<!-- why: … -->` on non-trivial lines — Chesterton's fence with a recorded reason.
- Time bomb: CI fails if `reviewed` is older than 90 days (Fowler + Google).
- Limit: a new rule is added only if an old one is removed (Fowler, inventory limit).
- Monthly: telemetry across all skills + deep ablation of 5 skills in rotation, so every skill gets reviewed once a quarter. A full run on a model change.
- Ablation in blocks with bisection (with 3 cases, single-line ablation is statistically weak).
