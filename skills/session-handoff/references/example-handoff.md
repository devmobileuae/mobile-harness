<!--
Worked example of a full handoff (fictional app: a cycle tracker adding a partner-sharing feature with a small
Cloudflare Worker backend). Shape of a handoff that was resumed from twice without re-discovery. What makes it good:
  - opens with what it SUPERSEDES and what the older doc is still right about;
  - one-paragraph state with numbers measured at handoff;
  - an OWNER checklist split from the agent's resume list, grouped A–E, with exact commands and success signals;
  - a stale artefact named and replaced inline (the plan's smoke-test script);
  - "Resume here" numbered, with ONE UPDATE block on top saying which steps are DONE;
  - "Not verified, do not assume" as its own list, each with how it was observed;
  - owner decisions with his words in quotes, and how he wants to be talked to;
  - "How this was built" (so reviews can be trusted) and verified tooling facts with simulator UDIDs.
Secrets appear by NAME only. Real handoffs of yours go in local/skills/session-handoff/.
-->

# Handoff — 2026-03-10

Read this first in a fresh session. It replaces scrolling the long chat of 2026-03-09…10 and
**supersedes `HANDOFF-2026-03-09.md`** for everything about partner sharing (that file is still
right about the 1.4 bundle and the privacy debt). `docs/` and `.superpowers/` are git-ignored:
everything here exists only on disk.

## One-paragraph state

Partner sharing: **Parts 1–2 (Worker + kit core) are built, reviewed and green. Part 3 (the owner's
side of the app) works end to end on the simulator against a local Worker; two small follow-up fix
batches landed at the very end and have NOT been re-reviewed. Part 4 (the partner's side) is designed
but has no plan and no code. Nothing is deployed, nothing is committed.** Branch `hotfix/1.3`, last
commit `07b2e9a`; the tree also holds the owner's uncommitted 1.4 bundle.

Numbers at handoff (run just now): kit `swift test` → 245; Worker `vitest` → 137 in 10 files, `tsc`
clean; app builds for the simulator.

## Owner checklist (things only he can do)

Nothing here blocks the next coding session (Part 4 is built against `wrangler dev`).

**A. Look and decide** — screenshots in `docs/screenshots/2026-03-10-partner/`; the 24 partner strings
he has not read; "New invite" vs "Create invite" (recommend: "Create invite", verb-first per DESIGN.md).

**B. Deploy the Worker**
1. `cd backend/share-worker && npx wrangler login` (browser).
2. `npx wrangler kv namespace create SHARE_KV` → paste the id into `wrangler.jsonc`.
3. Secrets by name: `npx wrangler secret put RC_WEBHOOK_SECRET`, `RC_API_KEY` (RevenueCat v2 secret key, customer read).
4. Approve `npx wrangler deploy` → note the `*.workers.dev` host.
5. RevenueCat → Integrations → Webhooks: URL `https://<host>/v1/rc`; "Send test event" must show 200.
6. Smoke test — **the script in the plan is stale** (redeem now takes a client-generated token). Use:
   ```bash
   HOST=https://<worker host>; r() { openssl rand -base64 $1 | tr '+/' '-_' | tr -d '='; }
   ID=$(r 16); W=$(r 32)
   curl -s -o /dev/null -w "%{http_code}\n" -X PUT "$HOST/v1/share/$ID" -H "authorization: Bearer $W" -d '{"blob":"x"}'   # 201
   curl -s -o /dev/null -w "%{http_code}\n" -X DELETE "$HOST/v1/share/$ID" -H "authorization: Bearer $W"                # 204
   ```

**C. App + Apple (after B)** — `Info.plist` `ShareAPIHost` = the Worker host; Apple Developer → App ID
(`bundle_id` from `local/apps.yaml`): enable Push Notifications and Associated Domains, add both in Xcode.

**D. Site** — serve `/p` and `/.well-known/apple-app-site-association` (JSON, `Content-Type` header). Not prepared yet.

**E. Before the public release** — privacy policy, FAQ and App Store privacy label must disclose the sharing.

## Resume here

> **UPDATE, second session of 2026-03-10 — steps 1 and 2 are DONE. Start at step 3.** Both follow-ups had landed;
> the scoped re-review found two more Important defects, both fixed test-first. Numbers now: kit 245 · Worker 138.
>
> **Not verified, do not assume:** the 403 → "Forget here" path (read, never run — needs a tampered server); dark
> mode (the app is light-only since `48142fd`, so CLAUDE.md's "light AND dark" line is stale); anything on a device.

1. **Close Part 3.** Ledger `.superpowers/sdd/2026-03-10-partner-part3/progress.md`. Two follow-ups were dispatched at
   the very end — if the files show the changes, they landed; otherwise apply them from the descriptions.
2. **Known limitations from the reviews → write into the spec.**
3. **Part 4 — partner side.** Spec: `docs/superpowers/specs/2026-03-10-partner-ui-design.md`. Process:
   `superpowers:writing-plans` → `superpowers:subagent-driven-development`. Two-simulator check against `wrangler dev`.
4. Site files for D. 5. Copy in all locales, policy, FAQ, store.

## Decisions taken 2026-03-10 (owner, in chat)

- Upload once per app session ("yes, let's do per session"); 12-character code; Pro backfill for existing subscribers.
- He found the pace slow ("are you overthinking again?") — short status notes, pictures, one question with a recommendation.

## How this was built

Every task = implementer → reviewer → fix loop; no commits and no worktrees (owner's rules), so reviewers read files.
Reviews caught KV read-modify-write races and out-of-order webhook events; live simulator runs caught what reviews
cannot (glyph collisions at XXL Dynamic Type, a toast hidden under a sheet).

## Tooling facts (all verified)

- Worker needs Node 24 (`PATH=/opt/homebrew/opt/node@24/bin:$PATH`); KV in tests is isolated per file.
- App build: `-destination 'platform=iOS Simulator,id=<UDID>'` (`name=iPhone 16 Pro` no longer resolves; CLAUDE.md
  still has the old command — the owner was told).
- Local e2e: `npx wrangler dev --port 8799` from Bash, then `xcrun simctl launch <udid> <bundle_id> -ShareAPIHost 127.0.0.1:8799`.
- Toasts live 1.8 s: take burst screenshots, one screenshot after a tap misses them.
