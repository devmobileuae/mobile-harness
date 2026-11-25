export const meta = {
  name: 'skill-audit',
  description: 'Monthly skill audit: split each skill into units, prosecutor argues delete, defender must show evidence (eval / incident / external rule), judge rules per unit, report written',
  whenToUse: 'Monthly (first Monday) or after a model change. args: {skills: ["frame-qa", ...], pluginDir: "<abs path>", month: "YYYY-MM"}',
  phases: [
    { title: 'Inventory', detail: 'read skill, registry, usage, evals; split into units' },
    { title: 'Trial', detail: 'prosecutor vs defender per skill' },
    { title: 'Ruling', detail: 'judge per unit, rewrite proposal, report' },
  ],
}

const A = args || {}
if (!A.pluginDir || !A.skills || !A.skills.length) throw new Error('args: {pluginDir, skills[], month}')
const DIR = A.pluginDir
const MONTH = A.month || 'unknown-month'

const UNITS = {
  type: 'object',
  properties: {
    usage_note: { type: 'string' },
    eval_cases: { type: 'array', items: { type: 'string' } },
    born_from: { type: 'array', items: { type: 'string' } },
    units: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, section: { type: 'string' }, text: { type: 'string' }, why_comment: { type: 'string' } }, required: ['id', 'section', 'text'] } },
  },
  required: ['units', 'eval_cases', 'born_from'],
}
const PROSECUTION = {
  type: 'object',
  properties: { charges: { type: 'array', items: { type: 'object', properties: { unit: { type: 'string' }, category: { type: 'string', enum: ['DEFAULT', 'DUPLICATE', 'OUTDATED', 'CONTRADICTED', 'VAGUE', 'OVERFIT', 'MODEL-COMPENSATION', 'NONE'] }, argument: { type: 'string' }, shorter_rewrite: { type: 'string' } }, required: ['unit', 'category', 'argument'] } } },
  required: ['charges'],
}
const DEFENSE = {
  type: 'object',
  properties: { defenses: { type: 'array', items: { type: 'object', properties: { unit: { type: 'string' }, evidence_type: { type: 'string', enum: ['E1-eval', 'E2-incident', 'E3-external', 'ENV-FACT', 'NONE'] }, evidence: { type: 'string' }, concede: { type: 'boolean' }, eval_to_write: { type: 'string' } }, required: ['unit', 'evidence_type', 'concede'] } } },
  required: ['defenses'],
}
const RULING = {
  type: 'object',
  properties: {
    rulings: { type: 'array', items: { type: 'object', properties: { unit: { type: 'string' }, verdict: { type: 'string', enum: ['KEEP', 'DELETE', 'REWRITE', 'MERGE', 'NEEDS-EVAL'] }, deciding_evidence: { type: 'string' }, new_text: { type: 'string' } }, required: ['unit', 'verdict', 'deciding_evidence'] } },
    sections_to_ablate: { type: 'array', items: { type: 'string' } },
    report_markdown: { type: 'string' },
  },
  required: ['rulings', 'sections_to_ablate', 'report_markdown'],
}

const results = await pipeline(
  A.skills,
  // 1. inventory
  skill => agent(
    `Audit inventory for skill "${skill}" in plugin ${DIR}.\nRead ${DIR}/skills/${skill}/SKILL.md, its entry in ${DIR}/skills/registry.yaml, and the eval case folders in ${DIR}/evals/ that match its registry globs (list their names). If ${DIR}/evals/results/ has recent aggregate-result.json files, note this skill's cases' with/without delta. Split the SKILL.md body into units (one bullet / rule / table row / example each, ids U1..Un, keep section name and any <!-- why: --> comment).`,
    { label: `inventory:${skill}`, phase: 'Inventory', schema: UNITS },
  ),
  // 2. trial: prosecutor and defender in parallel (the defender gets the same units, not the charges, to avoid anchoring)
  (inv, skill) => parallel([
    () => agent(
      `You are the prosecutor in a skill audit. Skill "${skill}". For EVERY unit below make the strongest honest case for deletion and pick a category (DEFAULT = model does it anyway; DUPLICATE; OUTDATED; CONTRADICTED; VAGUE = uncheckable; OVERFIT = one past case; MODEL-COMPENSATION = patched an older model; NONE = you cannot honestly charge it). Offer a shorter rewrite where deletion is too strong. Facts about the owner's environment (file ids, account rules, product canon) are not DEFAULT — the model cannot know them.\nUnits:\n${JSON.stringify(inv.units, null, 1)}`,
      { label: `prosecutor:${skill}`, phase: 'Trial', schema: PROSECUTION, ...(A.useAgentTypes ? { agentType: 'mobile-harness:skill-prosecutor' } : {}) },
    ),
    () => agent(
      `You are the defender in a skill audit. Skill "${skill}". Burden of proof is on keeping. For each unit, give evidence or concede: E1-eval (name an eval case among ${JSON.stringify(inv.eval_cases)} that depends on the unit), E2-incident (one of these dated incidents, ≤ 6 months: ${JSON.stringify(inv.born_from)}, or a why-comment), E3-external (store guideline, platform spec, API contract), ENV-FACT (a fact about the owner's environment the model cannot know). "Good practice" is NONE → concede, and say which eval case you would write to test it.\nUnits:\n${JSON.stringify(inv.units, null, 1)}`,
      { label: `defender:${skill}`, phase: 'Trial', schema: DEFENSE, ...(A.useAgentTypes ? { agentType: 'mobile-harness:skill-defender' } : {}) },
    ),
  ]).then(([pros, def]) => ({ inv, pros, def })),
  // 3. ruling
  (trial, skill) => agent(
    `You are the judge in the ${MONTH} audit of skill "${skill}". Decide each unit on evidence only: KEEP needs E1/E2/E3/ENV-FACT that you find credible; ties go to the shorter skill; MERGE names the target skill; REWRITE gives new_text (shorter, checkable); NEEDS-EVAL keeps the unit one month and names the eval case to write. List sections_to_ablate: sections whose KEEP rests only on belief, to be verified by running claude plugin eval with the section removed.\nThen write report_markdown in this shape:\n"Skill: <name>  eval cases: <n>  units: <n> → keep <k>, delete <d>, rewrite <r>, merge <m>, needs-eval <e>" followed by a table | unit | verdict | evidence | note | and an estimate of token change.\n\nUnits: ${JSON.stringify(trial.inv.units)}\nProsecution: ${JSON.stringify(trial.pros)}\nDefense: ${JSON.stringify(trial.def)}`,
    { label: `judge:${skill}`, phase: 'Ruling', schema: RULING, ...(A.useAgentTypes ? { agentType: 'mobile-harness:eval-judge' } : {}) },
  ),
)

const ok = results.filter(Boolean)
log(`Audited ${ok.length}/${A.skills.length} skills. Nothing is edited by this workflow — apply rulings, then run the evals before committing.`)
return {
  month: MONTH,
  reports: ok.map((r, i) => ({ skill: A.skills[i], report: r.report_markdown, ablate: r.sections_to_ablate, rulings: r.rulings })),
  next: 'For each skill: write docs/audits/<month>-<skill>.md from report; ablate listed sections with claude plugin eval on a temp copy; apply edits only if the suite score holds; bump `reviewed` in registry.yaml.',
}
