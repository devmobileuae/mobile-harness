# Link outreach for a young app site

Keep each campaign's targets, sent emails and tracking log in the site repo (e.g. `LINKS.md`, `OUTREACH.md`) and a
summary in `local/skills/app-site-seo/`. Re-read third-party contact addresses from the target's site before
sending.

## Goal setting

A 4-week-old domain with ~0 referring domains: aim for 15–25 linking root domains in ~6 weeks, 3–8 editorial
links from one linkable asset. Expect directory listings first, editorial links in months, rankings after.

## Tracks (in order of effort-to-value)

| Track | What | Effort | Typical outcome |
|---|---|---|---|
| A Product Hunt | launch kit (tagline ≤60, maker comment, Tue–Thu 00:01 PT) | 1 day | rarely the source of a seen link |
| B Directories | ~20 vetted listings, 3–4 per sitting | ~15 min each | live listings within weeks (many `nofollow`) |
| C Asset outreach | stale-fact corrections + resource additions, 10/week | 30 min/day | slow; "retroactively linking to new resources isn't our usual practice" is a common reply |
| D Expert quotes | MentionMatch, Source of Sources, Qwoted free, #JournoRequest | per query | occasional |
| E Communities | niche subreddits, 10:1 give-to-ask, disclose "I built this" | ongoing | — |
| F New-regulation hook | the same stale-fact hook for pages covering a changed rule | — | time it to the rule's effective dates |

GSC → Links lags weeks and only shows links from pages Google has indexed; a live listing that isn't indexed yet
won't appear.

## Ground rules

- Targets: directories → `/` (or the tool page); outreach → the linkable asset.
- Anchors: brand or natural only, never the money keyword.
- Never: paid link packages, Fiverr/PBN, link exchanges, "write for us" fee farms, auto-submitters,
  **badge-for-dofollow rings** (take the free listing, skip the badge).
- Identity the same everywhere: name, domain, one-liner.
- Send from a domain address (forwarding + Gmail "Send as" with SMTP); some directories reject Gmail. Plain text,
  no attachments, no pixels, Tue–Thu recipient-morning.
- **One** follow-up after 5–7 days, then stop. Log every send the same day.
- Facts in pitches exact and re-verified that day (a rate-check script like `scripts/check-boe-rates.mjs`).
- The owner sends; Claude drafts. Never send on his behalf.

## Directory verdicts (re-verify they are alive before a sitting)

Worth it: Product Hunt · AlternativeTo (**account must be 7 days old** — create it on day 1; list as alternative
to the category leaders) · Tiny Startups · Peerlist Launchpad · Launching Next (free queue, don't pay) · SaaSHub
(its `/submit/list` is a checklist of 100+ more) · MicroLaunch · Crunchbase (nofollow, entity signal) · Show HN ·
Indie Hackers · Capterra/GetApp/Software Advice (one application; decline PPC calls) · G2 (work email). Skip: AI-tool
directories, deal sites, badge rings.

## Templates

**T3 — stale fact correction (highest reply rate; send first).** Find pages quoting an old figure
(`"<topic>" "<old value>" site:<tld>`).

> Subject: <Figure> on your <topic> page
>
> Hi [name],
>
> Your guide at [URL] quotes [figure] at [X] — that was right before [authority] changed it; it has been [Y]
> since [date]. Worth a quick edit.
>
> While checking I built a [tool] that always uses the current figure: [link] — if you'd rather point readers at
> something that stays current, feel free to link it.
>
> Thanks,
> [owner's first name]

Sharpest variant: name the subtle rule the page gets wrong if your tool handles it (e.g. a reference date vs the
live rate).

**T1 — resource addition.** Subject `Small addition to your <topic> resources?`. First line = one specific genuine
remark about their page; then "one thing it doesn't have: …"; one link; "No signup, no ads"; under 120 words.
Lead with **"free, no signup, no email capture"** — charities and advice sites avoid lead-gen tools.

**T2 — professionals.** Subject `A freebie for clients who <problem>`: they get asked, the tool does the work.

**Follow-up (day 5–7):**

> Hi [name] — floating this once in case it sank. The free [tool]: [link]. If it's not a fit, no reply needed.

**Newsjack hook:** a dated event the target is already covering (a bill's next stage, verified the day before);
describe the effect, not clause numbers.

## Lessons

- Cold outreach from a 1-month-old domain produces directory listings, not editorial links. Budget it as slow;
  don't promise ranking movement from it.
- The strongest asset is a page that **corrects** something (rates, penalties, deadlines). Keep it re-verified —
  a stale linkable asset is worse than none.
- Keep a "dropped after checking" list per campaign (lapsed sites, domains for sale, no editorial route).
