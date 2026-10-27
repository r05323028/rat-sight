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
  const toggle = page.getByRole("checkbox", { name: "雨水下水道管線" });
  await expect(toggle).toBeEnabled();
  await toggle.click();
  await expect(toggle).toBeChecked();
  await expect(page.getByText("從清單或地圖選取管線，以檢視來源屬性。")).toBeVisible();
  await page.getByText("雨水下水道來源、授權與現勢性").click();
  await expect(
    page.getByText("發布機關僅供參考警示：請僅作參考；如需精確資料，請向權責公用事業機關取得。"),
  ).toBeVisible();
  await expect(
    page.getByText("未驗證實際連通性。起點／終點節點值僅為發布機關屬性。"),
  ).toBeVisible();
  const inspection = page.getByRole("region", { name: "雨水下水道管線檢視" });
  const firstPipeline = inspection.getByRole("list").getByRole("button").first();
  await expect(firstPipeline).toBeVisible();
  const visiblePipelineName = (await firstPipeline.textContent())?.trim();
  const accessiblePipelineName = await firstPipeline.getAttribute("aria-label");
  expect(visiblePipelineName).toBeTruthy();
  expect(accessiblePipelineName?.startsWith(visiblePipelineName ?? "")).toBe(true);
  await firstPipeline.click();
  await expect(inspection.getByText("管段 ID")).toBeVisible();
  await expect(inspection.getByText("INFRASTRUCTURE_REFERENCE").last()).toBeVisible();
});
