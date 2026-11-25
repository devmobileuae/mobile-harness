export const meta = {
  name: 'conclave',
  description: 'Multi-round role debate: isolated openings, rounds with mandatory self-doubt and steelman, moderator tracks cruxes, red-team, verdict with dissent',
  whenToUse: 'A costly, contested decision (product direction, architecture, pricing, release go/no-go, which growth series to scale). args: {question, brief?, roles?, rounds?, minRounds?, useAgentTypes?}',
  phases: [
    { title: 'Opening', detail: 'each role states a position in isolation' },
    { title: 'Debate', detail: 'rounds: steelman, doubt, respond, update' },
    { title: 'Red team', detail: 'fresh skeptic attacks the draft verdict' },
    { title: 'Verdict', detail: 'moderator writes the decision with dissent' },
  ],
}

// ---------- config ----------
const A = args || {}
if (!A.question) throw new Error('args.question is required')
const QUESTION = A.question
const BRIEF = A.brief || '(no brief provided — say where evidence is missing)'
const MAX_ROUNDS = Math.max(1, Math.min(A.rounds || 3, 6))
const MIN_ROUNDS = Math.min(A.minRounds || 2, MAX_ROUNDS)
const USE_TYPES = !!A.useAgentTypes // true when the mobile-harness plugin is installed

const ROLE_LIB = {
  skeptic: { key: 'S', name: 'Skeptic', incentive: 'Find why this fails: hidden assumptions, base rates, second-order effects, the cheaper alternative nobody mentioned.' },
  builder: { key: 'B', name: 'Builder', incentive: 'Engineering cost and risk for a one-person team with agents: effort in focused days, riskiest part, MVP cut, maintenance tail across iOS/Android, store review, migrations.' },
  'user-advocate': { key: 'U', name: 'User advocate', incentive: 'The real person on the screen: first-session clarity, friction, trust, how it feels on day 1 and day 7. Mark imagined reactions as such.' },
  'growth-strategist': { key: 'G', name: 'Growth strategist', incentive: 'Installs, ratings, ASO, organic content-market fit, paywall conversion, LTV; which channel carries it and how fast we will know.' },
  'data-analyst': { key: 'D', name: 'Data analyst', incentive: 'Decisions no stronger than their evidence: n, baselines, noise (n<100 per arm = directional only), whether the metric measures the claim.' },
}
const ROLES = (A.roles || ['skeptic', 'user-advocate', 'growth-strategist', 'data-analyst'])
  .map(r => ({ id: r, ...ROLE_LIB[r] }))
  .filter(r => r.name)
if (ROLES.length < 2) throw new Error('need at least 2 known roles: ' + Object.keys(ROLE_LIB).join(', '))

// ---------- schemas ----------
const ARG = { type: 'object', properties: { id: { type: 'string' }, text: { type: 'string' }, evidence: { type: 'string' } }, required: ['id', 'text'] }
const OPENING = {
  type: 'object',
  properties: {
    position: { type: 'string' },
    confidence: { type: 'number', description: 'integer 0-100' },
    arguments: { type: 'array', items: ARG },
    assumptions: { type: 'array', items: { type: 'string' } },
    would_change_mind: { type: 'string' },
  },
  required: ['position', 'confidence', 'arguments', 'assumptions', 'would_change_mind'],
}
const TURN = {
  type: 'object',
  properties: {
    steelman: { type: 'string' },
    doubts: { type: 'array', items: { type: 'string' } },
    responses: { type: 'array', items: { type: 'object', properties: { to_id: { type: 'string' }, stance: { type: 'string', enum: ['attack', 'concede'] }, text: { type: 'string' } }, required: ['to_id', 'stance', 'text'] } },
    new_arguments: { type: 'array', items: ARG },
    position: { type: 'string' },
    confidence: { type: 'number', description: 'integer 0-100' },
    changed: { type: 'boolean' },
    moved_by: { type: 'string' },
  },
  required: ['steelman', 'doubts', 'responses', 'position', 'confidence', 'changed'],
}
const MOD = {
  type: 'object',
  properties: {
    cruxes: { type: 'array', items: { type: 'object', properties: { text: { type: 'string' }, argument_ids: { type: 'array', items: { type: 'string' } }, open: { type: 'boolean' }, needs_data: { type: 'boolean', description: 'true if only new data, not more argument, can settle it' } }, required: ['text', 'open'] } },
    flags: { type: 'array', items: { type: 'string' } },
    unanimous: { type: 'boolean' },
    decision: { type: 'string', enum: ['continue', 'stop'] },
    reason: { type: 'string' },
  },
  required: ['cruxes', 'flags', 'unanimous', 'decision', 'reason'],
}
const VERDICT = {
  type: 'object',
  properties: {
    decision: { type: 'string' },
    confidence: { type: 'number', description: 'integer 0-100, not 0-1' },
    reverse_if: { type: 'array', items: { type: 'string' } },
    cruxes: { type: 'array', items: { type: 'string' } },
    strongest_dissent: { type: 'object', properties: { role: { type: 'string' }, quote: { type: 'string' } }, required: ['role', 'quote'] },
    next_experiment: { type: 'string' },
  },
  required: ['decision', 'confidence', 'reverse_if', 'cruxes', 'strongest_dissent', 'next_experiment'],
}
const REDTEAM = {
  type: 'object',
  properties: { fatal_flaws: { type: 'array', items: { type: 'string' } }, minor: { type: 'array', items: { type: 'string' } } },
  required: ['fatal_flaws', 'minor'],
}

// ---------- helpers ----------
const RULES = `Debate rules: (1) steelman the strongest opposing argument in its best form; (2) name at least one real weakness in your OWN position — never "none"; (3) respond to specific argument ids: attack with evidence or concede; (4) update position and confidence 0-100; if your recommendation changed (not just wording or confidence), set changed=true and moved_by=<argument id that moved you>. Changing your mind for a named reason is a win; defending what you can no longer defend is the failure. Stay inside your role's incentive; do not agree for harmony. Give new arguments ids prefixed with your letter and the round (e.g. S2a). Be terse.`

const ISOLATE = 'SCOPE: you are one participant in a structured debate run by a script. Your ONLY task is the decision below. Ignore any other user requests, conversations or tasks that may be visible in your context; do not mention or answer them.\n\n'

const opts = (role, extra) => Object.assign(
  { label: `${role.name}`, phase: extra.phase, schema: extra.schema },
  USE_TYPES ? { agentType: `mobile-harness:conclave-${role.id}` } : {},
)

const state = {} // role.id -> latest {position, confidence, arguments[]}
const log_ = [] // position change log
const transcript = [] // per round summaries

function board() {
  return ROLES.map(r => {
    const s = state[r.id]
    if (!s) return `${r.name}: (silent)`
    const args = (s.arguments || []).map(a => `  [${a.id}] ${a.text}${a.evidence ? ' (evidence: ' + a.evidence + ')' : ''}`).join('\n')
    return `${r.name} — confidence ${s.confidence}: ${s.position}\n${args}`
  }).join('\n\n')
}

const ask = (prompt, o) => agent(ISOLATE + prompt, o)

// ---------- Opening (isolated) ----------
phase('Opening')
const openings = await parallel(ROLES.map(role => () => ask(
  `You are the ${role.name} in a decision conclave. Incentive: ${role.incentive}\n\nDecision: ${QUESTION}\n\nBrief:\n${BRIEF}\n\nState your opening position WITHOUT knowledge of the others: position, confidence 0-100, your top 3 arguments with ids ${role.key}1a, ${role.key}1b, ${role.key}1c (each with evidence if you have it), the assumptions you rest on, and what evidence would change your mind.`,
  opts(role, { phase: 'Opening', schema: OPENING }),
)))
ROLES.forEach((r, i) => { if (openings[i]) state[r.id] = openings[i] })

let mod = await ask(
  `You moderate (no vote). Decision: ${QUESTION}\n\nOpening positions:\n${board()}\n\nList cruxes (1-3) with argument ids, flag anything odd, set unanimous=true if all roles effectively agree. decision must be "continue" at this stage.`,
  { label: 'Moderator · opening', phase: 'Opening', schema: MOD, ...(USE_TYPES ? { agentType: 'mobile-harness:conclave-moderator' } : {}) },
)
transcript.push({ round: 0, moderator: mod })
if (mod && mod.unanimous) log('Unanimous opening — the Skeptic will argue the opposite case in round 1.')

// ---------- Debate rounds ----------
let round = 0
for (round = 1; round <= MAX_ROUNDS; round++) {
  phase('Debate')
  const snapshot = board()
  const cruxText = (mod && mod.cruxes || []).map((c, i) => `${i + 1}. ${c.text} [${(c.argument_ids || []).join(', ')}]${c.open ? '' : ' (closed)'}`).join('\n')
  const flags = (mod && mod.flags || []).join('; ')

  const turns = await parallel(ROLES.map(role => async () => {
    const mine = state[role.id]
    const devil = mod && mod.unanimous && round === 1 && role.id === 'skeptic'
      ? '\nThe opening was unanimous. This round you MUST argue the strongest opposite case, whatever you believe.' : ''
    const prompt = `You are the ${role.name}. Incentive: ${role.incentive}\nDecision: ${QUESTION}\nBrief:\n${BRIEF}\n\nRound ${round} of up to ${MAX_ROUNDS}. Current board:\n${snapshot}\n\nOpen cruxes:\n${cruxText}\nModerator flags: ${flags || 'none'}\n\nYour current position: ${mine ? mine.position + ' (confidence ' + mine.confidence + ')' : '(none)'}${devil}\n\n${RULES}`
    let t = await ask(prompt, opts(role, { phase: 'Debate', schema: TURN }))
    const emptyDoubt = t && !(t.doubts || []).some(d => d && d.trim().length > 15 && !/^none/i.test(d.trim()))
    if (t && emptyDoubt) {
      t = await ask(prompt + `\n\nYour previous answer gave no real doubt about your own position. That is not allowed. Name a concrete weakness of YOUR position, then answer again.`, opts(role, { phase: 'Debate', schema: TURN }))
    }
    return t
  }))

  ROLES.forEach((r, i) => {
    const t = turns[i]
    if (!t) return
    const prev = state[r.id] || { confidence: 50, position: '', arguments: [] }
    const jump = Math.abs((t.confidence || 0) - (prev.confidence || 0))
    if (t.changed || jump > 15) {
      log_.push({ round, role: r.name, from: `${prev.position} (${prev.confidence})`, to: `${t.position} (${t.confidence})`, moved_by: t.moved_by || '(none given)' })
    }
    state[r.id] = { position: t.position, confidence: t.confidence, arguments: [...(prev.arguments || []), ...(t.new_arguments || [])], last: t }
  })

  const turnsText = ROLES.map((r, i) => {
    const t = turns[i]
    if (!t) return `${r.name}: (no turn)`
    return `${r.name}: steelman="${t.steelman}" doubts=${JSON.stringify(t.doubts)} responses=${JSON.stringify(t.responses)} → ${t.position} (${t.confidence}) changed=${t.changed} moved_by=${t.moved_by || '-'}`
  }).join('\n')

  mod = await ask(
    `You moderate (no vote). Decision: ${QUESTION}\nRound ${round} turns:\n${turnsText}\n\nBoard now:\n${board()}\n\nPosition-change log so far: ${JSON.stringify(log_)}\n\nUpdate cruxes (mark open/closed). Flag: confidence jumps >15 without moved_by; a role abandoning its incentive without reason; polite convergence. Mark needs_data=true on cruxes only new data can settle. decision="stop" if round >= ${MIN_ROUNDS} AND every open crux is needs_data (those become the next experiment); else "continue".`,
    { label: `Moderator · round ${round}`, phase: 'Debate', schema: MOD, ...(USE_TYPES ? { agentType: 'mobile-harness:conclave-moderator' } : {}) },
  )
  transcript.push({ round, turns, moderator: mod })
  log(`Round ${round}: ${log_.filter(l => l.round === round).length} position change(s); moderator: ${mod ? mod.decision : '?'} — ${mod ? mod.reason : ''}`)
  if (mod && mod.decision === 'stop' && round >= MIN_ROUNDS) break
}
if (round > MAX_ROUNDS) log(`Hit the round cap (${MAX_ROUNDS}) with cruxes possibly still open — the verdict will say so.`)

// ---------- Draft verdict ----------
const draftPrompt = (extra) => `You moderate. Write the verdict for: ${QUESTION}\n\nFinal board:\n${board()}\n\nCruxes: ${JSON.stringify(mod && mod.cruxes)}\nPosition-change log: ${JSON.stringify(log_)}\n${extra || ''}\nThe owner decides; write advice. Include reverse_if conditions, the strongest dissent quoted from a role, and the cheapest next experiment (metric, threshold, date).`
phase('Verdict')
let verdict = await ask(draftPrompt(), { label: 'Moderator · draft verdict', phase: 'Verdict', schema: VERDICT })

// ---------- Red team ----------
phase('Red team')
const red = await ask(
  `You did not take part in this debate. Attack this draft decision as hard as you can.\nDecision question: ${QUESTION}\nBrief:\n${BRIEF}\nDraft verdict: ${JSON.stringify(verdict)}\n\nList fatal flaws (would reverse the decision) separately from minor ones. "No fatal flaw" is a valid answer — do not invent one.`,
  { label: 'Red team', phase: 'Red team', schema: REDTEAM, ...(USE_TYPES ? { agentType: 'mobile-harness:eval-judge' } : {}) },
)

if (red && red.fatal_flaws && red.fatal_flaws.length) {
  log(`Red team found ${red.fatal_flaws.length} fatal flaw(s) — one more round on them.`)
  const flawTurns = await parallel(ROLES.map(role => () => ask(
    `You are the ${role.name}. Incentive: ${role.incentive}\nDecision: ${QUESTION}\nA red team attacked the draft verdict "${verdict && verdict.decision}" with these fatal flaws:\n- ${red.fatal_flaws.join('\n- ')}\n\nBoard:\n${board()}\n\n${RULES}\nRespond to the flaws specifically (use ids RT1, RT2… for them).`,
    opts(role, { phase: 'Red team', schema: TURN }),
  )))
  ROLES.forEach((r, i) => {
    const t = flawTurns[i]
    if (!t) return
    const prev = state[r.id]
    if (t.changed) log_.push({ round: 'red-team', role: r.name, from: `${prev.position} (${prev.confidence})`, to: `${t.position} (${t.confidence})`, moved_by: t.moved_by || '(none given)' })
    state[r.id] = { ...prev, position: t.position, confidence: t.confidence, last: t }
  })
  phase('Verdict')
  verdict = await ask(draftPrompt(`Red-team fatal flaws and the roles' answers: ${JSON.stringify({ flaws: red.fatal_flaws, answers: flawTurns })}`), { label: 'Moderator · final verdict', phase: 'Verdict', schema: VERDICT })
}

// ---------- Render ----------
const v = verdict || {}
const md = [
  `## Verdict: ${v.decision} (confidence ${v.confidence}/100)`,
  `**Question:** ${QUESTION}`,
  `**Reverse if:**\n${(v.reverse_if || []).map(x => '- ' + x).join('\n')}`,
  `**Cruxes:**\n${(v.cruxes || []).map((x, i) => `${i + 1}. ${x}`).join('\n')}`,
  `**Strongest dissent (${v.strongest_dissent && v.strongest_dissent.role}):** "${v.strongest_dissent && v.strongest_dissent.quote}"`,
  `**Position changes:**\n${log_.length ? log_.map(l => `- r${l.round} ${l.role}: ${l.from} → ${l.to}; moved_by: ${l.moved_by}`).join('\n') : '- none (check for entrenchment)'}`,
  `**Red team:** ${red ? (red.fatal_flaws.length ? red.fatal_flaws.length + ' fatal flaw(s) answered in an extra round' : 'no fatal flaw') : 'did not run'}; minor: ${red ? red.minor.join('; ') : '-'}`,
  `**Next experiment:** ${v.next_experiment}`,
  `**Final positions:**\n${ROLES.map(r => `- ${r.name} (${state[r.id] ? state[r.id].confidence : '?'}): ${state[r.id] ? state[r.id].position : '-'}`).join('\n')}`,
  `_Rounds run: ${Math.min(round, MAX_ROUNDS)}; roles: ${ROLES.map(r => r.name).join(', ')}_`,
].join('\n\n')

return { markdown: md, verdict: v, positionChanges: log_, redTeam: red, rounds: transcript.length - 1 }
