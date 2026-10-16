import { expect, test } from "@playwright/test";

// This project is invoked by scripts/geospatial_smoke.sh, which starts FastAPI,
// PostGIS, and Next.js separately. No application API route is intercepted here.
test("renders administrative data obtained from the running FastAPI API", async ({ page }) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via make geospatial-smoke");
  // Keep the external basemap deterministic without replacing the application API.
  await page.route("**/gl/positron-gl-style/style.json", (route) =>
    route.fulfill({ json: { version: 8, sources: {}, layers: [] } }),
  );
  const districtsResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/administrative-districts") && response.status() === 200,
  );
  await page.goto("/");
  const response = await districtsResponse;
  const body = await response.json();
  expect(body.data_state).toBe("available");
  expect(body.data_class).toBe("ADMINISTRATIVE_REFERENCE");
  expect(body.provenance.schema_version).toBe("1");
  expect(body.features[0].properties.classification).toBe("UNVERIFIED");
  expect(body.features[0].geometry.type).toBe("Polygon");
  const [longitude, latitude] = body.features[0].geometry.coordinates[0][0];
  expect(longitude).toBeGreaterThanOrEqual(-180);
  expect(longitude).toBeLessThanOrEqual(180);
  expect(latitude).toBeGreaterThanOrEqual(-90);
  expect(latitude).toBeLessThanOrEqual(90);
  await expect(page.getByRole("button", { name: "測試行政區" })).toBeVisible();
  await page.getByRole("button", { name: "測試行政區" }).click();
  await expect(page.getByText("smoke-1")).toBeVisible();
  await expect(page.getByText("RatSight automated test fixture")).toBeVisible();
});
