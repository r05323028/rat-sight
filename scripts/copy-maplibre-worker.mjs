import { copyFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repositoryRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
const webRoot = path.join(repositoryRoot, "apps", "web");
const require = createRequire(path.join(webRoot, "package.json"));
const dist = path.join(
  path.dirname(require.resolve("maplibre-gl/package.json")),
  "dist",
);
const destination = path.join(webRoot, "public", "maplibre");

mkdirSync(destination, { recursive: true });
for (const file of ["maplibre-gl-worker.mjs", "maplibre-gl-shared.mjs"]) {
  copyFileSync(path.join(dist, file), path.join(destination, file));
}
