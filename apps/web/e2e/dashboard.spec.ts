import { expect, test } from "@playwright/test";

// Frontend-only smoke: API endpoints and map style are mocked.
// API-to-simulation behavior is covered by services/api/tests/test_api.py.
const LAYERS_RESPONSE = [
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
];

const PREVIEW_RESPONSE = {
  simulation_status: "completed",
  classification: "SIMULATED",
  model_id: "synthetic_weighted_random_walk",
  model_version: "0.1.0",
  parameters: {
    study_area: "taipei_synthetic_demo",
    duration_steps: 12,
    walkers: 24,
    random_seed: 42,
    movement_model: "weighted_random_walk",
    intervention_scenario: "baseline",
  },
  provenance: {
    classification: "SIMULATED",
    source_type: "synthetic_fixture",
    source_id: "ratsight-synthetic-graph-v1",
    source_crs: "EPSG:4326",
    note: "synthetic only",
  },
  assumptions: ["synthetic fixture"],
  nodes: [],
  edges: [],
};

const EMPTY_BOUNDARIES = {
  type: "FeatureCollection",
  data_state: "empty",
  data_class: "ADMINISTRATIVE_REFERENCE",
  provenance: null,
  features: [],
};

const AVAILABLE_BOUNDARIES = {
  type: "FeatureCollection",
  data_state: "available",
  data_class: "ADMINISTRATIVE_REFERENCE",
  provenance: {
    schema_version: "1",
    source_url: "https://data.taipei/example",
    dataset_id: "121199",
    resource_version: "20220915",
    retrieved_at: "2026-10-15T00:00:00Z",
    archive_sha256: "a".repeat(64),
    license: "政府資料開放授權條款-第1版",
    attribution: "臺北市政府民政局",
    source_crs: "EPSG:3826",
    target_crs: "EPSG:4326",
    processing: { tool: "test", tool_version: "0", steps: ["fixture"] },
    uncertainty: { currentness: "UNVERIFIED after 2022-09-15", note: "fixture" },
  },
  features: [
    {
      type: "Feature",
      id: "63000010",
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [121.55, 25.02],
            [121.58, 25.02],
            [121.58, 25.06],
            [121.55, 25.02],
          ],
        ],
      },
      properties: {
        district_id: "63000010",
        district_name: "松山區",
        data_class: "ADMINISTRATIVE_REFERENCE",
        classification: "UNVERIFIED",
        provenance_schema_version: "1",
        dataset_id: "121199",
        resource_version: "20220915",
        archive_sha256: "a".repeat(64),
      },
    },
  ],
};

async function mockDashboardServices(page: import("@playwright/test").Page, boundaries: unknown) {
  await page.route("**/gl/positron-gl-style/style.json", (route) =>
    route.fulfill({ json: { version: 8, sources: {}, layers: [] } }),
  );
  await page.route("**/api/v1/layers", (route) => route.fulfill({ json: LAYERS_RESPONSE }));
  await page.route("**/api/v1/simulations/preview", (route) =>
    route.fulfill({ json: PREVIEW_RESPONSE }),
  );
  await page.route("**/api/v1/administrative-districts", (route) =>
    route.fulfill({ json: boundaries }),
  );
}

test("dashboard renders controls, simulation, and the administrative toggle", async ({ page }) => {
  await mockDashboardServices(page, AVAILABLE_BOUNDARIES);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "見光鼠" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Interactive GIS map" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Interactive GIS map" })).toHaveAttribute(
    "data-map-ready",
    "true",
  );
  await expect(page.getByLabel("Duration · steps")).toBeVisible();
  await expect(page.getByLabel("Rodent observations")).toBeDisabled();

  const boundaryToggle = page.getByLabel("Administrative districts");
  await expect(boundaryToggle).toBeEnabled();
  await boundaryToggle.check();
  await expect(boundaryToggle).toBeChecked();

  await page.getByRole("button", { name: "Run synthetic preview" }).click();
  await expect(page.getByRole("status")).toContainText("Reproducible run complete · seed 42");
  await expect(page.getByText("ratsight-synthetic-graph-v1")).toBeVisible();
});

test("dashboard reports the empty administrative boundary state honestly", async ({ page }) => {
  await mockDashboardServices(page, EMPTY_BOUNDARIES);
  await page.goto("/");
  await expect(
    page
      .getByRole("region", { name: "Administrative reference inspection" })
      .getByText("No boundaries imported"),
  ).toBeVisible();
  await expect(page.getByLabel("Administrative districts")).toBeDisabled();
});

test("selects a district through the keyboard-accessible list and shows provenance", async ({
  page,
}) => {
  await mockDashboardServices(page, AVAILABLE_BOUNDARIES);
  await page.goto("/");
  const districtButton = page.getByRole("button", { name: "松山區" });
  await expect(districtButton).toBeVisible();
  await districtButton.focus();
  await page.keyboard.press("Enter");
  await expect(districtButton).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("63000010")).toBeVisible();
  const sourceLink = page.getByRole("link", { name: "https://data.taipei/example" });
  await expect(sourceLink).toBeVisible();
  await expect(sourceLink).toHaveAttribute("rel", "noopener noreferrer");
  await expect(page.getByText("臺北市政府民政局")).toBeVisible();
});
