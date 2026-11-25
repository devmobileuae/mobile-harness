# Porting a shipped Android app to KMP + CMP — what we learned

Source: a faithful full-app port of a multi-module, backend-driven Android app into one KMP codebase
with Compose UI on iOS too (~3 weeks, ~50 commits). An independent judge review said GO-WITH-CONDITIONS:
UI parity strong, testing and production-readiness weak. New features later went to the native repos
instead of the port — a port is not automatically where new work lands. Your own port logs:
`local/skills/android-kmp-engineering/`.

## Method that worked

bulk-copy → de-Android (table in `conventions.md`) → **4 compile gates**
(`:shared:compileKotlinIosSimulatorArm64`, `:shared:compileAndroidMain`, `:composeApp:assembleDebug`,
`:shared:iosSimulatorArm64Test`) → Android device proof → owner's iOS sim QA after every batch.
Subagents only for code-only screen ports; the orchestrator runs the gates itself. Keep a resume file during
the port (`migration/full-port-state.md`) + one handoff prompt per wave.

Keep the Android original reachable for 1:1 diffs: once the in-repo snapshot is deleted, diff with
`git show <snapshot-commit>:<path>`. A separate checkout of the Android repo may be stale — diff against the
shipped tag, not against whatever is on disk.

## Wave order that held up

1. Baseline + foundation: convention plugins, `:shared` skeleton, one thin vertical slice as a PoC.
2. Backend-driven-UI models + mappers; view models / use cases / processors + contracts.
3. The design-system / uikit layer (the biggest single chunk, ~200 files).
4. The universal screen + navigation; one real server page rendered through the real VM (captured fixture) + Ktor.
5. Live nav host + action processors; native auth shell; live network.
6. Durable auth, tab host, OTP; persistence (Room KMP page cache); profile.
7. Platform actuals (WebView, images, push permission, secure storage), theme, review prompt, pickers.
8. Fidelity audit (pair-by-pair against the original), then an independent judge review, then backlog waves.

## The backlog protocol

One file per item (`status/T01`…, `status/D01`…): problem / evidence / approach / DoD, plus a `## Status`
write-back (DONE / BLOCKED + QA instructions) that the worker updates. `STATUS.md` = narrative digest and
answered-questions log; `status/` is the source of truth. Items that stayed open were owner-gated (Firebase,
release signing, payments SDK, keychain attribute migration) or large (DI framework, upper test tiers, iOS runtime QA).

## Faithfulness rules (each one cost a bug)

1. **Diff allow-lists and maps 1:1 against the shipped tag.** A tab-root allow-list had dropped one URL (a whole
   tab vanished); the local-image resolver map had `drawable_onboarding_*` for the real `drawable_onb_*` and ~20
   webps were never copied; two entries were wrongly deleted as "invented".
2. **Port collectors, not just state.** The root VM lacked the `logOutTrigger → ReplaceAction(/auth)` collector;
   a fallback "quit application" event was emitted and never collected.
3. **Port behaviour, not your reading of it.** An empty-refresh-token "fix" inverted Android (strand vs wipe +
   logout); 400/429/599 moved from the silent NETWORK bucket to SERVER and surfaced error UI because the
   port's HTTP exception was not an `IOException`.
4. **Client version is product behaviour.** When the backend gates server-driven UI by the reported client
   versionCode (`X-User-Agent`-style header), a placeholder version shows tabs production does not have.
   Pin it to the shipped Android release; re-pinning is an owner decision.
5. **Platform defaults differ.** Dates were UTC (Android `SimpleDateFormat` is device-local); positional `%1$s`
   args ignored; Android 13+ shows its own copy confirmation (suppress your snackbar there); iOS
   `Dispatchers.IO` import; AOSP email regex.
6. **Things that do not exist in common:** Parcelable (→ SavedState codec), `@color/` in vectors, Paging3 on
   the shared classpath (manual paging + generation token), Android `R.*`.
7. **Existing users' data:** DataStore → multiplatform-settings in place (a `LegacyDataMigrator`); never add
   `kSecAttrAccessible` to queries of existing Keychain items (-25300, reverted).

A registry parity check (resolvers / colours / icons as identical name sets) is cheap and caught nothing
missing once the maps were diffed — run it anyway, it is the proof.
