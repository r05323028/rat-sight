import { expect, test } from "@playwright/test";

// Real browser -> FastAPI -> PostGIS smoke for the fixture-only rodent report
// layer. Invoked by scripts/rodent_report_smoke.sh, which starts FastAPI and
// Next.js separately. Only the external basemap style is stubbed; no
// application API route is intercepted. The data is synthetic fixture data.
const STYLE = { version: 8, sources: {}, layers: [] };

const PUBLIC_PROPERTY_KEYS = [
  "action_status",
  "classification",
  "content_sha256",
  "data_class",
  "dataset_id",
  "location_precision",
  "municipal_status",
  "provenance_schema_version",
  "report_id",
  "report_type",
  "reported_at",
  "resource_version",
  "review_status",
  "source",
].sort();

test("renders, filters, selects, and inspects rodent reports from the running FastAPI API", async ({
  page,
}) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via scripts/rodent_report_smoke.sh");
  test.skip(process.env.RODENT_SMOKE_EMPTY === "1", "populated case only");
  await page.route("**/gl/positron-gl-style/style.json", (route) => route.fulfill({ json: STYLE }));

  const responsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/rodent-reports") && response.status() === 200,
  );
  await page.goto("/");
  const body = await (await responsePromise).json();

  // Contract and provenance from the live API.
  expect(body.type).toBe("FeatureCollection");
  expect(body.data_state).toBe("available");
  expect(body.data_class).toBe("RODENT_REPORT");
  expect(body.classification).toBe("SIMULATED");
  expect(body.feature_count).toBe(5);
  expect(body.bbox).toHaveLength(4);
  expect(body.provenance.schema_version).toBe("1");
  expect(body.provenance.source_kind).toBe("synthetic_fixture");
  expect(body.provenance.synthetic).toBe(true);
  expect(body.provenance.content_sha256).toHaveLength(64);

  const first = body.features[0];
  expect(first.type).toBe("Feature");
  expect(first.id).toBe("RR-0001");
  expect(first.geometry.type).toBe("Point");
  expect(first.geometry.coordinates).toHaveLength(2);
  expect(first.properties.report_id).toBe("RR-0001");
  expect(first.properties.data_class).toBe("RODENT_REPORT");
  expect(first.properties.classification).toBe("SIMULATED");
  // Importer-only and coordinate fields must not be duplicated as properties.
  expect(first.properties.longitude).toBeUndefined();
  expect(first.properties.latitude).toBeUndefined();
  expect(first.properties.source_record_id).toBeUndefined();
  expect(Object.keys(first.properties).sort()).toEqual(PUBLIC_PROPERTY_KEYS);

  const panel = page.getByRole("region", { name: "Rodent report inspection" });
  const toggle = page.getByLabel("Rodent reports");
  await expect(toggle).toBeEnabled();
  await toggle.click();
  await expect(toggle).toBeChecked();
  await expect(panel.getByText("RODENT_REPORT · SIMULATED")).toBeVisible();
  await expect(
    panel.getByText(
      "Synthetic report-shaped fixtures. Not verified observations, prevalence, population, movement, or risk evidence.",
    ),
  ).toBeVisible();
  await expect(panel.getByText("synthetic_fixture", { exact: true })).toBeVisible();

  // Select an actual returned point through the keyboard-accessible list.
  const reportButton = panel.getByRole("button", { name: "RR-0001" });
  await expect(reportButton).toBeVisible();
  await reportButton.focus();
  await page.keyboard.press("Enter");
  await expect(reportButton).toHaveAttribute("aria-pressed", "true");
  await expect(panel.getByText("Report ID")).toBeVisible();
  await expect(panel.getByText("RR-0001")).toBeVisible();
  await expect(panel.locator(".reference-details").getByText("sighting_report")).toBeVisible();
  await expect(panel.getByText("Reported at")).toBeVisible();

  // Click an actual MapLibre point: RR-0003 sits at the map center.
  const mapRegion = page.getByRole("region", { name: "Interactive GIS map" });
  await expect(mapRegion).toHaveAttribute("data-rodent-points", "visible");
  const canvas = page.locator(".maplibregl-canvas");
  const box = await canvas.boundingBox();
  if (!box) throw new Error("map canvas is not measurable");
  await canvas.click({ position: { x: box.width / 2, y: box.height / 2 } });
  await expect(panel.getByText("RR-0003")).toBeVisible();
  await expect(panel.locator(".reference-details").getByText("service_request")).toBeVisible();

  // Disabling the layer hides the points but keeps the selected details.
  await toggle.click();
  await expect(toggle).not.toBeChecked();
  await expect(mapRegion).toHaveAttribute("data-rodent-points", "hidden");
  await expect(panel.getByText("RR-0003")).toBeVisible();
  await toggle.click();
  await expect(toggle).toBeChecked();
  await expect(mapRegion).toHaveAttribute("data-rodent-points", "visible");

  // Inclusive time filter with no matches: in-filter empty, no stale details.
  const filtered = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/rodent-reports") &&
      response.url().includes("reported_from=2026-10-10T00%3A00%3A00Z") &&
      response.status() === 200,
  );
  await panel.getByLabel("Reported from (Asia/Taipei, inclusive)").fill("2026-10-10T08:00");
  const filteredBody = await (await filtered).json();
  expect(filteredBody.data_state).toBe("available");
  expect(filteredBody.feature_count).toBe(0);
  expect(filteredBody.reported_from).toBe("2026-10-10T00:00:00Z");
  await expect(
    panel.getByText(/No returned reports match the selected Asia\/Taipei range and viewport/),
  ).toBeVisible();
  await expect(panel.getByText("RR-0001")).toHaveCount(0);
  // Filtering clears the stale map-click selection and its details.
  await expect(panel.getByText("RR-0003")).toHaveCount(0);
  await expect(panel.locator(".reference-details")).toHaveCount(0);

  // Inclusive lower boundary: from 2026-10-01 includes all fixture reports.
  const restored = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/rodent-reports") &&
      response.url().includes("reported_from=2026-10-01T00%3A00%3A00Z") &&
      response.status() === 200,
  );
  await panel.getByLabel("Reported from (Asia/Taipei, inclusive)").fill("2026-10-01T08:00");
  const restoredBody = await (await restored).json();
  expect(restoredBody.feature_count).toBe(5);
  await expect(panel.getByRole("button", { name: "RR-0002" })).toBeVisible();
});

test("reports an empty rodent report store without fabricated points", async ({ page }) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via scripts/rodent_report_smoke.sh");
  test.skip(process.env.RODENT_SMOKE_EMPTY !== "1", "empty case only");
  await page.route("**/gl/positron-gl-style/style.json", (route) => route.fulfill({ json: STYLE }));

  const responsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/rodent-reports") && response.status() === 200,
  );
  await page.goto("/");
  const body = await (await responsePromise).json();
  expect(body.data_state).toBe("empty");
  expect(body.feature_count).toBe(0);
  expect(body.provenance).toBeNull();

  const panel = page.getByRole("region", { name: "Rodent report inspection" });
  await expect(panel.getByText("No synthetic rodent reports have been imported.")).toBeVisible();
  await expect(page.getByLabel("Rodent reports")).toBeDisabled();
  await expect(panel.getByRole("list")).toHaveCount(0);
});
