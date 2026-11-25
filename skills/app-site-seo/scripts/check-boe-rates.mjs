// ─────────────────────────────────────────────────────────────────────────────
// WHAT: the "fact freshness" pattern for YMYL/money pages. It scrapes the primary
//   source (Bank of England Bank Rate table), reads the table the site actually ships
//   (lib/late-payment-config.ts REFERENCE_PERIODS) and fails if any row drifted or
//   today is not covered. Run it before any outreach email quotes the rate.
// RUN (in the site repo): npm run check:rates   (not in npm test: needs network)
//   Run on 1 Jan / 1 Jul and before quoting a rate in outreach.
// REUSE: copy the shape for any page that quotes an official number (VAT rates,
//   penalty tables, ASP counts): fetch source -> parse -> regex the shipped config -> diff -> exit 1.
// ─────────────────────────────────────────────────────────────────────────────
/**
 * Cross-checks REFERENCE_PERIODS in lib/late-payment-config.ts against the Bank of
 * England's published Bank Rate series.
 *
 *   npm run check:rates
 *
 * Not part of `npm test` — it needs the network, and a flaky fetch should not fail CI.
 * Run it whenever a new six-month window opens (1 January / 1 July), or before quoting
 * the rate to anyone who will check.
 */

import { readFileSync } from "node:fs";

const BOE_URL = "https://www.bankofengland.co.uk/boeapps/database/Bank-Rate.asp";
const CONFIG = new URL("../lib/late-payment-config.ts", import.meta.url);

/** Every Bank Rate change point the Bank publishes, oldest first. */
async function fetchChanges() {
  const res = await fetch(BOE_URL, {
    headers: { "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" },
  });
  if (!res.ok) throw new Error(`Bank of England returned HTTP ${res.status}`);
  const html = await res.text();

  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const changes = [];
  // The Bank prints two-digit years with no century, and the series reaches back to the
  // 1970s — "04 Nov 99" is 1999, and a naive 2000+NN would also turn a 1921 row into 2021
  // and silently corrupt a reference rate. The table is ordered strictly newest-first, so
  // the century is whichever one keeps the sequence moving backwards.
  let previous = Date.now();
  for (const row of html.match(/<tr[^>]*>[\s\S]*?<\/tr>/g) ?? []) {
    const cells = [...row.matchAll(/<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/g)]
      .map((m) => m[1].replace(/<[^>]+>/g, "").trim())
      .filter(Boolean);
    const m = cells[0]?.match(/^(\d{1,2})\s+(\w{3})\s+(\d{2})$/);
    if (!m || cells.length < 2) continue;
    const rate = Number(cells[1]);
    if (Number.isNaN(rate)) continue;
    const monthIndex = months.indexOf(m[2]);
    if (monthIndex === -1) continue;

    const day = Number(m[1]);
    const yy = Number(m[3]);
    const candidates = [2000 + yy, 1900 + yy].map((y) => Date.UTC(y, monthIndex, day));
    const on = candidates.find((c) => c <= previous);
    if (on === undefined) {
      throw new Error(`Row "${cells[0]}" is newer than the row above it — the page is no longer newest-first.`);
    }
    previous = on;
    changes.push({ on, rate });
  }
  changes.sort((a, b) => a.on - b.on);
  if (changes.length < 20) throw new Error("Parsed too few rate changes — the page layout probably moved.");
  return changes;
}

/** Bank Rate in force at the close of `day`. */
function rateOn(changes, day) {
  let current = null;
  for (const c of changes) {
    if (c.on <= day) current = c.rate;
    else break;
  }
  return current;
}

/** The shipped table, read out of the TypeScript source so we check what actually deploys. */
function ourPeriods() {
  const src = readFileSync(CONFIG, "utf8");
  const rows = [...src.matchAll(
    /\{\s*from:\s*"([\d-]+)",\s*to:\s*"([\d-]+)",\s*referenceDate:\s*"([\d-]+)",\s*baseRate:\s*([\d.]+)\s*\}/g
  )];
  if (!rows.length) throw new Error("Found no REFERENCE_PERIODS rows — did the shape change?");
  return rows.map(([, from, to, referenceDate, baseRate]) => ({
    from, to, referenceDate, baseRate: Number(baseRate),
  }));
}

const changes = await fetchChanges();
const periods = ourPeriods();
const latest = changes[changes.length - 1];

console.log(
  `Bank of England: ${changes.length} change points, latest ` +
  `${new Date(latest.on).toISOString().slice(0, 10)} -> ${latest.rate}%`
);
console.log(`Our table: ${periods.length} periods\n`);

let bad = 0;
for (const p of periods) {
  const official = rateOn(changes, Date.parse(`${p.referenceDate}T00:00:00Z`));
  const ok = official !== null && Math.abs(official - p.baseRate) < 1e-9;
  if (!ok) bad++;
  console.log(
    `${p.from}..${p.to}  ref ${p.referenceDate}  ours ${p.baseRate}%  BoE ${official ?? "?"}%  ` +
    (ok ? "ok" : `MISMATCH -> statutory should be ${(official + 8).toFixed(2)}%`)
  );
}

// A window that has already opened but is missing from the table is just as wrong as a
// bad rate: the pages would throw, or quote a lapsed period.
const today = new Date();
const covered = periods.some(
  (p) => Date.parse(`${p.from}T00:00:00Z`) <= Date.now() && Date.now() <= Date.parse(`${p.to}T23:59:59Z`)
);
if (!covered) {
  bad++;
  console.log(`\nNo period covers today (${today.toISOString().slice(0, 10)}) — add the next row.`);
}

console.log(`\n${periods.length - bad}/${periods.length} rows verified against the Bank of England.`);
process.exit(bad === 0 ? 0 : 1);
