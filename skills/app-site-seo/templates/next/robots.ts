// ─────────────────────────────────────────────────────────────────────────────
// WHAT: Allow + Sitemap on production, Disallow: / everywhere else. Guarded by
//   templates/tests/robots.test.ts. Copy to app/robots.ts; import path assumes lib/site.ts.
// ─────────────────────────────────────────────────────────────────────────────
import type { MetadataRoute } from "next";
import { site, isIndexable } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return isIndexable
    ? { rules: { userAgent: "*", allow: "/" }, sitemap: `${site.url}/sitemap.xml` }
    : { rules: { userAgent: "*", disallow: "/" } };
}
