import { expect, test } from "@playwright/test";

test("reports empty stormwater storage without fabricated lines", async ({ page }) => {
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
  expect(body.data_state).toBe("empty");
  expect(body.features).toEqual([]);
  await expect(
    page
      .getByRole("region", { name: "Stormwater pipeline inspection" })
      .getByText("No stormwater pipelines have been imported."),
  ).toBeVisible();
  await expect(page.getByLabel("Stormwater pipelines")).toBeDisabled();
});
