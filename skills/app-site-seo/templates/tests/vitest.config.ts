// oxc.jsx override: tsconfig "jsx: preserve" (Next) otherwise leaves .tsx untransformed under vitest 4.
import { defineConfig } from "vitest/config";
import path from "path";
export default defineConfig({
  oxc: { jsx: { runtime: "automatic" } },
  test: { environment: "node", include: ["tests/**/*.test.{ts,tsx}"] },
  resolve: { alias: { "@": path.resolve(__dirname) } },
});
