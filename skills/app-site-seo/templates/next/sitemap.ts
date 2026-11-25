// ─────────────────────────────────────────────────────────────────────────────
// WHAT: sitemap built from the SAME registries that render the pages and the footer, so a
//   registered page cannot miss the sitemap and an unregistered one cannot sneak in.
// RULES baked in:
//   - home entry is "/" -> "https://host/". With "" GSC URL Inspection said
//     "No referring sitemaps detected" for the home page.
//   - redirect/tracking endpoints (/get -> App Store) are never listed.
//   - lastModified = build time: honest for a static site that only changes on deploy.
// Replace TEMPLATES / GUIDES imports with your registries; keep tests/sitemap.test.ts in step.
// ─────────────────────────────────────────────────────────────────────────────
import type { MetadataRoute } from "next";
import { site } from "@/lib/site";
import { GUIDES } from "@/lib/guides";
import { TEMPLATES } from "@/lib/templates/registry";

const lastModified = new Date();

export const STATIC_PATHS = ["/", "/invoice-generator", "/invoice-templates", "/privacy", "/terms"];

export default function sitemap(): MetadataRoute.Sitemap {
  const staticPaths = [...STATIC_PATHS, ...GUIDES.map((g) => g.href)];
  return [
    ...staticPaths.map((p) => ({
      url: `${site.url}${p}`,
      lastModified,
      changeFrequency: "monthly" as const,
      priority: p === "/" ? 1 : 0.8,
    })),
    ...TEMPLATES.map((t) => ({
      url: `${site.url}/invoice-templates/${t.slug}`,
      lastModified,
      changeFrequency: "monthly" as const,
      priority: 0.7,
    })),
  ];
}
