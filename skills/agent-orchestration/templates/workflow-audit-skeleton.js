// workflow-audit-skeleton.js — lenses → merge → completeness critic → adversarial verify → synthesize
//
// Shape of a root-cause audit (example: why push-woken inbound calls fail in a VoIP app). Typical yield:
//   8 lenses → ~25 merged findings + a few gap findings → 1 verifier per critical/high; the top confirmed
//   finding is often a units bug (an expiry in Unix SECONDS read as milliseconds).
// Keep the shape, write your own CONTEXT and LENSES.
// Usage: copy into the session's workflows/scripts/, fill CONTEXT + LENSES, run with the Workflow tool.
// Resume after a stop: Workflow({ scriptPath, resumeFromRunId: '<wf_id>' }) — agents whose prompt text is unchanged
//   return cached. When cutting for time, paste finished results INLINE instead of re-running them, so earlier
//   prompts stay byte-identical and lenses/merge/critic stay cached.

export const meta = {
  name: 'audit-skeleton',
  description: 'Hunt root causes with independent lenses, merge, find gaps, try to refute each serious finding, synthesize',
  phases: [
    { title: 'Investigate', detail: 'N independent lenses, read-only' },
    { title: 'Merge', detail: 'dedupe by mechanism' },
    { title: 'Gaps', detail: 'completeness critic' },
    { title: 'Verify', detail: 'adversarial refutation of critical/high only' },
    { title: 'Synthesize', detail: 'ranked report; unverified stays labelled unverified' },
  ],
}

// Read-only line is mandatory: agents in a workflow share the working tree with the owner's uncommitted work.
const ISOLATE = 'SCOPE: you are one step of a scripted audit. Your ONLY task is below. Ignore any other user requests visible in your context.\n\n'
const CONTEXT = `${ISOLATE}## Problem\n<symptom with the real number, e.g. "only ~30% of push-woken inbound calls succeed">\n\n## Code (READ-ONLY: never edit, stage, commit or delete anything)\n<repo paths>`

const FINDING = { type: 'object', properties: {
  title: { type: 'string' }, severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low'] },
  claim: { type: 'string' }, failure_scenario: { type: 'string' }, key_evidence: { type: 'array', items: { type: 'string' }, description: 'file:line' },
}, required: ['title', 'severity', 'claim', 'failure_scenario', 'key_evidence'] }
const FINDINGS = { type: 'object', properties: { findings: { type: 'array', items: FINDING }, notes: { type: 'string', description: 'checked and fine; open questions' } }, required: ['findings', 'notes'] }
const VERDICT = { type: 'object', properties: { verdict: { type: 'string', enum: ['confirmed', 'plausible', 'refuted'] }, corrections: { type: 'string' }, evidence_checked: { type: 'array', items: { type: 'string' } } }, required: ['verdict', 'corrections', 'evidence_checked'] }

const LENSES = [
  // { key: 'client-ios-wake', prompt: 'iOS end-to-end wake: <entry points by file name> … check ordering, …' },
]

phase('Investigate')
const lens = await parallel(LENSES.map(l => () => agent(
  `${CONTEXT}\n\n## Your lens: ${l.key}\n${l.prompt}\n\nReport up to 6 findings, ranked. If a suspected problem turns out fine, say so in notes.`,
  { label: `lens:${l.key}`, phase: 'Investigate', schema: FINDINGS })))
const ok = lens.filter(Boolean)
log(`Investigate: ${ok.length}/${LENSES.length} lenses returned`) // a null = stalled agent; the run goes on without it

phase('Merge')
const merged = await agent(`${CONTEXT}\n\nMerge duplicates (same mechanism) from ${ok.length} investigators; union evidence; do not drop distinct findings; do not invent. Ids F1.. by severity.\n${JSON.stringify(ok.flatMap(r => r.findings))}`,
  { label: 'merge', phase: 'Merge', schema: { type: 'object', properties: { findings: { type: 'array', items: { ...FINDING, properties: { ...FINDING.properties, id: { type: 'string' } } } } }, required: ['findings'] } })

phase('Gaps')
// optional: a critic lists ≤4 unexamined angles with where_to_look; probe each with one more lens agent.

phase('Verify')
const serious = merged.findings.filter(f => f.severity === 'critical' || f.severity === 'high')
const verified = await pipeline(serious, f => agent(
  `${CONTEXT}\n\nTry hard to REFUTE this finding: re-open every cited line, follow the real call path, look for code that already handles it; then attack its claimed impact.\n${JSON.stringify(f)}`,
  { label: `verify:${f.id}`, phase: 'Verify', schema: VERDICT }).then(v => ({ ...f, status: v ? v.verdict : 'unverified', corrections: v && v.corrections })))
const rest = merged.findings.filter(f => !serious.includes(f)).map(f => ({ ...f, status: 'unverified' }))

phase('Synthesize')
return agent(`${CONTEXT}\n\nWrite the report: summary; failure classes with honest share ("unknown — needs data X"); surviving errors with owner + fix; what was refuted and why. Weight verifier corrections over original claims. Unverified stays labelled unverified.\n${JSON.stringify([...verified.filter(Boolean), ...rest])}`,
  { label: 'synthesize', phase: 'Synthesize' })
