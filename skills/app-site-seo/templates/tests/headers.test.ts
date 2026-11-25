// ─────────────────────────────────────────────────────────────────────────────
// WHAT: (1) every merged page is gone from the registry, its survivor exists, and the redirect
//   is permanent (308); (2) downloadable files carry X-Robots-Tag noindex, nofollow.
// ─────────────────────────────────────────────────────────────────────────────
import { describe, it, expect } from "vitest";
import nextConfig, { MERGED_TEMPLATES } from "../next.config.mjs";
import { getTemplate } from "@/lib/templates/registry";

describe("merged template redirects", () => {
  it("send each retired template page, permanently, to a live one", async () => {
    const rules = await nextConfig.redirects();
    for (const { from, to } of MERGED_TEMPLATES) {
      expect(getTemplate(from), `${from} must be gone from the registry`).toBeUndefined();
      expect(getTemplate(to), `${to} must exist`).toBeDefined();
      expect(rules).toContainEqual({
        source: `/invoice-templates/${from}`, destination: `/invoice-templates/${to}`, permanent: true,
      });
    }
  });
});

describe("response headers", () => {
  it("keeps the downloadable .docx/.xlsx templates out of the index", async () => {
    const rules = await nextConfig.headers();
    const rule = rules.find((r: { source: string }) => r.source === "/templates/:file*");
    expect(rule).toBeDefined();
    expect(rule.headers).toContainEqual({ key: "X-Robots-Tag", value: "noindex, nofollow" });
  });
});
