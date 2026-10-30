// Map interaction measurement harness.
//
// Run against a real Next.js app, real API, published aggregate snapshot, and pinned
// OSM network. Only the external basemap style is stubbed so measurements do not
// depend on a third-party tile service.
//
//   MEASURE_BASE=http://127.0.0.1:3012 MEASURE_LABEL=after \
//     corepack pnpm --filter @ratsight/web exec node e2e/measure-map-performance.mjs
//
// The script reads the counters that map-view.tsx publishes on `data-map-perf`
// (commits, source/layer builds, setData calls, animation frames). A baseline run
// needs the same counters patched into the older MapView; see
// openspec/changes/optimize-map-interaction-and-animated-simulation/verification/qa.md.
import { chromium } from "@playwright/test";
import { writeFileSync } from "node:fs";

const BASE = process.env.MEASURE_BASE ?? "http://127.0.0.1:3002";
const LABEL = process.env.MEASURE_LABEL ?? "current";
const OUT = process.env.MEASURE_OUT ?? `/tmp/ratsight-map-performance-${LABEL}.json`;

const mercatorY = (latitude) => {
  const sine = Math.sin((latitude * Math.PI) / 180);
  return Math.log((1 + sine) / (1 - sine)) / 2;
};

const percentile = (values, p) => {
  if (values.length === 0) return null;
  const sorted = [...values].sort((left, right) => left - right);
  const index = Math.min(sorted.length - 1, Math.floor((p / 100) * sorted.length));
  return Math.round(sorted[index] * 10) / 10;
};

const stats = (deltas, longTasks) => ({
  samples: deltas.length,
  frameMsP50: percentile(deltas, 50),
  frameMsP95: percentile(deltas, 95),
  frameMsMax: deltas.length ? Math.round(Math.max(...deltas) * 10) / 10 : null,
  longTaskCount: longTasks.length,
  longTaskTotalMs: Math.round(longTasks.reduce((sum, value) => sum + value, 0)),
  longTaskMaxMs: longTasks.length ? Math.round(Math.max(...longTasks)) : 0,
});

const parsePerf = async (mapFrame) => {
  const raw = await mapFrame.getAttribute("data-map-perf");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    // Telemetry is diagnostic only; a malformed sample must not mask the measurement run.
    return null;
  }
};

const main = async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const aggregateRequests = [];
  const pageErrors = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/v1/citizen-report-aggregates")) {
      aggregateRequests.push(request.url());
    }
  });
  page.on("pageerror", (error) => pageErrors.push(String(error)));
  await page.route("**/gl/positron-gl-style/style.json", (route) =>
    route.fulfill({ json: { version: 8, sources: {}, layers: [] } }),
  );

  const mapFrame = page.getByRole("region", { name: "互動式 GIS 地圖" });
  const report = { label: LABEL, base: BASE, viewport: "1440x900", deviceScaleFactor: 1 };

  const startedAt = Date.now();
  await page.goto(`${BASE}/`);
  await mapFrame.waitFor({ state: "visible" });
  await page.waitForSelector('[data-map-ready="true"]', { timeout: 60_000 });
  report.mapReadyMs = Date.now() - startedAt;

  const citizenResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/citizen-report-aggregates") && response.status() === 200,
    { timeout: 40_000 },
  );
  const box = await mapFrame.boundingBox();
  if (!box) throw new Error("map frame has no layout box");
  // The initial Taipei overview is too broad for the bounded aggregate query.
  await mapFrame.dblclick({ position: { x: box.width / 2, y: box.height / 2 } });
  const aggregateBody = await (await citizenResponse).json();
  await page.waitForSelector('[data-citizen-aggregates="visible"]', { timeout: 30_000 });
  await page.waitForTimeout(1200);
  report.aggregateRequestsAfterZoom = aggregateRequests.length;

  const sightings = (aggregateBody.features ?? []).filter(
    (feature) => feature.properties?.report_type === "sighting" && feature.geometry?.coordinates,
  );
  if (sightings.length === 0) throw new Error("no sighting cell in the zoomed aggregate response");
  const centerAttribute = await mapFrame.getAttribute("data-map-center");
  const zoomAttribute = await mapFrame.getAttribute("data-map-zoom");
  const [centerLng, centerLat] = centerAttribute.split(",").map(Number);
  const zoom = Number(zoomAttribute);
  const centroid = (feature) => {
    const points = (feature.geometry.coordinates[0] ?? []).slice(0, -1);
    const [sumLng, sumLat] = points.reduce(
      ([lng, lat], [pointLng, pointLat]) => [lng + pointLng, lat + pointLat],
      [0, 0],
    );
    return [sumLng / points.length, sumLat / points.length];
  };
  const nearest = sightings
    .map((feature) => {
      const [lng, lat] = centroid(feature);
      return { feature, lng, lat, distance: Math.hypot(lng - centerLng, lat - centerLat) };
    })
    .sort((left, right) => left.distance - right.distance)[0];
  const worldSize = 512 * 2 ** zoom;
  const pixelX = box.width / 2 + ((nearest.lng - centerLng) / 360) * worldSize;
  const pixelY =
    box.height / 2 - ((mercatorY(nearest.lat) - mercatorY(centerLat)) * worldSize) / (2 * Math.PI);
  await page.mouse.click(box.x + pixelX, box.y + pixelY);

  const runButton = page.getByRole("button", { name: "以此格網起點執行模擬" });
  await runButton.waitFor({ state: "visible", timeout: 20_000 });
  report.selectedCell = nearest.feature.properties.cell_id;
  report.selectedFeature = `${nearest.feature.properties.cell_id}:${nearest.feature.properties.month}:${nearest.feature.properties.report_type}`;

  const perfBeforePreview = await parsePerf(mapFrame);
  const previewResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/simulations/preview") && response.status() === 200,
    { timeout: 120_000 },
  );
  const previewStartedAt = Date.now();
  await runButton.click();
  const preview = await previewResponse;
  report.previewLatencyMs = Date.now() - previewStartedAt;
  report.previewPayloadBytes = (await preview.body()).length;
  await page.waitForTimeout(300);

  const revealStart = await parsePerf(mapFrame);
  await page.waitForTimeout(1200);
  const revealEnd = await parsePerf(mapFrame);
  report.revealAnimationFrames = revealEnd.animationFrames - revealStart.animationFrames;

  const playbackStart = await parsePerf(mapFrame);
  const individual = page.getByRole("button", { name: "個別路徑" });
  if (await individual.count()) {
    await individual.click();
    await page.waitForTimeout(400);
  }
  const nextStep = page.getByRole("button", { name: "下一步" });
  for (let step = 0; step < 4; step += 1) {
    await nextStep.click();
    await page.waitForTimeout(350);
  }
  await page.waitForTimeout(400);
  const playbackEnd = await parsePerf(mapFrame);
  report.playbackSteps = 4;
  report.playbackLayerBuilds = playbackEnd.layerBuilds - playbackStart.layerBuilds;
  report.playbackSourceBuilds = playbackEnd.sourceBuilds - playbackStart.sourceBuilds;
  report.playbackSetDataCalls = playbackEnd.setDataCalls - playbackStart.setDataCalls;
  report.playbackRenders = playbackEnd.renders - playbackStart.renders;
  report.cumulativeLayerBuilds = playbackEnd.layerBuilds;
  report.cumulativeSourceBuilds = playbackEnd.sourceBuilds;
  report.previewLayerBuilds = perfBeforePreview
    ? playbackStart.layerBuilds - perfBeforePreview.layerBuilds
    : null;
  report.previewSourceBuilds = perfBeforePreview
    ? playbackStart.sourceBuilds - perfBeforePreview.sourceBuilds
    : null;

  // Pan measurement after the simulation is visible, so playback-era layers are loaded.
  const panStartPerf = await parsePerf(mapFrame);
  const panStartRequests = aggregateRequests.length;
  await page.evaluate(() => {
    window.__frames = [];
    window.__long = [];
    window.__rafStart = performance.now();
    const loop = (time) => {
      window.__frames.push(time);
      if (performance.now() - window.__rafStart < 3200) requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
    try {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) window.__long.push(entry.duration);
      }).observe({ type: "longtask", buffered: false });
    } catch {
      // longtask is unavailable in some browsers; frame deltas still measure jank.
    }
  });
  const centerX = box.x + box.width / 2;
  const centerY = box.y + box.height / 2;
  await page.mouse.move(centerX, centerY);
  await page.mouse.down();
  for (let step = 0; step < 24; step += 1) {
    await page.mouse.move(centerX - step * 10, centerY + step * 4);
    await page.waitForTimeout(30);
  }
  await page.mouse.up();
  await page.waitForTimeout(1800);
  const frames = await page.evaluate(() => window.__frames);
  const longTasks = await page.evaluate(() => window.__long);
  const deltas = frames.slice(1).map((time, index) => time - frames[index]);
  const panEndPerf = await parsePerf(mapFrame);
  report.pan = stats(deltas, longTasks);
  report.panAggregateRequests = aggregateRequests.length - panStartRequests;
  report.panRenders = panEndPerf.renders - panStartPerf.renders;

  await page.screenshot({ path: `/tmp/ratsight-map-performance-${LABEL}.png`, fullPage: false });
  report.pageErrors = pageErrors;
  writeFileSync(OUT, JSON.stringify(report, null, 2));
  await browser.close();
  console.log(JSON.stringify(report, null, 2));
};

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
