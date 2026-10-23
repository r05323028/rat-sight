import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([
    ".next/**",
    // Alternate Next build dirs (e.g. the smoke runtime's .next-ratsight-*) are generated.
    ".next-*/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "public/maplibre/**",
  ]),
]);
