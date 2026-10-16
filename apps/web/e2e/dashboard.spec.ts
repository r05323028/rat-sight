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

const STORMWATER_RESPONSE = {
  type: "FeatureCollection",
  data_state: "available",
  data_class: "INFRASTRUCTURE_REFERENCE",
  feature_count: 1,
  bbox: [121.5, 24.98, 121.63, 25.09],
  truncated: false,
  provenance: {
    schema_version: "1",
    source_url: "https://data.taipei/stormwater",
    download_url: "https://data.taipei/stormwater/download",
    dataset_id: "97b82d58-faba-4ee4-9488-dd5d04a79efd",
    resource_id: "5240223d-5187-454e-b323-63443a195639",
    resource_version: "2026-02-23T17:10:41",
    retrieved_at: "2026-10-16T16:58:44Z",
    archive_sha256: "b".repeat(64),
    license: "政府資料開放授權條款-第1版",
    attribution: "臺北市政府工務局",
    source_crs: "EPSG:3826",
    target_crs: "EPSG:4326",
    z_handling: "dropped",
    processing: { tool: "test", tool_version: "0", steps: ["fixture"] },
    source_quality: {
      reference_only: true,
      missing_pipe_number_count: 20,
      duplicate_pipe_number_value_count: 311,
      missing_start_endpoint_count: 991,
      missing_end_endpoint_count: 991,
      missing_notes_count: 17950,
    },
    uncertainty: {
      currentness: "Publisher reference-only; currentness UNVERIFIED",
      note: "fixture",
    },
  },
  features: [
    {
      type: "Feature",
      id: "S-1",
      geometry: {
        type: "LineString",
        coordinates: [
          [121.55, 25.02],
          [121.58, 25.06],
        ],
      },
      properties: {
        segment_id: "S-1",
        data_class: "INFRASTRUCTURE_REFERENCE",
        classification: "UNVERIFIED",
        provenance_schema_version: "1",
        dataset_id: "97b82d58-faba-4ee4-9488-dd5d04a79efd",
        resource_version: "2026-02-23T17:10:41",
        archive_sha256: "b".repeat(64),
        pipe_number: "P-1",
        material: "RCP",
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
  await page.route("**/api/v1/stormwater-pipelines**", (route) =>
    route.fulfill({ json: STORMWATER_RESPONSE }),
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

test("enables the stormwater reference layer and shows its provenance", async ({ page }) => {
  await mockDashboardServices(page, AVAILABLE_BOUNDARIES);
  await page.goto("/");
  const toggle = page.getByLabel("Stormwater pipelines");
  await expect(toggle).toBeEnabled();
  await toggle.check();
  await expect(toggle).toBeChecked();
  const sourceLink = page.getByRole("link", {
    name: "https://data.taipei/stormwater",
    exact: true,
  });
  await expect(sourceLink).toBeVisible();
  await expect(sourceLink).toHaveAttribute("rel", "noopener noreferrer");
  await expect(page.getByText("臺北市政府工務局")).toBeVisible();
  await expect(page.getByText(/Publisher reference-only warning/)).toBeVisible();
});
