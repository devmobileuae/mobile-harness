# Keyword sweeps: the deliverable and how to read SERPs

Shape of the deliverable: a homepage target, ~8 pillar targets with **SERP evidence**, 8 home-FAQ questions and
a rejected list **with reasons**. Produced by parallel research agents (one per angle), then an adversarial
check. Save each site's sweep in its repo (`keywords.md`) and a summary in `local/skills/app-site-seo/`.

## Angles (pick 4–8)

Core category · competitor / alternative · problem-phrased questions ("how to … with irregular …", "know the
rules but still make mistakes") · tool intent (calculator, generator) · privacy / brand vacuum (a retired app,
a data-sharing scandal) · crossovers (astrology × cycle, game × learning).

## Table format

| Slug | Target | Why winnable (SERP on <date>) |
|---|---|---|
| `retired-app-name-app` | <retired app> app | publisher retired it on <date>; SERP = retirement notice + dead APK mirrors → successor angle |
| `predict-x-irregular` | how to predict X with irregular Y | every calculator says "may not work for irregular Y" — the gap is the content |
| `what-phase-am-i-in` | what phase am i in | explainers exist, nobody ships the tool → on-page finder |
| `competitor-alternative` | <competitor> alternative | no dedicated page; tiny /alternatives/ pages rank |
| `in-on-at-exercises` | in on at exercises | 2000s gap-fill sites + a university PDF |

Home: the "<category> app" term whose SERP is app-vendor pages, not an institutional wall.

## Typical rejections (write the reason)

- 9/9 institutional results (clinics, universities, big media) → wall.
- Clinical / teen / sensitive angles in YMYL niches → don't.
- Head calculators owned by a giant + one-shot widget intent → won't convert.
- Intent mismatch (weight loss, lab hardware, a checker tool when you make a practice app) → bounces.
- "Best app for X" → listicle wall.
- A "retired" app that is actually alive → false premise; verify before a successor page.
- Store-listing wall → ASO keyword field instead of a web page.

## App Store popularity as a proxy

AppKittie `get_keyword_difficulty` (US) gives pop/diff for app-store demand. Use it to rank candidates, then open
the live Google SERP for each: an App-Store-popular term may show travel-booking apps (no page answers the app
question → successor-style post), small app sites (go) or a directory holding the top (hardest).

## Head vs tail for programmatic sites

Generic heads ("invoice template", 100k+/mo) are not winnable on a new domain. Tail variants by trade/region are
where pages rank, but on a zero-link domain they take months (pos 50–80 at four months); a reference guide on a
fresh regulation can rank first. Title pattern: `Free <Trade> <Thing> Template — Fill & Download PDF` (≤ 60).

## ASO vs web split

If the web SERP for a term is a wall of App Store listings, the listing *is* the landing page: put the term in the
store keyword field/subtitle (aso-playbook), not a web page. App Store popularity is never a Google volume —
always open the live Google SERP before building.
