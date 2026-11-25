export const meta = {
  name: 'reel-pipeline',
  description: 'Short-form content from niche to post-ready: research hypotheses, conclave picks one, scenario per variant, adversarial script review, frame QA gate on rendered frames',
  whenToUse: 'A new content series or episode for an app account. args: {app, niche, account, variants?: 3, framesDir?: "<path to rendered frames for QA>"}',
  phases: [
    { title: 'Research', detail: 'formats, hooks, audience language with evidence' },
    { title: 'Decide', detail: 'conclave on which hypothesis to produce' },
    { title: 'Script', detail: 'N scenario variants, each reviewed adversarially' },
    { title: 'QA', detail: 'frame-qa on rendered frames (if provided)' },
  ],
}

const A = args || {}
if (!A.app || !A.niche) throw new Error('args: {app, niche, account?, variants?, framesDir?}')
const N = Math.min(A.variants || 3, 6)

const HYP = { type: 'object', properties: { hypotheses: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, format: { type: 'string' }, hook: { type: 'string' }, examples: { type: 'array', items: { type: 'string' } }, why_it_travels: { type: 'string' }, product_fit: { type: 'string' } }, required: ['id', 'format', 'hook', 'examples', 'why_it_travels'] } } }, required: ['hypotheses'] }
const SCORE = { type: 'object', properties: { score: { type: 'number' }, hook_ok: { type: 'boolean' }, product_forced: { type: 'boolean' }, ambiguous_lines: { type: 'array', items: { type: 'string' } }, safe_zone_risks: { type: 'array', items: { type: 'string' } }, verdict: { type: 'string', enum: ['PRODUCE', 'REWRITE', 'DROP'] }, fixes: { type: 'array', items: { type: 'string' } } }, required: ['score', 'hook_ok', 'product_forced', 'verdict', 'fixes'] }

phase('Research')
const research = await agent(
  `Research organic short-form content for the app "${A.app}" in the niche "${A.niche}". Find formats and hooks that actually get reach now (numbers + links), audience language from comments, and creators to study. Etiquette: no bulk fetching through the owner's logged-in browser; logged-out tools only. Return 4–6 ranked hypotheses; the product must not be forced into the story.`,
  { label: 'research', phase: 'Research', schema: HYP, ...(A.useAgentTypes ? { agentType: 'mobile-harness:growth-researcher' } : {}) },
)

phase('Decide')
const decision = await workflow('conclave', {
  question: `Which content hypothesis should ${A.account || A.app} produce next as a 10-post series?`,
  brief: JSON.stringify(research.hypotheses),
  roles: ['skeptic', 'growth-strategist', 'user-advocate', 'data-analyst'],
  rounds: 2,
  minRounds: 2,
})
log('Conclave verdict: ' + (decision && decision.verdict ? decision.verdict.decision : 'n/a'))

phase('Script')
const scripts = await pipeline(
  Array.from({ length: N }, (_, i) => i),
  i => agent(
    `Write scenario variant ${i + 1} of ${N} (make each variant use a different hook angle) for the chosen direction:\n${decision ? decision.verdict.decision : JSON.stringify(research.hypotheses[0])}\nApp: ${A.app}. Shot table: t | shot | on-screen text | VO | sound. Hook in the first 1.5 s; tension over explanation; no app score/brand inside the story unless asked; every VO line unambiguous against its frame; text inside 200<y<1500, x<960.`,
    { label: `script:v${i + 1}`, phase: 'Script', ...(A.useAgentTypes ? { agentType: 'mobile-harness:scenario-writer' } : {}) },
  ),
  (script, i) => agent(
    `Try to kill this short-form script before money is spent on generation. Score 0–16 (hook, clarity, retention, payoff). Flag product forced into the story, ambiguous VO lines vs frames, safe-zone risks. Default to REWRITE if unsure.\n\n${script}`,
    { label: `review:v${i + 1}`, phase: 'Script', schema: SCORE },
  ).then(score => ({ variant: i + 1, script, score })),
)

let qa = null
if (A.framesDir) {
  phase('QA')
  qa = await agent(
    `Run the frame-qa skill on every frame in ${A.framesDir}: full-size anatomy pass (count fingers on every hand close-up), safe_zones.py on text frames, narration vs screen, continuity, cover grid crop. Return the FRAME QA block with SHIP or FIX FIRST.`,
    { label: 'frame-qa', phase: 'QA', ...(A.useAgentTypes ? { agentType: 'mobile-harness:frame-inspector' } : {}) },
  )
}

const ranked = scripts.filter(Boolean).sort((a, b) => (b.score ? b.score.score : 0) - (a.score ? a.score.score : 0))
return { decision: decision && decision.markdown, scripts: ranked, frameQA: qa }
