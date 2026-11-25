// ─────────────────────────────────────────────────────────────────────────────
// WHAT: the sitemap lists exactly static paths + every guide + every registry page, the home
//   page WITH a trailing slash (GSC attributes sitemaps by exact URL string; without the
//   slash URL Inspection said "No referring sitemaps detected"), no
//   redirect endpoints, and a lastModified on every entry.
// HOW: copy to tests/, adjust imports to match templates/next/sitemap.ts.
// ─────────────────────────────────────────────────────────────────────────────
import { describe, it, expect } from "vitest";
import sitemap, { STATIC_PATHS } from "@/app/sitemap";
import { TEMPLATES } from "@/lib/templates/registry";
import { GUIDES } from "@/lib/guides";
import { site } from "@/lib/site";

describe("sitemap", () => {
  const entries = sitemap();
  const urls = entries.map((e) => e.url);

  it("lists static paths, every guide and every template page — nothing else", () => {
    expect(entries).toHaveLength(STATIC_PATHS.length + GUIDES.length + TEMPLATES.length);
    for (const g of GUIDES) expect(urls).toContain(`${site.url}${g.href}`);
    for (const t of TEMPLATES) expect(urls).toContain(`${site.url}/invoice-templates/${t.slug}`);
  });

  it("lists the home page with a trailing slash, matching the URL Googlebot crawls", () => {
    expect(urls).toContain(`${site.url}/`);
    expect(urls).not.toContain(site.url);
  });

  it("has no duplicate URLs", () => expect(new Set(urls).size).toBe(urls.length));

  it("keeps the /get App Store redirect out", () => {
    expect(urls.some((u) => u.endsWith("/get"))).toBe(false);
  });

  it("stamps every entry with a last-modified date", () => {
    for (const e of entries) expect(e.lastModified).toBeInstanceOf(Date);
  });
});
