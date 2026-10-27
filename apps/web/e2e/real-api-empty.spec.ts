import { expect, test } from "@playwright/test";

test("reports an empty administrative dataset from the running FastAPI API", async ({ page }) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via make geospatial-smoke");
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
  expect(body.data_state).toBe("empty");
  expect(body.features).toEqual([]);
  await expect(
    page.getByRole("region", { name: "行政區參考檢視" }).getByText("尚未匯入邊界"),
  ).toBeVisible();
  await expect(page.getByRole("checkbox", { name: "行政區" })).toBeDisabled();
});
