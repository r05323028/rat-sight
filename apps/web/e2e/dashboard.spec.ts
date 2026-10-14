import { expect, test } from "@playwright/test";

test("dashboard renders controls and map shell", async ({ page }) => {
  await page.route("**/gl/positron-gl-style/style.json", (route) =>
    route.fulfill({ json: { version: 8, sources: {}, layers: [] } }),
  );
  await page.route("**/api/v1/layers", (route) =>
    route.fulfill({
      json: [
        {
          id: "rodent_observations",
          label: "Rodent observations",
          available: false,
          classification: null,
          message: "No observation dataset loaded.",
        },
        {
          id: "sewer_networks",
          label: "Sewer networks",
          available: false,
          classification: null,
          message: "No sewer dataset loaded.",
        },
        {
          id: "stormwater_networks",
          label: "Stormwater networks",
          available: false,
          classification: null,
          message: "No stormwater dataset loaded.",
        },
        {
          id: "surface_corridors",
          label: "Surface movement corridors",
          available: false,
          classification: null,
          message: "No corridor dataset loaded.",
        },
        {
          id: "human_activity",
          label: "Human activity",
          available: false,
          classification: null,
          message: "No human-activity dataset loaded.",
        },
        {
          id: "environmental_conditions",
          label: "Environmental conditions",
          available: false,
          classification: null,
          message: "No environmental dataset loaded.",
        },
        {
          id: "simulated_paths",
          label: "Simulated movement paths",
          available: false,
          classification: "SIMULATED",
          message: "Available after a synthetic preview.",
        },
      ],
      headers: { "Access-Control-Allow-Origin": "*" },
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "見光鼠" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Interactive GIS map" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Interactive GIS map" })).toHaveAttribute(
    "data-map-ready",
    "true",
  );
  await expect(page.getByLabel("Duration · steps")).toBeVisible();
  await expect(page.getByLabel("Rodent observations")).toBeDisabled();
  await page.getByRole("button", { name: "Run synthetic preview" }).click();
  await expect(page.getByRole("status")).toContainText("Reproducible run complete · seed 42");
  await expect(page.getByText("ratsight-synthetic-graph-v1")).toBeVisible();
});
