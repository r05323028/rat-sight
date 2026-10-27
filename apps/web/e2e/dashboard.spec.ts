import { expect, test } from "@playwright/test";

// Frontend-only smoke: API endpoints and map style are mocked.
// API-to-simulation behavior is covered by services/api/tests/test_api.py.
const LAYERS_RESPONSE = [
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
    origin_node_id: "a",
  },
  origin: {
    node_id: "a",
    coordinates: [121.55, 25.02],
    classification: "SIMULATED",
    selection: "default",
    note: "Synthetic model input; not an observed or reported animal origin.",
  },
  provenance: {
    classification: "SIMULATED",
    source_type: "synthetic_fixture",
    source_id: "ratsight-synthetic-graph-v1",
    source_crs: "EPSG:4326",
    note: "synthetic only",
  },
  assumptions: ["synthetic fixture"],
  nodes: [
    {
      id: "a",
      coordinates: [121.55, 25.02],
      visits: 1,
      probability: 0.5,
      classification: "SIMULATED",
    },
    {
      id: "b",
      coordinates: [121.56, 25.03],
      visits: 1,
      probability: 0.5,
      classification: "SIMULATED",
    },
  ],
  edges: [],
  trajectories: [
    {
      walker_id: 1,
      classification: "SIMULATED",
      edges: [
        {
          source: "a",
          target: "b",
          edge_id: "e1",
          step_index: 0,
          geometry: [
            [121.55, 25.02],
            [121.56, 25.03],
          ],
          classification: "SIMULATED",
        },
      ],
    },
  ],
  trajectory_count: 1,
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
  await page.route("**/api/v1/simulations/preview", (route) => {
    const requested = (route.request().postDataJSON() as { origin_node_id?: string } | null)
      ?.origin_node_id;
    const node = PREVIEW_RESPONSE.nodes.find((candidate) => candidate.id === requested);
    route.fulfill({
      json: requested
        ? {
            ...PREVIEW_RESPONSE,
            parameters: { ...PREVIEW_RESPONSE.parameters, origin_node_id: requested },
            origin: {
              ...PREVIEW_RESPONSE.origin,
              node_id: requested,
              coordinates: node?.coordinates ?? PREVIEW_RESPONSE.origin.coordinates,
              selection: "user",
            },
          }
        : PREVIEW_RESPONSE,
    });
  });
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
  await expect(page.getByRole("region", { name: "互動式 GIS 地圖" })).toBeVisible();
  await expect(page.getByRole("region", { name: "互動式 GIS 地圖" })).toHaveAttribute(
    "data-map-ready",
    "true",
  );
  await expect(page.getByRole("button", { name: "開始模擬" })).toBeVisible();
  await expect(page.getByLabel("模擬長度 · 步數")).toBeHidden();
  await page.getByText(/進階設定 ·/).click();
  await expect(page.getByLabel("模擬長度 · 步數")).toBeVisible();
  await expect(page.getByRole("button", { name: "放大地圖" })).toBeVisible();
  await expect(page.getByRole("button", { name: "縮小地圖" })).toBeVisible();
  await expect(page.getByRole("button", { name: "重設地圖方向" })).toBeVisible();
  await expect(
    page.locator(".layer-row", { hasText: "鼠類觀測" }).getByText("未載入", { exact: true }),
  ).toBeVisible();

  const boundaryToggle = page.getByLabel("行政區", { exact: true });
  await expect(boundaryToggle).toBeEnabled();
  await boundaryToggle.click();
  await expect(boundaryToggle).toBeChecked();

  await page.getByRole("button", { name: "開始模擬" }).click();
  await expect(page.getByRole("status")).toContainText("可重現執行完成 · 種子 42");
  await page.getByText("模擬來源與版本").click();
  await expect(page.getByText("ratsight-synthetic-graph-v1")).toBeVisible();

  await page.getByLabel("輸出模式").selectOption("trajectory");
  await expect(page.getByLabel("模擬摘要")).toContainText("1 條合成軌跡（SIMULATED）");
  await expect(page.getByLabel("模擬摘要")).not.toContainText("節點造訪");
  await expect(page.getByLabel("模擬移動路徑")).toBeChecked();
  // Reachability is stated as graph-derived and never as absence of animals.
  await expect(page.locator(".analysis-row", { hasText: "可達節點" })).toContainText("個模型節點");
  await expect(page.getByText(/可達性由 API 回傳的模型節點與邊計算/)).toContainText(
    /不代表沒有動物/,
  );
  await expect(page.locator(".analysis-row", { hasText: "合成起點" })).toContainText(
    "a · 25.02000, 121.55000 · 預設固定起點 · SIMULATED",
  );
  // Playback walks the returned steps; it is not elapsed time.
  await expect(page.getByText("步驟 0 / 1")).toBeVisible();
  await page.getByRole("button", { name: "下一步" }).click();
  await expect(page.getByText("步驟 1 / 1")).toBeVisible();
  await expect(page.getByRole("button", { name: /步驟 1（step_index 0）/ })).toHaveAttribute(
    "aria-current",
    "step",
  );

  // The fitted preview extent puts the trajectory through the map centre, so a
  // plain coordinate click must reach the path instead of the basemap.
  if ((page.viewportSize()?.width ?? 0) >= 900) {
    const canvasBox = await page.locator(".maplibregl-canvas").boundingBox();
    await page.mouse.click(
      canvasBox!.x + canvasBox!.width / 2,
      canvasBox!.y + canvasBox!.height / 2,
    );
    await expect(page.locator(".map-selection")).toContainText("模擬軌跡 #1");
    await expect(page.locator(".map-selection")).toContainText("SIMULATED");
  }

  // Choosing a returned network node is sent to the API and disclosed as user-selected.
  const originSelect = page.getByLabel("合成起點節點");
  if (!(await originSelect.isVisible())) {
    await page.locator("details.advanced-settings > summary").click();
  }
  await expect(originSelect).toBeVisible();
  await originSelect.selectOption("b");
  await expect(page.locator(".analysis-row", { hasText: "合成起點" })).toContainText(
    "已選擇，尚未以此外起點執行",
  );
  await page.getByRole("button", { name: "開始模擬" }).click();
  await expect(page.getByRole("status")).toContainText("可重現執行完成");
  await expect(page.locator(".analysis-row", { hasText: "合成起點" })).toContainText(
    "b · 25.03000, 121.56000 · 使用者選擇 · SIMULATED",
  );
});

test("dashboard reports the empty administrative boundary state honestly", async ({ page }) => {
  await mockDashboardServices(page, EMPTY_BOUNDARIES);
  await page.goto("/");
  await expect(
    page.getByRole("region", { name: "行政區參考檢視" }).getByText("尚未匯入邊界"),
  ).toBeVisible();
  await expect(page.getByLabel("行政區", { exact: true })).toBeDisabled();
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
  await page.getByText("行政區來源、授權與現勢性").click();
  const sourceLink = page.getByRole("link", { name: "https://data.taipei/example" });
  await expect(sourceLink).toBeVisible();
  await expect(sourceLink).toHaveAttribute("rel", "noopener noreferrer");
  await expect(page.getByText("臺北市政府民政局")).toBeVisible();
});

test("enables the stormwater reference layer and shows its provenance", async ({ page }) => {
  await mockDashboardServices(page, AVAILABLE_BOUNDARIES);
  await page.goto("/");
  const toggle = page.getByLabel("雨水下水道管線", { exact: true });
  await expect(toggle).toBeEnabled();
  await toggle.click();
  await expect(toggle).toBeChecked();
  await page.getByText("雨水下水道來源、授權與現勢性").click();
  const sourceLink = page.getByRole("link", {
    name: "https://data.taipei/stormwater",
    exact: true,
  });
  await expect(sourceLink).toBeVisible();
  await expect(sourceLink).toHaveAttribute("rel", "noopener noreferrer");
  await expect(page.getByText("臺北市政府工務局")).toBeVisible();
  await expect(page.getByText(/發布機關僅供參考警示/)).toBeVisible();
});
