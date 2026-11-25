// ─────────────────────────────────────────────────────────────────────────────
// WHAT: robots opens ONLY on VERCEL_ENV=production; explicit NEXT_PUBLIC_SITE_INDEXABLE=false
//   wins; preview and local builds stay Disallow: /. isIndexable is resolved at import time,
//   so each case stubs env and re-imports a fresh module graph.
// ─────────────────────────────────────────────────────────────────────────────
import { describe, it, expect, vi, afterEach } from "vitest";

async function loadRobots() {
  vi.resetModules();
  const [{ default: robots }, { site }] = await Promise.all([import("@/app/robots"), import("@/lib/site")]);
  return { robots, site };
}

afterEach(() => { vi.unstubAllEnvs(); vi.resetModules(); });

describe("robots gate", () => {
  it("disallows everything when the build is explicitly marked non-indexable", async () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_INDEXABLE", "false");
    vi.stubEnv("VERCEL_ENV", "production");
    const res = (await loadRobots()).robots();
    expect(res.rules).toEqual({ userAgent: "*", disallow: "/" });
    expect(res.sitemap).toBeUndefined();
  });

  it("opens up and advertises the sitemap on the production deploy", async () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_INDEXABLE", "");
    vi.stubEnv("VERCEL_ENV", "production");
    const { robots, site } = await loadRobots();
    const res = robots();
    expect(res.rules).toEqual({ userAgent: "*", allow: "/" });
    expect(res.sitemap).toBe(`${site.url}/sitemap.xml`);
  });

  it("keeps preview deploys out of the index", async () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_INDEXABLE", "");
    vi.stubEnv("VERCEL_ENV", "preview");
    expect((await loadRobots()).robots().rules).toEqual({ userAgent: "*", disallow: "/" });
  });

  it("keeps local builds out of the index", async () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_INDEXABLE", "");
    vi.stubEnv("VERCEL_ENV", "");
    expect((await loadRobots()).robots().rules).toEqual({ userAgent: "*", disallow: "/" });
  });
});
