export const meta = {
  name: 'feature-delivery',
  description: 'Mobile feature from criteria to verified build: plan slices, implement per platform in parallel (iOS + Android/KMP), fresh review, simulator QA, release checklist',
  whenToUse: 'A feature that touches several files or both platforms. args: {repo, feature, criteria: [..], platforms: ["ios","android"], baseBranch?}',
  phases: [
    { title: 'Plan', detail: 'risk tiers, slices of 1–3 files, metric' },
    { title: 'Build', detail: 'engineer agent per slice in dependency waves; fix rounds' },
    { title: 'Review', detail: 'fresh reviewer per platform, diff only' },
    { title: 'Verify', detail: 'simulator/emulator QA + upgrade install' },
  ],
}

const A = args || {}
if (!A.repo || !A.feature || !A.criteria) throw new Error('args: {repo, feature, criteria[], platforms[]}')
const PLATFORMS = A.platforms || ['ios']

const PLAN = {
  type: 'object',
  properties: {
    metric: { type: 'string' },
    slices: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, platform: { type: 'string', enum: ['ios', 'android', 'shared'] }, files: { type: 'array', items: { type: 'string' } }, tier: { type: 'string', enum: ['core', 'ui'] }, goal: { type: 'string' }, done_check: { type: 'string' }, depends_on: { type: 'array', items: { type: 'string' } } }, required: ['id', 'platform', 'files', 'tier', 'goal', 'done_check'] } },
    traps: { type: 'array', items: { type: 'string' } },
  },
  required: ['slices', 'traps'],
}
const REPORT = { type: 'object', properties: { slice: { type: 'string' }, built: { type: 'boolean' }, tests: { type: 'string' }, files_changed: { type: 'array', items: { type: 'string' } }, unverified: { type: 'array', items: { type: 'string' } } }, required: ['slice', 'built', 'files_changed', 'unverified'] }
const FINDINGS = { type: 'object', properties: { findings: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, line: { type: 'number' }, severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, what_breaks: { type: 'string' }, trigger: { type: 'string' } }, required: ['file', 'severity', 'what_breaks'] } } }, required: ['findings'] }
const QA = { type: 'object', properties: { rows: { type: 'array', items: { type: 'object', properties: { criterion: { type: 'string' }, result: { type: 'string', enum: ['PASS', 'FAIL', 'NOT CHECKED'] }, evidence: { type: 'string' } }, required: ['criterion', 'result', 'evidence'] } }, upgrade_install: { type: 'string' } }, required: ['rows', 'upgrade_install'] }

phase('Plan')
const plan = await agent(
  `Repo: ${A.repo}. Feature: ${A.feature}\nAcceptance criteria:\n- ${A.criteria.join('\n- ')}\nPlatforms: ${PLATFORMS.join(', ')}.\nRead the repo CLAUDE.md (risk table) and the code the feature touches. Produce slices of 1–3 files each, one writer per file, tier core/ui per the risk table, a done_check each slice must pass (build command / test name), depends_on only when unavoidable. List platform traps that apply (SwiftData/Room schema changes need optional attrs or migration + migration test; xcodegen project.yml; Swift 6 isolation; KMP commonMain boundaries). Name the metric this feature should move. Do not write code.`,
  { label: 'planner', phase: 'Plan', schema: PLAN },
)
log(`${plan.slices.length} slices; traps: ${plan.traps.join(' | ')}`)

// Build in dependency order: each wave holds the slices whose dependencies all built in earlier waves.
// A slice whose dependency failed is skipped, never run on top of a broken base.
phase('Build')
const brief = s => `Repo ${A.repo}. Implement slice ${s.id} (${s.platform}, tier ${s.tier}): ${s.goal}\nFiles (touch only these): ${s.files.join(', ')}\nDone check: ${s.done_check}\nTraps: ${plan.traps.join('; ')}\nCore tier: tests first. Build after every file. Write docs/agent-reports/${s.id}.md and return the report.`
const engineer = p => (p === 'android' ? 'mobile-harness:android-engineer' : 'mobile-harness:ios-engineer')
const run = s => agent(brief(s), { label: `build:${s.id}`, phase: 'Build', schema: REPORT, ...(A.useAgentTypes ? { agentType: engineer(s.platform) } : {}) })

const ids = new Set(plan.slices.map(s => s.id))
for (const s of plan.slices) for (const d of s.depends_on || []) if (!ids.has(d)) throw new Error(`slice ${s.id} depends on unknown slice ${d}`)
const built = new Set(), failedIds = new Set(), reports = []
let pending = [...plan.slices]
while (pending.length) {
  const blocked = pending.filter(s => (s.depends_on || []).some(d => failedIds.has(d)))
  for (const s of blocked) { failedIds.add(s.id); reports.push({ slice: s.id, built: false, files_changed: [], unverified: [`skipped: dependency failed (${s.depends_on.join(', ')})`] }) }
  pending = pending.filter(s => !blocked.includes(s))
  const ready = pending.filter(s => (s.depends_on || []).every(d => built.has(d)))
  if (!ready.length) {
    if (pending.length) throw new Error(`dependency cycle among slices: ${pending.map(s => s.id).join(', ')}`)
    break
  }
  const wave = await parallel(ready.map(s => () => run(s)))
  ready.forEach((s, i) => {
    const r = wave[i]
    reports.push(r || { slice: s.id, built: false, files_changed: [], unverified: ['agent returned nothing'] })
    if (r && r.built) built.add(s.id); else failedIds.add(s.id)
  })
  pending = pending.filter(s => !ready.includes(s))
}
const failed = reports.filter(r => !r.built)
if (failed.length) {
  // Review and QA on a tree that does not build only burn agents; stop and report.
  log(`${failed.length} slice(s) did not build, stalled or were skipped — stopping before review and QA.`)
  return { metric: plan.metric, slices: reports, reviewFindings: [], qa: {}, blocking: failed.map(r => `${r.slice}: did not build (${(r.unverified || []).join('; ')})`), status: 'NOT READY' }
}

const review = (p, round) => agent(
  `Review the uncommitted diff in ${A.repo} for platform ${p} only (git diff). You get the diff and the criteria, not the author's reasoning.\nCriteria:\n- ${A.criteria.join('\n- ')}\nCheck in order: upgrade crashes (schema changes without migration), concurrency/main-thread, lifecycle, money paths (restore/entitlements), permissions/privacy strings, store-policy risks. Each finding needs file:line, what breaks and a concrete trigger. No style nits.`,
  { label: `review:${p}:r${round}`, phase: 'Review', schema: FINDINGS, ...(A.useAgentTypes ? { agentType: 'mobile-harness:mobile-reviewer' } : {}) },
)
const verify = (p, round) => agent(
  `Build and launch the ${p} app from ${A.repo} on the ${p === 'ios' ? 'iOS Simulator' : 'Android emulator'}. Walk each criterion as a user and screenshot it; also dark mode, largest text, empty/offline state, and an upgrade install over the previous release build with existing data. NOT CHECKED is never rounded up to PASS.\nCriteria:\n- ${A.criteria.join('\n- ')}`,
  { label: `qa:${p}:r${round}`, phase: 'Verify', schema: QA, ...(A.useAgentTypes ? { agentType: 'mobile-harness:qa-verifier' } : {}) },
)
// What still blocks a platform: a missing review or QA result, blocker findings, any criterion not PASS.
const problems = (p, rv, q) => {
  const out = []
  if (!rv) out.push('review agent returned nothing')
  else out.push(...rv.findings.filter(f => f.severity === 'blocker').map(f => `blocker ${f.file}:${f.line ?? '?'} ${f.what_breaks}`))
  if (!q) out.push('QA agent returned nothing')
  else out.push(...q.rows.filter(r => r.result !== 'PASS').map(r => `${r.result}: ${r.criterion} (${r.evidence})`))
  return out
}

// Review + QA, then send what blocks back to the engineers, up to maxRounds fix rounds.
const MAX_ROUNDS = A.maxRounds ?? 2
let reviews = {}, qa = {}, open = {}
for (let round = 0; ; round++) {
  phase('Review')
  const targets = round === 0 ? PLATFORMS : PLATFORMS.filter(p => open[p].length)
  const rv = await parallel(targets.map(p => () => review(p, round)))
  phase('Verify')
  const qv = await parallel(targets.map(p => () => verify(p, round)))
  targets.forEach((p, i) => { reviews[p] = rv[i]; qa[p] = qv[i]; open[p] = problems(p, rv[i], qv[i]) })
  const stillOpen = PLATFORMS.filter(p => open[p].length)
  if (!stillOpen.length || round >= MAX_ROUNDS) break
  log(`round ${round + 1}: fixing ${stillOpen.map(p => `${p} (${open[p].length})`).join(', ')}`)
  phase('Build')
  await parallel(stillOpen.map(p => () => agent(
    `Repo ${A.repo}, platform ${p}. Fix exactly these problems from review and QA, nothing else:\n- ${open[p].join('\n- ')}\nTraps: ${plan.traps.join('; ')}\nBuild after every file. Append what you changed to docs/agent-reports/fix-${p}-r${round + 1}.md and return the report.`,
    { label: `fix:${p}:r${round + 1}`, phase: 'Build', schema: REPORT, ...(A.useAgentTypes ? { agentType: engineer(p) } : {}) },
  )))
}

const blocking = PLATFORMS.flatMap(p => open[p].map(x => `${p}: ${x}`))
return {
  metric: plan.metric,
  slices: reports,
  reviewFindings: PLATFORMS.flatMap(p => (reviews[p] ? reviews[p].findings : [])),
  qa,
  blocking,
  status: failed.length || blocking.length ? 'NOT READY' : 'READY FOR RELEASE CHECKLIST',
}
