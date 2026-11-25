// ─────────────────────────────────────────────────────────────────────────────
// WHY IT EXISTS: guides reachable ONLY from the sitemap don't get indexed (a site with single-digit
//   internal links in GSC -> Links). One list feeds footer, home, hubs, the "Guides for this
//   template" block and the sitemap, so a guide cannot ship as an orphan.
// HOW: add a page = add an entry here. tests/guides.test.ts fails if the page file is missing.
//   Order inside a topic matters: the hub goes first (it leads every block it appears in).
// ─────────────────────────────────────────────────────────────────────────────
export type Guide = {
  href: string;
  title: string;
  /** One line for cards and lists. */
  blurb: string;
  topic: "e-invoicing" | "late-payment"; // your clusters
};

export const EINVOICING_GUIDES: Guide[] = [
  { href: "/e-invoicing", title: "E-invoicing: requirements & timeline",
    blurb: "Who must comply, the go-live waves, and what to do now — from the official decisions.",
    topic: "e-invoicing" },
  { href: "/e-invoicing/penalties", title: "E-invoicing penalties",
    blurb: "The fines under the current decision — what it replaced, and the caps.",
    topic: "e-invoicing" },
];

export const LATE_PAYMENT_GUIDES: Guide[] = [
  { href: "/late-payment-calculator", title: "Late payment interest calculator",
    blurb: "Statutory interest and fixed compensation, worked out for you.",
    topic: "late-payment" },
];

export const GUIDES: Guide[] = [...EINVOICING_GUIDES, ...LATE_PAYMENT_GUIDES];
export const getGuide = (href: string) => GUIDES.find((g) => g.href === href);
