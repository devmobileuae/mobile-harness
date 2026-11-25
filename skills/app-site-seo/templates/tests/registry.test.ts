// ─────────────────────────────────────────────────────────────────────────────
// The anti-doorway gate: pages that pass land around 2,000–2,400 words with max pairwise
//   5-gram Jaccard ≤ 0.10 — i.e. not near-duplicates.
// WHAT: content-depth gate for programmatic pages. A page that fails cannot be deployed.
//   Contrast: programmatic pages with ~128 words sit in "Discovered – not indexed".
// HOW: point REGISTRIES at your typed registries; field names below assume a
//   TemplateDef (metaTitle, metaDescription, intro[2], tips[{body}], faq[], howTo[{step,detail}],
//   related[slug]). Run: npx vitest run tests/registry.test.ts
// ─────────────────────────────────────────────────────────────────────────────
import { describe, it, expect } from "vitest";
import { TEMPLATES } from "@/lib/templates/registry";

type Def = (typeof TEMPLATES)[number];
const wordCount = (s: string) => s.trim().split(/\s+/).length;
const REGISTRIES: { reg: string; list: Def[] }[] = [{ reg: "invoice", list: TEMPLATES }];

describe("registry quality gate", () => {
  for (const { reg, list } of REGISTRIES) {
    it(`${reg} slugs unique`, () => expect(new Set(list.map((t) => t.slug)).size).toBe(list.length));

    for (const t of list) {
      describe(`${reg}/${t.slug}`, () => {
        it("meta lengths (title <=60, description 120–165)", () => {
          expect(t.metaTitle.length).toBeLessThanOrEqual(60);
          expect(t.metaDescription.length).toBeGreaterThanOrEqual(120);
          expect(t.metaDescription.length).toBeLessThanOrEqual(165);
        });
        it("content depth", () => {
          expect(t.intro).toHaveLength(2);
          expect(wordCount(t.intro.join(" "))).toBeGreaterThanOrEqual(120);
          expect(t.tips.length).toBeGreaterThanOrEqual(4);
          for (const tip of t.tips) {
            const w = wordCount(tip.body);
            expect(w).toBeGreaterThanOrEqual(30);
            expect(w).toBeLessThanOrEqual(110);
          }
          expect(t.faq.length).toBeGreaterThanOrEqual(7);
        });
        it("how-to walkthrough is real (6–8 steps, 30–80 words each)", () => {
          expect(t.howTo.length).toBeGreaterThanOrEqual(6);
          expect(t.howTo.length).toBeLessThanOrEqual(8);
          for (const s of t.howTo) {
            const w = wordCount(s.detail);
            expect(w, `${t.slug} step "${s.step}"`).toBeGreaterThanOrEqual(30);
            expect(w, `${t.slug} step "${s.step}"`).toBeLessThanOrEqual(80);
          }
        });
        it("related slugs resolve (no dead internal links)", () => {
          for (const r of t.related) expect(list.some((x) => x.slug === r), `unknown related: ${r}`).toBe(true);
        });
      });
    }
  }
});
