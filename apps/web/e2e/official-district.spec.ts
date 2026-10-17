import { expect, test } from "@playwright/test";

test("inspects the imported official administrative district layer", async ({ page }) => {
  test.skip(!process.env.OFFICIAL_DISTRICTS, "one-time official verification only");
  await page.route("**/gl/positron-gl-style/style.json", (route) =>
    route.fulfill({ json: { version: 8, sources: {}, layers: [] } }),
  );
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/administrative-districts") && response.status() === 200,
  );
  await page.goto("/");
  const body = await (await responsePromise).json();
  expect(body.data_state).toBe("available");
  expect(body.features).toHaveLength(12);
  expect(body.provenance.dataset_id).toBe("121199");
  const toggle = page.getByLabel("Administrative districts");
  await expect(toggle).toBeEnabled();
  await toggle.click();
  await expect(toggle).toBeChecked();
  const district = page.getByRole("button").filter({ hasText: /區/ }).first();
  await expect(district).toBeVisible();
  await district.click();
  await expect(page.getByText("ADMINISTRATIVE_REFERENCE")).toBeVisible();
});
