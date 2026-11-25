# Localized App Store listings: brief

<!-- Fill the <…> parts and hand this to a sub-agent. One brief can cover all locales of a release. -->

<App> <version> ships in <languages>. Every language gets its own App Store listing, written for that market
rather than translated from English.

## The app (facts you may state)

<5–10 bullets: what it is, the core loop, content counts, modes/mini-games, what is free and what the
subscription unlocks, no ads (if true), who it is for. Don't put prices in the copy: they vary by storefront.>

What is translated, so the copy never promises more than the app does:
- <language>: <whole app | interface only; content still English → mention the content without naming its language>.
- Names that stay English in every language: <…>.

## Reference

- `appstore/metadata/en-US/` holds the current English listing: name, subtitle, keywords, promo text,
  description, release notes, 10 screenshot headlines (`screenshots.txt`) and subscriptions (`subscriptions.json`).
- `appstore/research.md` has the reasoning behind the English fields. Reuse its logic.
- The app's own UI translations and glossary: <path>. The listing must use the same words the app shows.

## Keyword research (free signals)

`scripts/aso_probe.py`, storefronts <us, mx, es, fr, ca, de, it, br, pt>:
- `hints <cc> "<prefix>"` — App Store autocomplete; what people type is the best signal.
- `depth <cc> "<term>"` — letters typed before the term is suggested; lower = more popular; "-" = never.
- `top <cc> "<term>"` — apps ranking for the term (name, ratings, genre): competition and their title words.
- `batch <cc> file.txt` — depth and top-3 for every line.

Method:
1. Seed with local equivalents of the English winners: <8–15 seed terms>.
2. Expand each seed with `hints` on its first letters, keep what is relevant.
3. Score each term on relevance first, then depth (demand), then competition (ratings of the top 3).
4. Don't parallelize the tool; it pauses between calls on purpose.

## Fields and rules

- **Name** ≤ 30 characters: `<Brand>: <what it is>`, brand first, the market's top term.
- **Subtitle** ≤ 30 characters: the next strongest terms.
- **Keywords** ≤ 100 UTF-8 bytes (an accented letter counts 2): commas with no spaces; no word already in the
  name or subtitle; no singular and plural of the same word; no category words; no competitor brands
  (<list>); prefer strong single words over long phrases (they combine with each other and with name/subtitle).
- **Paired listings in one language** each have their own 100 bytes: split terms between es-MX + es-ES, fr-FR +
  fr-CA, pt-BR + pt-PT. es-MX is also indexed in the US storefront and fr-CA in Canada. Use local vocabulary.
- **Promotional text** ≤ 170 characters.
- **Description** ≤ 4000 characters, the English structure (hook in the first two lines, short CAPS sections with
  • bullets, who it's for), ending with the same legal block as en-US, translated, with the same URLs
  (Apple EULA, <site>/terms, <site>/privacy). Native for the market, not a translation.
- **Release notes** short: "<App> now speaks <language>", 2–3 bullets, a feedback line.
- **screenshots.txt**: 10 headlines in the en-US order; same meaning per slide; ≤ 2 lines split with `<br>`,
  ≤ 22 characters per line; exactly one `<em>…</em>` accent; a searched keyword where natural (screenshot text
  is indexed since 2025); numbers in local format.
- **subscriptions.json**: group (keep the English product name), yearly/monthly name ≤ 30, description ≤ 45.

Check with `python3 scripts/check_meta.py <locale> --brand <brand>` until it prints ok.

Also write `appstore/aso/<locale>.md`: candidate terms with depth and top competitors, what you chose for each
field and why, what you left out. Keep it short; it is the record for the next ASO pass.
