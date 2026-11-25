// ─────────────────────────────────────────────────────────────────────────────
// WHAT: one place for the canonical origin and the "only production may be indexed" gate.
//   robots.ts, layout metadata (robots: { index: isIndexable }) and tests read from here.
// HOW: copy to lib/site.ts, fill the constants. Nothing has to be set in the Vercel
//   dashboard: VERCEL_ENV === "production" opens the gate, previews stay Disallow: /.
// ─────────────────────────────────────────────────────────────────────────────
export const site = {
  appName: "MyApp",                                   // short brand, WebSite.name
  fullName: "MyApp: Invoice & Estimate Maker",        // store name
  // No trailing slash. NEXT_PUBLIC_SITE_URL overrides it for a staging host.
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "https://example.app",
  appStoreUrl: "https://apps.apple.com/app/id0000000000"     // app_store_url from local/apps.yaml,
  appStoreId: "0000000000",                                  // Smart App Banner: metadata.itunes.appId
};

/**
 * An explicit NEXT_PUBLIC_SITE_INDEXABLE always wins ("false" keeps a *.vercel.app host out of
 * the index until the real domain exists). Otherwise only the production deploy is
 * indexable, so preview URLs never compete with the real domain for our own keywords.
 */
export const isIndexable = process.env.NEXT_PUBLIC_SITE_INDEXABLE
  ? process.env.NEXT_PUBLIC_SITE_INDEXABLE === "true"
  : process.env.VERCEL_ENV === "production";
