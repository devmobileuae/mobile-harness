# Per-app env note — format

Your real env notes (repos, bundle ids, ASC/RevenueCat/PostHog ids, sims, tags) live in
`local/skills/mobile-feature-delivery/env.md` and the app's block in `local/apps.yaml`
(`python3 scripts/setup.py --get <key>.<field>`). Credentials (ASC .p8 keys, PostHog tokens, RevenueCat
keys) are never recorded here: ASC creds live in a git-ignored `config.json` next to the app's `asc.py`
or in `local/secrets.env`; ask the owner to copy them.

Keep one block per app in that shape:

```markdown
## <App> — `~/code/<app>`
- Bundle `com.example.<app>`, Team `<apple_team_id>`, ASC app `<asc_app_id>`, iPhone-only, iOS 18, Swift 6.
- Version source: `project.yml` → `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` (current: <ver> / <build>).
- Tags: `<ver>` (commit <sha>); release worktree if any.
- Archives: `build/release/<App>-<ver>-<build>.xcarchive`.
- ASC subscription group `<id>`; product ids → ASC ids.
- RevenueCat project `<revenuecat_project_id>`, app `<id>`, entitlement `premium`, offerings `default` + `recovery`.
- PostHog org + project `<posthog_project_id>`, main dashboard id. The MCP's active project is shared state:
  switch org + project before reading; check `$app_namespace = <release bundle id>`.
- Simulators: test gate name (+ id when the name is ambiguous); store/demo sim.
- Figma `<figma_file_key>`. Site repo + Vercel project; legal URLs (terms / privacy).
- QA list / E2E scope file in the repo.

## <KMP app> (work repo)
- Two Firebase projects (Android + iOS); Remote Config param `remote` → `appUpdate`, feature allow-list.
- Build number source (e.g. `iosApp/Configuration/Config.xcconfig` `CURRENT_PROJECT_VERSION`, both platforms).
- Server-driven UI gated by the reported client versionCode → must equal the shipped release.
```
