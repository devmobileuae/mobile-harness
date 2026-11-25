// ─────────────────────────────────────────────────────────────────────────────
// WHAT: every guide in lib/guides.ts has a real app/<href>/page.tsx, hrefs are unique, the
//   cluster hub comes first, and every template's guides[] reference resolves.
// Pin official figures the same way: expect(OFFICIAL_PROVIDERS).toHaveLength(<n>) — the official list as
//   fetched on <date> — so a stale edit fails CI instead of shipping.
// ─────────────────────────────────────────────────────────────────────────────
import { describe, it, expect } from "vitest";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { GUIDES, EINVOICING_GUIDES } from "@/lib/guides";
import { TEMPLATES } from "@/lib/templates/registry";

const pageFile = (href: string) => join(__dirname, "..", "app", ...href.split("/").filter(Boolean), "page.tsx");

describe("guides registry", () => {
  it("every guide points at a real page", () => {
    for (const g of GUIDES) expect(existsSync(pageFile(g.href)), g.href).toBe(true);
  });
  it("hrefs are unique", () => expect(new Set(GUIDES.map((g) => g.href)).size).toBe(GUIDES.length));
  it("the cluster hub comes first", () => expect(EINVOICING_GUIDES[0].href).toBe("/e-invoicing"));
  it("template guide references all resolve", () => {
    const known = new Set(GUIDES.map((g) => g.href));
    for (const t of TEMPLATES) for (const href of (t as { guides?: string[] }).guides ?? [])
      expect(known.has(href), `${t.slug} → ${href}`).toBe(true);
  });
});
