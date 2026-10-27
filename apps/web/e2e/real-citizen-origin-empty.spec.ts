import { expect, test } from "@playwright/test";

test("reports an empty synthetic aggregate fixture without citizen substitution", async ({
  page,
}) => {
  test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, "run via make geospatial-smoke");
  await page.route("**/gl/positron-gl-style/style.json", (route) =>
    route.fulfill({ json: { version: 8, sources: {}, layers: [] } }),
  );
  const mapFrame = page.getByRole("region", { name: "互動式 GIS 地圖" });
  const citizenResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/citizen-report-aggregates") && response.status() === 200,
    { timeout: 20_000 },
  );
  await page.goto("/");
  await expect(mapFrame).toBeVisible();
  const box = await mapFrame.boundingBox();
  if (!box) throw new Error("map frame has no layout box");
  const position = { x: box.width / 2, y: box.height / 2 };
  await mapFrame.dblclick({ position });

  const body = await (await citizenResponse).json();
  expect(body.data_state).toBe("empty");
  expect(body.data_class).toBe("SYNTHETIC_AGGREGATE_FIXTURE");
  expect(body.classification).toBe("SIMULATED");
  expect(body.features).toEqual([]);
  expect(body.provenance).toBeNull();

  const panel = page.getByRole("region", { name: "本機合成測試格檢視" });
  await expect(panel).toBeVisible();
  await expect(panel.getByText("SIMULATED · 合成測試")).toBeVisible();
  await expect(panel.getByText(/尚無本機合成測試格/)).toBeVisible();
  await expect(panel.getByText(/資料庫尚未匯入本機測試夾具/)).toBeVisible();
  await expect(panel.getByLabel("選擇本機合成測試格")).toHaveCount(0);
  await expect(page.getByRole("region", { name: "公民通報彙整檢視" })).toHaveCount(0);
});
