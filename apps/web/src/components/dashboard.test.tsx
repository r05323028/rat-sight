import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Dashboard } from "@/components/dashboard";

const mockState = vi.hoisted(() => ({
  layerCatalogMode: "available" as "available" | "error" | "unknown",
  boundaryMode: "empty" as "empty" | "available" | "error",
  stormwaterMode: "available" as "available" | "empty" | "in_view" | "truncated" | "error",
  rodentMode: "available" as "available" | "empty" | "in_filters" | "truncated" | "error" | "many",
  previewMode: "available" as "available" | "osm_unavailable" | "ui_error" | "unknown_origin",
  district: {
    district_id: "63000010",
    district_name: "松山區",
    data_class: "ADMINISTRATIVE_REFERENCE",
    classification: "UNVERIFIED",
    provenance_schema_version: "1",
    dataset_id: "121199",
    resource_version: "20220915",
    archive_sha256: "a".repeat(64),
  },
  stormwaterFeature: {
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
  rodentFeature: {
    report_id: "report-1",
    source: "synthetic_fixture",
    report_type: "sighting_report",
    reported_at: "2026-10-01T00:00:00Z",
    location_precision: "synthetic_point",
    review_status: "unreviewed",
    municipal_status: "not_assessed",
    action_status: "none_reported",
    data_class: "RODENT_REPORT",
    classification: "SIMULATED",
    provenance_schema_version: "1",
    dataset_id: "00000000-0000-4000-8000-000000000002",
    resource_version: "2026-10-17T00:00:00Z",
    content_sha256: "c".repeat(64),
  },
}));

vi.mock("@/components/map-view", () => ({
  MapView: ({ rodentReports }: { rodentReports?: unknown }) => (
    <div
      role="region"
      aria-label="互動式 GIS 地圖"
      data-has-rodent-reports={rodentReports ? "yes" : "no"}
    />
  ),
}));

function renderDashboard() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>,
  );
}

const PROVENANCE = {
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
};

const STORMWATER_PROVENANCE = {
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
  uncertainty: { currentness: "Publisher reference-only; currentness UNVERIFIED", note: "fixture" },
};

const RODENT_PROVENANCE = {
  schema_version: "1",
  source_kind: "synthetic_fixture",
  dataset_id: "00000000-0000-4000-8000-000000000002",
  resource_version: "2026-10-17T00:00:00Z",
  retrieved_at: "2026-10-17T00:00:00Z",
  content_sha256: "c".repeat(64),
  license: "僅為合成測試資料；不含真實回報資料。",
  attribution: "RatSight synthetic report fixture",
  source_crs: "EPSG:4326",
  target_crs: "EPSG:4326",
  processing: { tool: "test", tool_version: "0", steps: ["fixture"] },
  synthetic: true,
  uncertainty: { currentness: "Synthetic fixture; not a real reporting system.", note: "fixture" },
};

beforeEach(() => {
  mockState.layerCatalogMode = "available";
  mockState.boundaryMode = "empty";
  mockState.stormwaterMode = "available";
  mockState.rodentMode = "available";
  mockState.previewMode = "available";
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/v1/layers")) {
        if (mockState.layerCatalogMode === "error") {
          return new Response("catalog unavailable", { status: 503 });
        }
        if (mockState.layerCatalogMode === "unknown") {
          return new Response(
            JSON.stringify([
              {
                id: "unmapped_layer",
                label: "Mystery dataset",
                available: true,
                classification: "OBSERVED",
                message: null,
              },
            ]),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response(
          JSON.stringify([
            {
              id: "rodent_observations",
              label: "鼠類觀測",
              available: false,
              classification: null,
              message: "尚未載入觀測資料集。",
            },
            {
              id: "sewer_networks",
              label: "污水下水道",
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
              label: "地表移動廊道",
              available: false,
              classification: null,
              message: "No corridor dataset loaded.",
            },
            {
              id: "human_activity",
              label: "人類活動",
              available: false,
              classification: null,
              message: "No human-activity dataset loaded.",
            },
            {
              id: "environmental_conditions",
              label: "環境條件",
              available: false,
              classification: null,
              message: "No environmental dataset loaded.",
            },
            {
              id: "simulated_paths",
              label: "模擬移動路徑",
              available: false,
              classification: "SIMULATED",
              message: "Available after a synthetic preview.",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.endsWith("/api/v1/administrative-districts")) {
        if (mockState.boundaryMode === "error") {
          return new Response("storage unavailable", { status: 503 });
        }
        const features =
          mockState.boundaryMode === "available"
            ? [
                {
                  type: "Feature",
                  id: mockState.district.district_id,
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
                  properties: mockState.district,
                },
              ]
            : [];
        return new Response(
          JSON.stringify({
            type: "FeatureCollection",
            data_state: features.length > 0 ? "available" : "empty",
            data_class: "ADMINISTRATIVE_REFERENCE",
            provenance: features.length > 0 ? PROVENANCE : null,
            features,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/api/v1/stormwater-pipelines")) {
        if (mockState.stormwaterMode === "error") {
          return new Response("storage unavailable", { status: 503 });
        }
        const features =
          mockState.stormwaterMode === "empty" || mockState.stormwaterMode === "in_view"
            ? []
            : [
                {
                  type: "Feature",
                  id: mockState.stormwaterFeature.segment_id,
                  geometry: {
                    type: "LineString",
                    coordinates: [
                      [121.55, 25.02],
                      [121.58, 25.06],
                    ],
                  },
                  properties: mockState.stormwaterFeature,
                },
              ];
        return new Response(
          JSON.stringify({
            type: "FeatureCollection",
            data_state: mockState.stormwaterMode === "empty" ? "empty" : "available",
            data_class: "INFRASTRUCTURE_REFERENCE",
            provenance: mockState.stormwaterMode === "empty" ? null : STORMWATER_PROVENANCE,
            feature_count: features.length,
            bbox: [121.5, 24.98, 121.63, 25.09],
            truncated: mockState.stormwaterMode === "truncated",
            features,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/api/v1/rodent-reports")) {
        if (mockState.rodentMode === "error") {
          return new Response("storage unavailable", { status: 503 });
        }
        const many = mockState.rodentMode === "many";
        const features =
          mockState.rodentMode === "empty" || mockState.rodentMode === "in_filters"
            ? []
            : many
              ? Array.from({ length: 150 }, (_, index) => {
                  const reportId = `RR-${String(index).padStart(4, "0")}`;
                  return {
                    type: "Feature",
                    id: reportId,
                    geometry: { type: "Point", coordinates: [121.55, 25.02] },
                    properties: { ...mockState.rodentFeature, report_id: reportId },
                  };
                })
              : [
                  {
                    type: "Feature",
                    id: mockState.rodentFeature.report_id,
                    geometry: { type: "Point", coordinates: [121.55, 25.02] },
                    properties: mockState.rodentFeature,
                  },
                ];
        return new Response(
          JSON.stringify({
            type: "FeatureCollection",
            data_state: mockState.rodentMode === "empty" ? "empty" : "available",
            data_class: "RODENT_REPORT",
            classification: "SIMULATED",
            provenance: mockState.rodentMode === "empty" ? null : RODENT_PROVENANCE,
            feature_count: features.length,
            bbox: [121.5, 24.98, 121.63, 25.09],
            reported_from: null,
            reported_to: null,
            truncated: mockState.rodentMode === "truncated",
            features,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      const requestBody = JSON.parse(String(init?.body ?? "{}")) as {
        study_area?: string;
        origin_node_id?: string;
      };
      if (mockState.previewMode === "ui_error") {
        return new Response("preview exploded", { status: 500 });
      }
      if (
        mockState.previewMode === "osm_unavailable" &&
        requestBody.study_area === "taipei_osm_songshan"
      ) {
        return new Response(
          JSON.stringify({
            detail: {
              code: "SOURCE_NETWORK_UNAVAILABLE",
              message: "extract missing",
              provisioning: "see docs",
            },
          }),
          { status: 503, headers: { "Content-Type": "application/json" } },
        );
      }
      if (mockState.previewMode === "unknown_origin") {
        return new Response(
          JSON.stringify({
            detail: {
              code: "ORIGIN_NODE_NOT_IN_GRAPH",
              message: `origin_node_id '${requestBody.origin_node_id ?? "n1"}' is not a node in study area '${requestBody.study_area}'`,
              study_area: requestBody.study_area,
            },
          }),
          { status: 422, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(
        JSON.stringify({
          simulation_status: "completed",
          classification: "SIMULATED",
          model_id: "synthetic_weighted_random_walk",
          model_version: "0.1.0",
          parameters: {
            study_area: requestBody.study_area ?? "taipei_osm_songshan",
            duration_steps: 12,
            walkers: 24,
            random_seed: 42,
            movement_model: "weighted_random_walk",
            intervention_scenario: "baseline",
            origin_node_id: requestBody.origin_node_id ?? "n1",
          },
          provenance:
            requestBody.study_area === "taipei_synthetic_demo"
              ? {
                  classification: "SIMULATED",
                  source_type: "synthetic_fixture",
                  source_id: "ratsight-synthetic-graph-v1",
                  source_crs: "EPSG:4326",
                  note: "synthetic only",
                }
              : {
                  classification: "SIMULATED",
                  source_type: "osm_surface_network",
                  source_id: "taipei-songshan-20261023.osm",
                  source_crs: "EPSG:4326",
                  note: "bounded OSM surface extract",
                },
          assumptions: ["synthetic fixture"],
          origin: {
            node_id: requestBody.origin_node_id ?? "n1",
            coordinates: requestBody.origin_node_id === "n2" ? [121.52, 25.02] : [121.5, 25],
            classification: "SIMULATED",
            selection: requestBody.origin_node_id ? "user" : "default",
            note: "Synthetic model input; not an observed or reported animal origin.",
          },
          nodes: [
            {
              id: "n1",
              coordinates: [121.5, 25],
              visits: 3,
              probability: 0.6,
              classification: "SIMULATED",
            },
            {
              id: "n2",
              coordinates: [121.52, 25.02],
              visits: 2,
              probability: 0.4,
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
                    [121.5, 25],
                    [121.51, 25.01],
                  ],
                  classification: "SIMULATED",
                },
              ],
            },
            {
              walker_id: 2,
              classification: "SIMULATED",
              terminated_early: true,
              edges: [
                {
                  source: "b",
                  target: "c",
                  edge_id: "e2",
                  step_index: 0,
                  geometry: [
                    [121.51, 25.01],
                    [121.52, 25.02],
                  ],
                  classification: "SIMULATED",
                },
              ],
            },
          ],
          trajectory_count: 2,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }),
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("RatSight dashboard", () => {
  it("renders map, layer controls, and simulation controls", async () => {
    renderDashboard();
    expect(screen.getByRole("heading", { name: "見光鼠" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "互動式 GIS 地圖" })).toBeInTheDocument();
    // Planned catalog entries carry status text, never a dead control.
    expect(screen.queryByLabelText("鼠類觀測")).not.toBeInTheDocument();
    expect(await screen.findByText("尚未載入觀測資料集。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "開始模擬" })).toBeInTheDocument();
    expect(screen.getByText("尚未載入真實觀測資料")).toBeInTheDocument();
    expect(screen.getByText(/目前尚未載入已查證的鼠類觀測資料/)).toBeInTheDocument();
    expect(screen.getByText(/模擬結果不代表真實移動、風險或熱區/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "合成模擬示範" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "工作區狀態" })).toBeInTheDocument();
  });

  it("reports workspace readouts and the bounded viewport without inventing counts", async () => {
    mockState.boundaryMode = "available";
    renderDashboard();

    const hud = await screen.findByRole("region", { name: "目前狀態讀數" });
    expect(await within(hud).findByText("2 / 2")).toBeInTheDocument();
    expect(within(hud).getByText("未產生")).toBeInTheDocument();
    expect(within(hud).getByText("目錄未載入")).toBeInTheDocument();
    expect(within(hud).getByText("版本化 API")).toBeInTheDocument();

    expect(screen.getByText("0.130°")).toBeInTheDocument();
    expect(screen.getByText("上限 0.30°")).toBeInTheDocument();
  });

  it("keeps a catalog failure out of the readout instead of showing zero", async () => {
    mockState.layerCatalogMode = "error";
    renderDashboard();

    const hud = await screen.findByRole("region", { name: "目前狀態讀數" });
    expect(await within(hud).findByText("無法判定")).toBeInTheDocument();
    expect(within(hud).queryByText("0")).not.toBeInTheDocument();
  });

  it("indexes every rail chapter and draws layer marks instead of text glyphs", async () => {
    renderDashboard();

    const index = screen.getByRole("navigation", { name: "章節索引" });
    const links = within(index).getAllByRole("link");
    expect(links).toHaveLength(6);
    expect(within(index).getByRole("link", { name: "02 圖層" })).toHaveAttribute(
      "href",
      "#panel-layers",
    );
    expect(document.getElementById("panel-layers")).not.toBeNull();
    expect(document.getElementById("panel-rodent")).not.toBeNull();

    const glyphs = document.querySelectorAll(".layer-glyph");
    expect(glyphs.length).toBeGreaterThan(0);
    glyphs.forEach((glyph) => expect(glyph.textContent).toBe(""));
  });

  it("reports a catalog failure without calling the fallback catalog empty", async () => {
    mockState.layerCatalogMode = "error";
    renderDashboard();
    expect(await screen.findByText("圖層目錄無法使用")).toBeInTheDocument();
    expect(screen.queryByLabelText("鼠類觀測")).not.toBeInTheDocument();
    expect(screen.getByText(/不得推論任何圖層可用性/)).toBeInTheDocument();
    expect(screen.queryByText(/顯示空的圖層目錄/)).not.toBeInTheDocument();
  });

  it("never leaks an unknown API label and glosses classifications", async () => {
    mockState.layerCatalogMode = "unknown";
    renderDashboard();
    expect(await screen.findByText("未命名資料圖層")).toBeInTheDocument();
    expect(screen.getByText("OBSERVED · 已觀測")).toBeInTheDocument();
    expect(screen.queryByText("Mystery dataset")).not.toBeInTheDocument();
  });

  it("groups planned layers with honest source-readiness guidance", async () => {
    renderDashboard();
    expect(await screen.findByText("此版本尚未載入")).toBeInTheDocument();
    expect(screen.getByText("尚未載入觀測資料集。")).toBeInTheDocument();
    expect(screen.getByText(/尚未記錄核准的資料來源或匯入程式/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "資料來源整備指南" })).toHaveAttribute(
      "href",
      "https://github.com/r05323028/rat-sight/blob/main/docs/infrastructure/data-sources.md",
    );
    expect(screen.getByText("SIMULATED · 合成測試資料；請執行預覽以產生")).toBeInTheDocument();
    const unavailableGroup = screen.getByText("此版本尚未載入").parentElement;
    if (!unavailableGroup) throw new Error("Unavailable layer group was not rendered");
    expect(within(unavailableGroup).queryByLabelText("模擬移動路徑")).not.toBeInTheDocument();
  });

  it("keeps simulated paths separate and labeled as a fixture before and after preview", async () => {
    renderDashboard();
    expect(screen.getByText("合成模擬")).toBeInTheDocument();
    expect(screen.queryByLabelText("模擬移動路徑")).not.toBeInTheDocument();
    expect(screen.getByText("SIMULATED · 合成測試資料；請執行預覽以產生")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    await screen.findByRole("status");
    await waitFor(() => expect(screen.getByLabelText("模擬移動路徑")).toBeEnabled());
    expect(screen.getByText("SIMULATED · 合成測試資料")).toBeInTheDocument();
    expect(screen.getByText("此版本尚未載入")).toBeInTheDocument();
  });

  it("links to operator-only import guides for supported layers", async () => {
    mockState.stormwaterMode = "empty";
    mockState.rodentMode = "empty";
    renderDashboard();
    expect(await screen.findByRole("link", { name: "行政區邊界匯入指南" })).toHaveAttribute(
      "href",
      "https://github.com/r05323028/rat-sight/blob/main/docs/infrastructure/administrative-boundaries-import.md",
    );
    expect(await screen.findByRole("link", { name: "雨水下水道匯入指南" })).toHaveAttribute(
      "href",
      "https://github.com/r05323028/rat-sight/blob/main/docs/infrastructure/stormwater-pipelines-import.md",
    );
    expect(await screen.findByRole("link", { name: "合成回報測試資料匯入指南" })).toHaveAttribute(
      "href",
      "https://github.com/r05323028/rat-sight/blob/main/docs/infrastructure/rodent-reports-import.md",
    );
  });

  it("defaults to the pinned OSM study area", () => {
    renderDashboard();
    expect(screen.getByLabelText("研究範圍")).toHaveValue("taipei_osm_songshan");
  });

  it("explains the schematic network as straight-line topology, not road geometry", async () => {
    renderDashboard();
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    await screen.findByRole("status");
    // The OSM default follows surveyed edge geometry, so no schematic caveat is shown.
    expect(screen.queryByText(/示意拓撲：/)).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("研究範圍"), {
      target: { value: "taipei_synthetic_demo" },
    });
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    expect(await screen.findByText(/示意拓撲：.*直線（虛線）連接/)).toBeInTheDocument();
  });

  it("states synthetic preview limitations beside the analysis metrics", async () => {
    renderDashboard();
    expect(screen.getByText(/合成預覽 — 僅為模擬測試資料；不含真實觀測/)).toBeInTheDocument();
    expect(screen.getByText(/請勿推論盛行率、移動、風險/)).toBeInTheDocument();
    expect(screen.getByText("模型網路邊")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    await screen.findByRole("status");
    expect(screen.getByText(/次無單位、假設性的節點造訪/)).toBeInTheDocument();
  });

  it("labels the reported-date filter as Asia/Taipei and counts returned reports", async () => {
    mockState.rodentMode = "available";
    renderDashboard();
    expect(screen.getByLabelText("回報起時間（Asia/Taipei，含端點）")).toBeInTheDocument();
    expect(screen.getByLabelText("回報迄時間（Asia/Taipei，含端點）")).toBeInTheDocument();
    expect(screen.getByText(/Asia\/Taipei（UTC\+8，無日光節約時間）/)).toBeInTheDocument();
    expect(await screen.findByText(/內回傳 1 筆 SIMULATED\s+合成報告形資料/)).toBeInTheDocument();
  });

  it("counts visible layer rows once and offers no dead layer checkboxes", async () => {
    renderDashboard();
    await screen.findByText("尚未載入觀測資料集。");
    for (const label of ["鼠類觀測", "污水下水道", "地表移動廊道", "人類活動", "環境條件"]) {
      expect(screen.getAllByText(label)).toHaveLength(1);
      expect(screen.queryByLabelText(label)).not.toBeInTheDocument();
    }
    // Four built-in map rows plus five catalog entries plus synthetic paths.
    const badge = screen.getByLabelText(/個圖層列/);
    expect(badge).toHaveTextContent("10");
    // The displayed count must equal the rows actually rendered, not a stale total.
    expect(document.querySelectorAll(".layer-row")).toHaveLength(Number(badge.textContent));
    expect(screen.getAllByRole("checkbox")).toHaveLength(4);
  });

  it("qualifies a truncated response without claiming a total", async () => {
    mockState.rodentMode = "truncated";
    renderDashboard();
    const panel = screen.getByRole("region", { name: "鼠類回報檢視" });
    expect(await within(panel).findByText("回傳資料已截斷")).toBeInTheDocument();
    expect(within(panel).getByText(/內回傳 1 筆 SIMULATED\s+合成報告形資料/)).toBeInTheDocument();
    expect(within(panel).getByText(/已達回傳上限/)).toBeInTheDocument();
  });

  it("requests and labels synthetic preview output", async () => {
    mockState.previewMode = "osm_unavailable";
    renderDashboard();
    // The schematic graph is now an explicit choice, so select it rather than relying on the default.
    fireEvent.change(screen.getByLabelText("研究範圍"), {
      target: { value: "taipei_synthetic_demo" },
    });
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    expect(await screen.findByRole("status")).toHaveTextContent("可重現執行完成 · 種子 42");
    expect(screen.getByText("ratsight-synthetic-graph-v1")).toBeInTheDocument();
  });

  it("shows only the simulation provenance the API returns and marks the rest unavailable", async () => {
    renderDashboard();
    fireEvent.change(screen.getByLabelText("研究範圍"), {
      target: { value: "taipei_synthetic_demo" },
    });
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    await screen.findByRole("status");
    const panel = screen.getByRole("region", { name: "合成模擬示範" });
    fireEvent.click(within(panel).getByText("模擬來源與版本"));
    expect(within(panel).getByText("來源類型")).toBeInTheDocument();
    expect(within(panel).getByText("synthetic_fixture")).toBeInTheDocument();
    expect(within(panel).getByText("來源 ID")).toBeInTheDocument();
    expect(within(panel).getByText("內容 SHA-256")).toBeInTheDocument();
    // Fields the fixture omits are stated as absent, never guessed.
    expect(within(panel).getAllByText("未提供").length).toBeGreaterThan(0);
  });

  it("states that an unavailable OSM network is not replaced by the schematic network", async () => {
    mockState.previewMode = "osm_unavailable";
    renderDashboard();
    fireEvent.change(screen.getByLabelText("研究範圍"), {
      target: { value: "taipei_osm_songshan" },
    });
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/來源網路無法使用：extract missing/);
    expect(alert).toHaveTextContent(/系統未以示意網路替代 OSM 結果/);
  });

  it("keeps the failure generic when the OSM source itself is not the reported cause", async () => {
    mockState.previewMode = "ui_error";
    renderDashboard();
    fireEvent.change(screen.getByLabelText("研究範圍"), {
      target: { value: "taipei_osm_songshan" },
    });
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Simulation preview failed (500)");
    expect(alert).not.toHaveTextContent(/來源網路無法使用/);
    expect(alert).not.toHaveTextContent(/未以示意網路替代/);
  });

  it("reports synthetic trajectories instead of aggregate visits in trajectory mode", async () => {
    renderDashboard();
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    await screen.findByRole("status");
    fireEvent.change(screen.getByLabelText("輸出模式"), { target: { value: "trajectory" } });
    const summary = screen.getByLabelText("模擬摘要");
    expect(within(summary).getByText("2 條合成軌跡（SIMULATED）")).toBeInTheDocument();
    expect(within(summary).queryByText(/節點造訪/)).not.toBeInTheDocument();
    expect(screen.getByLabelText("合成軌跡")).toHaveValue("1");
    expect(screen.getByText("步驟 0 / 1")).toBeInTheDocument();
    expect(screen.getByText(/只顯示已回傳的合成邊幾何累積到第 0 步/)).toBeInTheDocument();
    // Selecting trajectories turns the paths layer on, otherwise the map shows nothing.
    expect(screen.getByLabelText("模擬移動路徑")).toBeChecked();
  });

  it("advances playback through returned steps without implying elapsed time", async () => {
    renderDashboard();
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    await screen.findByRole("status");
    fireEvent.change(screen.getByLabelText("輸出模式"), { target: { value: "trajectory" } });
    expect(screen.getByRole("button", { name: "上一步" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "下一步" }));
    expect(screen.getByText("步驟 1 / 1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "下一步" })).toBeDisabled();
    expect(screen.getByRole("button", { name: /步驟 1（step_index 0）/ })).toHaveAttribute(
      "aria-current",
      "step",
    );
    fireEvent.click(screen.getByRole("button", { name: "重設" }));
    expect(screen.getByText("步驟 0 / 1")).toBeInTheDocument();
    // Playback switches trajectory without re-running the model.
    fireEvent.change(screen.getByLabelText("合成軌跡"), { target: { value: "2" } });
    expect(screen.getByText(/此合成代理在模型網路死路終止/)).toBeInTheDocument();
  });

  it("discloses the default origin chosen by the API", async () => {
    renderDashboard();
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    await screen.findByRole("status");
    expect(
      screen.getByText(/^n1 · 25\.00000, 121\.50000 · 預設固定起點 · SIMULATED$/),
    ).toBeInTheDocument();
  });

  it("sends a chosen origin and discloses it as a user selection", async () => {
    renderDashboard();
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    await screen.findByRole("status");
    fireEvent.change(screen.getByLabelText("合成起點節點"), { target: { value: "n2" } });
    expect(screen.getByText(/已選擇，尚未以此外起點執行/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    await waitFor(() =>
      expect(
        screen.getByText(/^n2 · 25\.02000, 121\.52000 · 使用者選擇 · SIMULATED$/),
      ).toBeInTheDocument(),
    );
    const previewCall = vi
      .mocked(fetch)
      .mock.calls.filter(([input]) => String(input).includes("/api/v1/simulations/preview"))
      .at(-1);
    expect(JSON.parse(String(previewCall?.[1]?.body))).toMatchObject({ origin_node_id: "n2" });
  });

  it("surfaces a rejected origin instead of silently snapping to a node", async () => {
    mockState.previewMode = "unknown_origin";
    renderDashboard();
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("合成起點不在模型網路內：origin_node_id 'n1' is not a node");
    expect(alert).not.toHaveTextContent(/來源網路無法使用/);
  });

  it("clears an earlier trajectory when a later origin run fails", async () => {
    renderDashboard();
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    await screen.findByRole("status");
    fireEvent.change(screen.getByLabelText("輸出模式"), { target: { value: "trajectory" } });
    expect(screen.getByText("步驟 0 / 1")).toBeInTheDocument();
    mockState.previewMode = "unknown_origin";
    fireEvent.change(screen.getByLabelText("合成起點節點"), { target: { value: "n2" } });
    fireEvent.click(screen.getByRole("button", { name: "開始模擬" }));
    await screen.findByRole("alert");
    expect(screen.queryByText("步驟 0 / 1")).not.toBeInTheDocument();
  });

  it("summarizes evidence state and prohibited conclusions before any action", async () => {
    renderDashboard();
    const orientation = screen.getByRole("region", { name: "工作區狀態" });
    expect(within(orientation).getByText(/行政區邊界 · UNVERIFIED（未驗證）/)).toBeInTheDocument();
    expect(
      within(orientation).getByText("鼠類回報格式測試資料 · RODENT_REPORT · SIMULATED"),
    ).toBeInTheDocument();
    expect(
      await within(orientation).findByText(
        "尚未載入：鼠類觀測、污水下水道、地表移動廊道、人類活動、環境條件。",
      ),
    ).toBeInTheDocument();
    expect(within(orientation).getByText("目前可回答")).toBeInTheDocument();
    expect(within(orientation).getByText("目前無法回答")).toBeInTheDocument();
    expect(within(orientation).getByText("真實移動路徑、熱區或介入效果")).toBeInTheDocument();
    expect(within(orientation).getByText(/未載入也不代表數量為零/)).toBeInTheDocument();
  });

  it("keeps advanced simulation settings collapsed behind stated defaults", () => {
    renderDashboard();
    const summary = screen.getByText(/進階設定 · 松山 OSM 來源網路 · 12 步 · 種子 42 · 24 個合成代理/);
    expect(summary.closest("details")).not.toHaveAttribute("open");
    expect(screen.getByText(/預設示範參數：松山 OSM 來源網路 · 12 步 · 種子 42/)).toBeInTheDocument();
    expect(screen.getByText(/合成預覽 — 僅為模擬測試資料/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "開始模擬" })).toBeEnabled();
  });

  it("applies Asia/Taipei date presets and reports the active filter", () => {
    mockState.rodentMode = "available";
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-26T02:10:00Z"));
    try {
      renderDashboard();
      const panel = screen.getByRole("region", { name: "鼠類回報檢視" });
      fireEvent.click(within(panel).getByRole("button", { name: "近 7 天" }));
      expect(screen.getByLabelText("回報起時間（Asia/Taipei，含端點）")).toHaveValue(
        "2026-10-20T00:00",
      );
      expect(screen.getByLabelText("回報迄時間（Asia/Taipei，含端點）")).toHaveValue(
        "2026-10-26T10:10",
      );
      expect(
        within(panel).getByText(
          /目前篩選：近 7 天（2026-10-20T00:00 ～ 2026-10-26T10:10 · Asia\/Taipei，起迄皆含）/,
        ),
      ).toBeInTheDocument();
      fireEvent.click(within(panel).getByRole("button", { name: "全部" }));
      expect(screen.getByLabelText("回報起時間（Asia/Taipei，含端點）")).toHaveValue("");
      expect(within(panel).getByText(/目前篩選：自訂或未設定/)).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("keeps provenance details collapsed until opened", async () => {
    mockState.boundaryMode = "available";
    renderDashboard();
    const summary = await screen.findByText("行政區來源、授權與現勢性");
    expect(summary.closest("details")).not.toHaveAttribute("open");
    expect(summary.closest("details")).toHaveTextContent("臺北市政府民政局");
  });

  it("shows the selected feature summary next to the map", async () => {
    mockState.boundaryMode = "available";
    renderDashboard();
    expect(screen.getByText(/尚未選取圖徵/)).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "松山區" }));
    expect(document.querySelector(".map-selection")).toHaveTextContent(
      "松山區 · UNVERIFIED（未驗證）",
    );
  });

  it("shows the empty administrative boundary state without fabricating geometry", async () => {
    renderDashboard();
    const reference = screen.getByRole("region", {
      name: "行政區參考檢視",
    });
    expect(await within(reference).findByText("尚未匯入邊界")).toBeInTheDocument();
    expect(screen.getByLabelText("行政區")).toBeDisabled();
  });

  it("selects a district through the keyboard-accessible list and shows provenance", async () => {
    mockState.boundaryMode = "available";
    renderDashboard();
    const toggle = await screen.findByLabelText("行政區");
    await waitFor(() => expect(toggle).toBeEnabled());
    expect(toggle).not.toBeChecked();
    fireEvent.click(toggle);
    expect(toggle).toBeChecked();

    const districtButton = screen.getByRole("button", { name: "松山區" });
    districtButton.focus();
    expect(districtButton).toHaveFocus();
    fireEvent.click(districtButton);
    expect(districtButton).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("63000010")).toBeInTheDocument();
    expect(screen.getByText("121199")).toBeInTheDocument();

    const sourceLink = screen.getByRole("link", { name: "https://data.taipei/example" });
    expect(sourceLink).toHaveAttribute("href", "https://data.taipei/example");
    expect(sourceLink).toHaveAttribute("target", "_blank");
    expect(sourceLink).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.getByText("臺北市政府民政局")).toBeInTheDocument();
    expect(screen.getByText("UNVERIFIED after 2022-09-15")).toBeInTheDocument();
  });

  it("communicates an unavailable boundary service", async () => {
    mockState.boundaryMode = "error";
    renderDashboard();
    const reference = screen.getByRole("region", {
      name: "行政區參考檢視",
    });
    expect(await within(reference).findByText("邊界服務無法使用")).toBeInTheDocument();
    expect(screen.getByLabelText("行政區")).toBeDisabled();
  });

  it("reports the storage-empty stormwater state", async () => {
    mockState.stormwaterMode = "empty";
    renderDashboard();
    expect(await screen.findByText("尚未匯入管線")).toBeInTheDocument();
    expect(await screen.findByText("尚未匯入雨水下水道管線。")).toBeInTheDocument();
    expect(screen.getByLabelText("雨水下水道管線")).toBeDisabled();
  });

  it("distinguishes an in-view miss from an empty store", async () => {
    mockState.stormwaterMode = "in_view";
    renderDashboard();
    const panel = screen.getByRole("region", { name: "雨水下水道管線檢視" });
    expect(await within(panel).findByText("目前視圖範圍內無管線")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("雨水下水道管線")).toBeEnabled());
  });

  it("shows the capped partial-data state", async () => {
    mockState.stormwaterMode = "truncated";
    renderDashboard();
    const panel = screen.getByRole("region", { name: "雨水下水道管線檢視" });
    expect(await within(panel).findByText("僅顯示部分資料 · 請放大")).toBeInTheDocument();
    expect(await within(panel).findByText(/目前視窗範圍內回傳 1 條管線。/)).toBeInTheDocument();
    expect(
      within(panel).getByText(
        /已達回傳上限：除這些回傳圖徵外仍有符合條件的管線，且不宣稱精確總數。/,
      ),
    ).toBeInTheDocument();
  });

  it("communicates an unavailable stormwater service", async () => {
    mockState.stormwaterMode = "error";
    renderDashboard();
    const panel = screen.getByRole("region", { name: "雨水下水道管線檢視" });
    expect(await within(panel).findByText("雨水下水道服務無法使用")).toBeInTheDocument();
    expect(screen.getByLabelText("雨水下水道管線")).toBeDisabled();
  });

  it("inspects a selected stormwater pipeline with reference-only provenance", async () => {
    mockState.stormwaterMode = "available";
    renderDashboard();
    const toggle = await screen.findByLabelText("雨水下水道管線");
    await waitFor(() => expect(toggle).toBeEnabled());
    fireEvent.click(toggle);
    expect(toggle).toBeChecked();

    const segmentButton = screen.getByRole("button", { name: "S-1" });
    segmentButton.focus();
    expect(segmentButton).toHaveFocus();
    fireEvent.click(segmentButton);
    expect(segmentButton).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("RCP")).toBeInTheDocument();
    expect(screen.getByText("來源 Z 已捨棄 — 無文件化的垂直坐標參考系統")).toBeInTheDocument();
    expect(screen.getByText(/未驗證實際連通性/)).toBeInTheDocument();
    expect(screen.getByText(/發布機關僅供參考警示/)).toBeInTheDocument();
    const sourceLink = screen.getByRole("link", { name: "https://data.taipei/stormwater" });
    expect(sourceLink).toHaveAttribute("target", "_blank");
    expect(sourceLink).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("reports the storage-empty rodent report state", async () => {
    mockState.rodentMode = "empty";
    renderDashboard();
    expect(await screen.findByText("尚未匯入回報")).toBeInTheDocument();
    expect(await screen.findByText("尚未匯入合成鼠類回報。")).toBeInTheDocument();
    expect(screen.getByLabelText("鼠類回報")).toBeDisabled();
  });

  it("distinguishes an in-filter rodent report miss from storage-empty", async () => {
    mockState.rodentMode = "in_filters";
    renderDashboard();
    const panel = screen.getByRole("region", { name: "鼠類回報檢視" });
    expect(
      await within(panel).findByText(/沒有回傳的 SIMULATED\s+合成報告形資料/),
    ).toBeInTheDocument();
    expect(within(panel).getByText(/這不是事件計數/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("鼠類回報")).toBeEnabled());
  });

  it("shows the capped rodent report state", async () => {
    mockState.rodentMode = "truncated";
    renderDashboard();
    const panel = screen.getByRole("region", { name: "鼠類回報檢視" });
    expect(await within(panel).findByText("回傳資料已截斷")).toBeInTheDocument();
  });

  it("communicates an unavailable rodent report service", async () => {
    mockState.rodentMode = "error";
    renderDashboard();
    const panel = screen.getByRole("region", { name: "鼠類回報檢視" });
    expect(await within(panel).findByText("鼠類回報服務無法使用")).toBeInTheDocument();
    expect(screen.getByLabelText("鼠類回報")).toBeDisabled();
  });

  it("inspects a selected synthetic report with provenance and disclaimer", async () => {
    mockState.rodentMode = "available";
    renderDashboard();
    const toggle = await screen.findByLabelText("鼠類回報");
    await waitFor(() => expect(toggle).toBeEnabled());
    fireEvent.click(toggle);
    expect(toggle).toBeChecked();

    const reportButton = screen.getByRole("button", { name: "report-1" });
    reportButton.focus();
    expect(reportButton).toHaveFocus();
    fireEvent.click(reportButton);
    expect(reportButton).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("unreviewed")).toBeInTheDocument();
    expect(screen.getByText("not_assessed")).toBeInTheDocument();
    expect(screen.getByText("none_reported")).toBeInTheDocument();
    expect(screen.getByText("synthetic_point")).toBeInTheDocument();
    expect(screen.getByText("00000000-0000-4000-8000-000000000002")).toBeInTheDocument();
    expect(screen.getByText("僅為合成測試資料；不含真實回報資料。")).toBeInTheDocument();
    expect(
      screen.getByText("合成回報格式的測試資料。非經查證的觀測、盛行率、族群、移動或風險證據。"),
    ).toBeInTheDocument();
  });

  it("converts a Taipei-local filter to an RFC3339 Z query value", async () => {
    mockState.rodentMode = "available";
    renderDashboard();
    fireEvent.change(screen.getByLabelText("回報起時間（Asia/Taipei，含端點）"), {
      target: { value: "2026-10-01T08:30" },
    });
    await waitFor(() => {
      const urls = vi.mocked(fetch).mock.calls.map((call) => String(call[0]));
      expect(urls.some((url) => url.includes("reported_from=2026-10-01T00%3A30%3A00Z"))).toBe(true);
    });
  });

  it("caps the auxiliary report list at 100 with a clear notice", async () => {
    mockState.rodentMode = "many";
    renderDashboard();
    const toggle = await screen.findByLabelText("鼠類回報");
    await waitFor(() => expect(toggle).toBeEnabled());
    const panel = screen.getByRole("region", { name: "鼠類回報檢視" });
    const reportList = within(panel).getByRole("list", { name: "回報 · 選取以檢視" });
    await waitFor(() => expect(within(reportList).getAllByRole("button")).toHaveLength(100));
    expect(within(panel).getByText(/僅顯示前 100 筆，共回傳/)).toBeInTheDocument();
  });

  it("rejects a reversed Taipei-local range locally without an API request", async () => {
    mockState.rodentMode = "available";
    renderDashboard();
    await waitFor(() => expect(screen.getByLabelText("鼠類回報")).toBeEnabled());
    fireEvent.change(screen.getByLabelText("回報起時間（Asia/Taipei，含端點）"), {
      target: { value: "2026-10-10T00:00" },
    });
    fireEvent.change(screen.getByLabelText("回報迄時間（Asia/Taipei，含端點）"), {
      target: { value: "2026-10-01T00:00" },
    });
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "回報起時間必須早於或等於回報迄時間。",
    );
    await waitFor(() => expect(screen.getByLabelText("鼠類回報")).toBeDisabled());
    // No stale points reach the map while the range is invalid.
    expect(screen.getByRole("region", { name: "互動式 GIS 地圖" })).toHaveAttribute(
      "data-has-rodent-reports",
      "no",
    );
    const urls = vi.mocked(fetch).mock.calls.map((call) => String(call[0]));
    expect(
      urls.some(
        (url) => url.includes("reported_from=2026-10-09") && url.includes("reported_to=2026-09-30"),
      ),
    ).toBe(false);
  });
});
