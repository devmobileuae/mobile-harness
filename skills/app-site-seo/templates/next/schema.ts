// ─────────────────────────────────────────────────────────────────────────────
// WHAT: the home graph — WebSite + Organization + MobileApplication with stable @ids, so every
//   page's Article points at the same publisher instead of describing a new one.
//   WebSite.name is what Google shows as the site name; sameAs ties the name to the store listing.
// RULES: no SearchAction unless the site has search (Google can drop the
//   whole graph over a false claim). Render with <JsonLd data={homeJsonLd()} /> on "/" only;
//   faq/breadcrumb/article per page. Validate one page in the Rich Results test after deploy.
// ─────────────────────────────────────────────────────────────────────────────
const SITE_URL = "https://example.app";                // canonical origin, no trailing slash
const SITE_NAME = "MyApp";
const APP_STORE_NAME = "MyApp: Geography Game";
const PUBLISHER = "MyApp";
const DESCRIPTION = "…";
const APP_STORE_URL = "https://apps.apple.com/app/id0000000000";
const SAME_AS = [APP_STORE_URL /*, Google Play URL, socials */];

const abs = (p: string) => new URL(p, SITE_URL).toString();
const WEBSITE_ID = abs("/#website");
const ORGANIZATION_ID = abs("/#organization");
const APP_ID = abs("/#app");
const logo = { "@type": "ImageObject", url: abs("/icon-512.png"), width: 512, height: 512 };

export function homeJsonLd() {
  return {
    "@context": "https://schema.org",
    "@graph": [
      { "@type": "WebSite", "@id": WEBSITE_ID, url: abs("/"), name: SITE_NAME,
        alternateName: [APP_STORE_NAME], description: DESCRIPTION, inLanguage: "en-US",
        publisher: { "@id": ORGANIZATION_ID } },
      { "@type": "Organization", "@id": ORGANIZATION_ID, name: PUBLISHER, url: abs("/"), logo, sameAs: SAME_AS },
      { "@type": "MobileApplication", "@id": APP_ID, name: SITE_NAME, alternateName: APP_STORE_NAME,
        description: DESCRIPTION, operatingSystem: "iOS", applicationCategory: "GameApplication",
        url: abs("/"), downloadUrl: APP_STORE_URL, installUrl: APP_STORE_URL, sameAs: [APP_STORE_URL],
        image: abs("/icon-512.png"), offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
        publisher: { "@id": ORGANIZATION_ID }, author: { "@id": ORGANIZATION_ID } },
    ],
  };
}

export const faqJsonLd = (items: { q: string; a: string }[]) => ({
  "@context": "https://schema.org", "@type": "FAQPage",
  mainEntity: items.map((i) => ({ "@type": "Question", name: i.q, acceptedAnswer: { "@type": "Answer", text: i.a } })),
});

export const breadcrumbJsonLd = (trail: { name: string; path: string }[]) => ({
  "@context": "https://schema.org", "@type": "BreadcrumbList",
  itemListElement: trail.map((t, i) => ({ "@type": "ListItem", position: i + 1, name: t.name, item: abs(t.path) })),
});

export function articleJsonLd(p: { slug: string; title: string; description: string; date: string; updated?: string }) {
  const url = abs(`/blog/${p.slug}`);
  const publisher = { "@type": "Organization", "@id": ORGANIZATION_ID, name: PUBLISHER, url: abs("/"), logo };
  return { "@context": "https://schema.org", "@type": "Article", headline: p.title, description: p.description,
    datePublished: p.date, dateModified: p.updated ?? p.date, mainEntityOfPage: url, url,
    image: `${url}/opengraph-image`, author: publisher, publisher };
}

// components/JsonLd.tsx:
// export function JsonLd({ data }: { data: object }) {
//   return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }} />;
// }
