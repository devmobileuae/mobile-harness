// ─────────────────────────────────────────────────────────────────────────────
// WHAT:
//   - MERGED_*: consolidation instead of noindex. When GSC shows Google already sends the
//     weak page's queries to a sibling (e.g. "lawn mowing invoice" queries
//     land on /landscaping while /lawn-mowing sits in "Discovered – not indexed"), delete the weak
//     entry from the registry, fold its best tips/FAQs into the survivor, redirect here.
//     Next emits 308 for permanent: true. Download files redirect too.
//   - headers(): X-Robots-Tag noindex on downloadable .docx/.xlsx — otherwise they appear
//     in "Crawled – currently not indexed", spending crawl on files that compete with their pages.
// Guarded by templates/tests/headers.test.ts. Keep `export const` so the test can import it.
// ─────────────────────────────────────────────────────────────────────────────
export const MERGED_TEMPLATES = [
  { from: "lawn-mowing", to: "landscaping" },
  { from: "self-employed", to: "sole-trader" },
];

const nextConfig = {
  reactStrictMode: true,
  async redirects() {
    return MERGED_TEMPLATES.flatMap(({ from, to }) => [
      { source: `/invoice-templates/${from}`, destination: `/invoice-templates/${to}`, permanent: true },
      {
        source: `/templates/${from}-invoice-template.:ext(docx|xlsx)`,
        destination: `/templates/${to}-invoice-template.:ext`,
        permanent: true,
      },
    ]);
  },
  async headers() {
    return [{ source: "/templates/:file*", headers: [{ key: "X-Robots-Tag", value: "noindex, nofollow" }] }];
  },
};

export default nextConfig;
