import { expect, test } from "@playwright/test";

test("renders and inspects stormwater data from the running FastAPI API", async ({ page }) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via make geospatial-smoke");
  await page.route("**/gl/positron-gl-style/style.json", (route) =>
    route.fulfill({ json: { version: 8, sources: {}, layers: [] } }),
  );
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/stormwater-pipelines") && response.status() === 200,
  );
  await page.goto("/");
  const body = await (await responsePromise).json();
  expect(body.data_state).toBe("available");
  expect(body.data_class).toBe("INFRASTRUCTURE_REFERENCE");
  expect(body.provenance.z_handling).toBe("dropped");
  expect(body.features[0].geometry.type).toBe("LineString");
  const toggle = page.getByLabel("Stormwater pipelines");
  await expect(toggle).toBeEnabled();
  await toggle.check();
  await expect(
    page.getByText("Select a pipeline from the list or the map to inspect its source attributes."),
  ).toBeVisible();
  await expect(page.getByText("Publisher reference-only warning")).toBeVisible();
  await expect(page.getByText("Not verified physical connectivity.")).toBeVisible();
  const inspection = page.getByRole("region", { name: "Stormwater pipeline inspection" });
  const firstPipeline = inspection.getByRole("list").getByRole("button").first();
  await expect(firstPipeline).toBeVisible();
  await firstPipeline.click();
  await expect(inspection.getByText("Segment ID")).toBeVisible();
  await expect(inspection.getByText("INFRASTRUCTURE_REFERENCE").last()).toBeVisible();
});
