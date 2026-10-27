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
    page.getByRole("region", { name: "雨水下水道管線檢視" }).getByText("尚未匯入雨水下水道管線。"),
  ).toBeVisible();
  await expect(page.getByRole("checkbox", { name: "雨水下水道管線" })).toBeDisabled();
});
