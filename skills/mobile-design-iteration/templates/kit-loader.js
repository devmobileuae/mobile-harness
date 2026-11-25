// Figma "kit in the file" pattern — snippets for use_figma (Figma MCP).
// Replace <kit id>, <lint id>, <builder id>, <page id> with the nodes of your file (see references/env.md).
// WHAT: the helper kit (T/R/E/F/S/pill/chunky/icon/...) and the pixel lint are stored as TEXT inside
//   hidden nodes of the Figma file and loaded with the AsyncFunction constructor at the top of every
//   use_figma script. One source for every agent, no pasting 600 lines per call, patch once → all agents.
// HOW: paste ONE block as the `code` of a use_figma call. Plain JS, top-level await, final `return {...}`;
//   no object spread, no ?. or ??, no figma.closePlugin/notify. Build ONE phone per call.
// To start a kit for a new app: write the helpers as one async function body that takes `figma`
//   and returns {T, R, ...}; store it with `textNode.characters = src` in a hidden frame
//   «Build kit source»; never delete that frame (the loader breaks).

// ---------------------------------------------------------------- 1. build / fix a phone
const AF = Object.getPrototypeOf(async function () {}).constructor;
const K = await new AF('figma', (await figma.getNodeByIdAsync("<kit id>")).characters)(figma);
const { T, R, E, F, S, pill, chunky, icon, iconBtn, statusBar, tabBar, homeIndicator, clear, grad, radial, HOLO, place, fill, shadow } = K;

const phone = await figma.getNodeByIdAsync("<phone id>");   // the frame already exists on the board
clear(phone);                                               // re-runnable: always rebuild from empty
await statusBar(phone);
// ... content, every coordinate computed from one formula (next.y = prev.y + prev.height + gap)
await tabBar(phone, { active: 'Main' });                    // must be the LAST child
await phone.screenshot({ scale: 1.5 });                     // inline image; scale 2 returns nothing on big gradients
return { id: phone.id };

// ---------------------------------------------------------------- 2. pixel lint (read-only)
// Lint source lives in its own text node. Errors must be 0; warnings only if deliberate (say why).
const AF2 = Object.getPrototypeOf(async function () {}).constructor;
return await new AF2('figma', 'PHONE_IDS', (await figma.getNodeByIdAsync("<lint id>")).characters)(figma, ["<id1>", "<id2>", "<id3>"]);

// ---------------------------------------------------------------- 3. stored screen builder (all states at once)
// A parametrised builder stored with fn.toString() in the kit holder, one per screen family (TODAY, LEVELS…).
// Patch its text, write it back, re-run → every state updates.
const AF3 = Object.getPrototypeOf(async function () {}).constructor;
const K3 = await new AF3('figma', (await figma.getNodeByIdAsync("<kit id>")).characters)(figma);
const src = (await figma.getNodeByIdAsync("<builder id>")).characters;
const build = await new AF3('figma', 'K', 'only', 'return (' + src + ')(figma, K, only)');
return await build(figma, K3, null /* or ['L1'] to rebuild one state */);

// ---------------------------------------------------------------- 4. screenshot several phones (reviewer)
// get_screenshot/get_metadata share ~200 calls/day on the Pro plan; use_figma is not rate-limited
// (14 parallel calls are fine). So review from inside use_figma.
const PAGE = await figma.getNodeByIdAsync("<page id>");
await figma.setCurrentPageAsync(PAGE);
for (const id of ["<id1>", "<id2>", "<id3>"]) { const n = await figma.getNodeByIdAsync(id); await n.screenshot({ scale: 2 }); }
return { ok: true };

// ---------------------------------------------------------------- 5. geometry table (check alignment with numbers)
const P0 = await figma.getNodeByIdAsync("<phone id>");
const PB = P0.absoluteBoundingBox, rows = [];
const walk = (n, d) => {
  if (n.visible === false) return;
  const b = n.absoluteBoundingBox;
  if (n !== P0 && b) rows.push([d, n.type, (n.name || '').slice(0, 28), Math.round(b.x - PB.x), Math.round(b.y - PB.y), Math.round(b.width), Math.round(b.height), n.id, n.type === 'TEXT' ? n.fontSize : ''].join(' | '));
  if ('children' in n && n.type !== 'INSTANCE' && (n.name || '').indexOf('icon/') !== 0 && d < 4) for (const c of n.children) walk(c, d + 1);
};
walk(P0, 0);
return rows.join('\n');

// ---------------------------------------------------------------- 6. diff the owner's edits before touching a row
// The owner moves layers too (e.g. a speech bubble nudged up-right of the mascot); screenshots miss small moves. Compare a row with its earlier clone by layer name.
const A = await figma.getNodeByIdAsync("<original frame>"), B = await figma.getNodeByIdAsync("<clone frame>");
const map = n => { const m = {}; n.findAll(() => true).forEach(c => { m[c.name] = [Math.round(c.x), Math.round(c.y), Math.round(c.width), Math.round(c.height)]; }); return m; };
const ma = map(A), mb = map(B), diff = [];
for (const k in ma) if (mb[k] && ma[k].join() !== mb[k].join()) diff.push(k + ': ' + ma[k].join(',') + ' → ' + mb[k].join(','));
return diff;   // note: findAll does NOT descend into nested instances
