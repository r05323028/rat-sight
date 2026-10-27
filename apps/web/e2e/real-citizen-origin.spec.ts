import { expect, test } from "@playwright/test";
import type { Locator, Page, Route } from "@playwright/test";

// Invoked by scripts/geospatial_smoke.sh against a disposable PostGIS database,
// the real FastAPI process, the pinned local OSM graph, and Next.js. Only the
// external basemap is replaced; application API calls reach the real services.
const FIXTURE_CELL = "smoke-cell-1:2026-01:sighting";
const OTHER_FIXTURE_CELL = "smoke-cell-2:2026-01:sighting";
const CARD_NAME = "本機合成測試格詳細資料";
const PANEL_NAME = "本機合成測試格檢視";

async function openCitizenFixture(page: Page) {
  await page.route("**/gl/positron-gl-style/style.json", (route) =>
    route.fulfill({ json: { version: 8, sources: {}, layers: [] } }),
  );
  const mapFrame = page.getByRole("region", { name: "互動式 GIS 地圖" });
  await page.goto("/");
  await expect(mapFrame).toBeVisible();
  const box = await mapFrame.boundingBox();
  if (!box) throw new Error("map frame has no layout box");
  const position = { x: box.width / 2, y: box.height / 2 };
  // The initial Taipei overview is too broad for the bounded aggregate query.
  // One zoom at the fixture node is enough; wait for that viewport's response.
  const citizenResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/citizen-report-aggregates") && response.status() === 200,
    { timeout: 20_000 },
  );
  await mapFrame.dblclick({ position });
  const body = await (await citizenResponse).json();
  await expect(mapFrame).toHaveAttribute("data-map-zoom", /12/);
  await expect(mapFrame).toHaveAttribute("data-citizen-aggregates", "visible");
  await expect(page.getByRole("region", { name: PANEL_NAME })).toBeVisible();
  return { mapFrame, body };
}

function mercatorY(latitude: number): number {
  const sine = Math.sin((latitude * Math.PI) / 180);
  return Math.log((1 + sine) / (1 - sine)) / 2;
}

async function clickCitizenCell(
  page: Page,
  mapFrame: Locator,
  feature: { geometry: { coordinates: number[][][] } },
) {
  const box = await mapFrame.boundingBox();
  if (!box) throw new Error("map frame has no layout box");
  const centerAttribute = await mapFrame.getAttribute("data-map-center");
  const zoomAttribute = await mapFrame.getAttribute("data-map-zoom");
  if (!centerAttribute || !zoomAttribute) throw new Error("map transform is unavailable");
  const [centerLongitude, centerLatitude] = centerAttribute.split(",").map(Number);
  const zoom = Number(zoomAttribute);
  const ring = feature.geometry.coordinates[0] ?? [];
  const points = ring.slice(0, -1);
  if (points.length === 0) throw new Error("citizen cell has no polygon ring");
  const [longitude, latitude] = points
    .reduce(
      ([sumLongitude, sumLatitude], [pointLongitude, pointLatitude]) => [
        sumLongitude + pointLongitude,
        sumLatitude + pointLatitude,
      ],
      [0, 0],
    )
    .map((sum) => sum / points.length);
  const worldSize = 512 * 2 ** zoom;
  const x = box.width / 2 + ((longitude - centerLongitude) / 360) * worldSize;
  const y =
    box.height / 2 -
    ((mercatorY(latitude) - mercatorY(centerLatitude)) * worldSize) / (2 * Math.PI);
  await page.mouse.click(box.x + x, box.y + y);
}

test("runs, plays back, and switches an isolated citizen-origin fixture", async ({ page }) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via make geospatial-smoke");
  // The pinned OSM graph makes the real preview request slower than the default
  // 30 s test budget on a cold process.
  test.setTimeout(120_000);
  const { mapFrame, body } = await openCitizenFixture(page);
  expect(body.data_state).toBe("available");
  expect(body.data_class).toBe("SYNTHETIC_AGGREGATE_FIXTURE");
  expect(body.classification).toBe("SIMULATED");
  expect(body.features.length).toBeGreaterThanOrEqual(2);
  const fixture = body.features.find(
    (feature: { properties: { cell_id: string } }) => feature.properties.cell_id === "smoke-cell-1",
  );
  expect(fixture.properties.count).toBeNull();
  expect(fixture.properties.data_class).toBe("SYNTHETIC_AGGREGATE_FIXTURE");
  expect(fixture.properties.classification).toBe("SIMULATED");
  expect(body.provenance.synthetic).toBe(true);
  expect(body.provenance.test_scope).toBe("isolated_disposable_postgis_smoke");
  expect(body.provenance.cell_size_meters).toBe(250);

  const panel = page.getByRole("region", { name: PANEL_NAME });
  await expect(panel.getByText("SMULATED", { exact: false })).toHaveCount(0);
  await expect(panel.getByText(/SIMULATED/).first()).toBeVisible();
  await expect(panel.getByText(/不含公民通報/).first()).toBeVisible();

  await clickCitizenCell(page, mapFrame, fixture);
  const card = page.getByRole("complementary", { name: CARD_NAME });
  await expect(card).toBeVisible();
  await expect(card.getByText("smoke-cell-1")).toBeVisible();
  await expect(card.getByText("SIMULATED · 本機測試")).toBeVisible();
  await expect(card.getByText("發布通報計數")).toHaveCount(0);

  const requestPromise = page.waitForRequest(
    (request) =>
      request.url().endsWith("/api/v1/simulations/preview") && request.method() === "POST",
  );
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/simulations/preview") && response.status() === 200,
  );
  await card.getByRole("button", { name: "以此格網起點執行模擬" }).click();
  const request = await requestPromise;
  const payload = request.postDataJSON() as Record<string, unknown>;
  expect(payload.study_area).toBe("taipei_osm_songshan");
  expect(payload.origin_cell_id).toBe(FIXTURE_CELL);
  expect(payload).not.toHaveProperty("origin_node_id");
  const preview = await (await responsePromise).json();
  expect(preview.classification).toBe("SIMULATED");
  expect(preview.origin.cell_id).toBe(FIXTURE_CELL);
  expect(preview.origin.selection).toBe("cell");
  expect(preview.origin.source_data_class).toBe("SYNTHETIC_AGGREGATE_FIXTURE");
  expect(preview.origin.source_classification).toBe("SIMULATED");
  expect(preview.origin.cell_candidate_count).toBeGreaterThanOrEqual(1);
  expect(preview.trajectories.length).toBeGreaterThan(0);
  const walkable = preview.trajectories.find(
    (trajectory: { edges: unknown[] }) => trajectory.edges.length >= 2,
  );
  expect(walkable).toBeTruthy();

  const playback = page.getByRole("region", { name: "模擬軌跡播放控制" });
  await expect(playback).toBeVisible();
  await expect(playback.getByText(`SIMULATED · 起點 ${FIXTURE_CELL}`)).toBeVisible();
  await playback.getByRole("button", { name: "個別路徑" }).click();
  await playback.getByLabel("選擇行走者").selectOption(String(walkable.walker_id));
  const stepText = playback.getByText(/步驟 \d+ \/ \d+ · 非實際時間/);
  await expect(stepText).toHaveText(`步驟 0 / ${walkable.edges.length} · 非實際時間`);

  await playback.getByRole("button", { name: "播放" }).click();
  const pause = playback.getByRole("button", { name: "暫停" });
  await expect(pause).toBeVisible();
  await pause.click();
  await expect(playback.getByRole("button", { name: "播放" })).toBeVisible();
  await playback.getByRole("button", { name: "下一步" }).click();
  await expect(stepText).toHaveText(`步驟 1 / ${walkable.edges.length} · 非實際時間`);
  await playback.getByRole("button", { name: "上一步" }).click();
  await expect(stepText).toHaveText(`步驟 0 / ${walkable.edges.length} · 非實際時間`);
  await expect(playback.getByRole("button", { name: "重設" })).toBeDisabled();
  await playback.getByRole("button", { name: "下一步" }).click();
  await expect(stepText).toHaveText(`步驟 1 / ${walkable.edges.length} · 非實際時間`);
  await playback.getByRole("button", { name: "重設" }).click();
  await expect(stepText).toHaveText(`步驟 0 / ${walkable.edges.length} · 非實際時間`);
  await playback.getByRole("button", { name: "彙整路線" }).click();
  await expect(playback.getByRole("button", { name: "彙整路線" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );

  // Selecting another origin must not leave the previous origin's output labeled
  // as the newly selected cell.
  await page.getByLabel("選擇本機合成測試格").selectOption(OTHER_FIXTURE_CELL);
  await expect(playback).toHaveCount(0);
  const otherCard = page.getByRole("complementary", { name: CARD_NAME });
  await expect(otherCard.getByText("smoke-cell-2")).toBeVisible();
  await expect(otherCard.getByText("smoke-cell-1")).toHaveCount(0);
  await expect(page.getByText(`起點 ${FIXTURE_CELL}`)).toHaveCount(0);
});

test("ignores an out-of-order response from a previous origin", async ({ page }) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via make geospatial-smoke");
  test.setTimeout(120_000);
  let heldRoute: Route | undefined;
  let releaseHeld!: () => void;
  const held = new Promise<void>((resolve) => {
    releaseHeld = resolve;
  });
  await page.route("**/api/v1/simulations/preview", async (route) => {
    if (!heldRoute) {
      heldRoute = route;
      await held;
      await route.continue();
      return;
    }
    await route.continue();
  });

  await openCitizenFixture(page);
  const picker = page.getByLabel("選擇本機合成測試格");
  await picker.selectOption(FIXTURE_CELL);
  const card = page.getByRole("complementary", { name: CARD_NAME });
  await expect(card.getByText("smoke-cell-1")).toBeVisible();
  await card.getByRole("button", { name: "以此格網起點執行模擬" }).click();
  await expect.poll(() => Boolean(heldRoute)).toBe(true);
  await expect(card.getByRole("button", { name: "模擬執行中…" })).toBeVisible();

  await picker.selectOption(OTHER_FIXTURE_CELL);
  await expect(card.getByText("smoke-cell-2")).toBeVisible();
  const secondResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/simulations/preview") && response.status() === 200,
  );
  await card.getByRole("button", { name: "以此格網起點執行模擬" }).click();
  const secondPreview = await (await secondResponse).json();
  expect(secondPreview.origin.cell_id).toBe(OTHER_FIXTURE_CELL);
  const playback = page.getByRole("region", { name: "模擬軌跡播放控制" });
  await expect(playback.getByText(`SIMULATED · 起點 ${OTHER_FIXTURE_CELL}`)).toBeVisible();

  releaseHeld();
  await page.waitForTimeout(800);
  await expect(playback.getByText(`SIMULATED · 起點 ${OTHER_FIXTURE_CELL}`)).toBeVisible();
  await expect(playback.getByText(`SIMULATED · 起點 ${FIXTURE_CELL}`, { exact: true })).toHaveCount(
    0,
  );
});

test("reports an unavailable aggregate service without a synthetic fallback", async ({ page }) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via make geospatial-smoke");
  await page.route("**/gl/positron-gl-style/style.json", (route) =>
    route.fulfill({ json: { version: 8, sources: {}, layers: [] } }),
  );
  await page.route("**/api/v1/citizen-report-aggregates*", (route) =>
    route.fulfill({ status: 503, json: { detail: "unavailable" } }),
  );
  const mapFrame = page.getByRole("region", { name: "互動式 GIS 地圖" });
  const failedResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/citizen-report-aggregates") && response.status() === 503,
  );
  await page.goto("/");
  await expect(mapFrame).toBeVisible();
  const box = await mapFrame.boundingBox();
  if (!box) throw new Error("map frame has no layout box");
  await mapFrame.dblclick({ position: { x: box.width / 2, y: box.height / 2 } });
  await failedResponse;

  const panel = page.getByRole("region", { name: "公民通報彙整檢視" });
  await expect(panel.getByText("公民通報彙整服務無法使用")).toBeVisible();
  await expect(panel.getByText(/不顯示代替資料/)).toBeVisible();
  await expect(page.getByRole("region", { name: "本機合成測試格檢視" })).toHaveCount(0);
  await expect(page.getByRole("region", { name: "模擬軌跡播放控制" })).toHaveCount(0);
});

test("reports a generic simulation failure without retaining a success view", async ({ page }) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via make geospatial-smoke");
  await page.route("**/api/v1/simulations/preview", (route) =>
    route.fulfill({ status: 503, json: { detail: "unavailable" } }),
  );
  await openCitizenFixture(page);
  await page.getByLabel("選擇本機合成測試格").selectOption(FIXTURE_CELL);
  const card = page.getByRole("complementary", { name: CARD_NAME });
  await expect(card.getByText("smoke-cell-1")).toBeVisible();
  await card.getByRole("button", { name: "以此格網起點執行模擬" }).click();
  await expect(card.getByRole("alert")).toHaveText("Simulation preview failed (503)");
  await expect(page.getByRole("region", { name: "模擬軌跡播放控制" })).toHaveCount(0);
});

test("reports unavailable OSM source without substituting the schematic network", async ({
  page,
}) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via make geospatial-smoke");
  await page.route("**/api/v1/simulations/preview", (route) =>
    route.fulfill({
      status: 503,
      json: {
        detail: {
          code: "SOURCE_NETWORK_UNAVAILABLE",
          message: "pinned OSM missing",
          provisioning: "provision the source.",
        },
      },
    }),
  );
  await openCitizenFixture(page);
  await page.getByLabel("選擇本機合成測試格").selectOption(FIXTURE_CELL);
  const card = page.getByRole("complementary", { name: CARD_NAME });
  await card.getByRole("button", { name: "以此格網起點執行模擬" }).click();
  const alert = card.getByRole("alert");
  await expect(alert).toContainText("來源網路無法使用：pinned OSM missing");
  await expect(alert).toContainText("系統未以示意網路替代 OSM 結果。");
  await expect(page.getByRole("region", { name: "模擬軌跡播放控制" })).toHaveCount(0);
});

test("reports an unresolvable citizen cell without a default graph origin", async ({ page }) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via make geospatial-smoke");
  await page.route("**/api/v1/simulations/preview", (route) =>
    route.fulfill({
      status: 422,
      json: {
        detail: {
          code: "ORIGIN_CELL_NOT_RESOLVABLE",
          message: "no eligible node inside cell",
        },
      },
    }),
  );
  await openCitizenFixture(page);
  await page.getByLabel("選擇本機合成測試格").selectOption(FIXTURE_CELL);
  const card = page.getByRole("complementary", { name: CARD_NAME });
  await card.getByRole("button", { name: "以此格網起點執行模擬" }).click();
  await expect(card.getByRole("alert")).toContainText(
    "公民通報格網起點無法解析：no eligible node inside cell",
  );
  await expect(page.getByRole("region", { name: "模擬軌跡播放控制" })).toHaveCount(0);
});

test("clears selected output when the refreshed source no longer publishes the cell", async ({
  page,
}) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via make geospatial-smoke");
  test.setTimeout(120_000);
  await openCitizenFixture(page);
  await page.getByLabel("選擇本機合成測試格").selectOption(FIXTURE_CELL);
  const card = page.getByRole("complementary", { name: CARD_NAME });
  const previewResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/simulations/preview") && response.status() === 200,
  );
  await card.getByRole("button", { name: "以此格網起點執行模擬" }).click();
  await previewResponse;
  const playback = page.getByRole("region", { name: "模擬軌跡播放控制" });
  await expect(playback.getByText(`SIMULATED · 起點 ${FIXTURE_CELL}`)).toBeVisible();

  await page.route("**/api/v1/citizen-report-aggregates*", (route) =>
    route.fulfill({
      json: {
        type: "FeatureCollection",
        data_state: "empty",
        data_class: "SYNTHETIC_AGGREGATE_FIXTURE",
        classification: "SIMULATED",
        provenance: null,
        features: [],
      },
    }),
  );
  const refreshed = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/citizen-report-aggregates") && response.status() === 200,
  );
  await page.getByRole("button", { name: "放大地圖" }).click();
  await refreshed;

  const panel = page.getByRole("region", { name: "本機合成測試格檢視" });
  await expect(panel.getByText(/尚無本機合成測試格/)).toBeVisible();
  await expect(page.getByRole("complementary", { name: CARD_NAME })).toHaveCount(0);
  await expect(playback).toHaveCount(0);
});
