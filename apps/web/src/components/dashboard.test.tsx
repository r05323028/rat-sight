import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Dashboard } from "@/components/dashboard";

const mockState = vi.hoisted(() => ({
  layerCatalogMode: "available" as "available" | "error" | "unknown",
  boundaryMode: "empty" as "empty" | "available" | "error",
  stormwaterMode: "available" as "available" | "empty" | "in_view" | "truncated" | "error",
  citizenMode: "available" as "available" | "empty" | "error",
  previewMode: "available" as
    "available" | "osm_unavailable" | "ui_error" | "unknown_origin" | "cell_origin",
  // Absent by default: the API does not ship termination_reason yet.
  previewTerminationReason: undefined as "dead_end" | "no_eligible_transition" | undefined,
  previewReachability: true,
  previewVisualization: false,
  citizenCell: {
    cell_id: "g250m:1:2",
    month: "2026-05",
    report_type: "sighting" as const,
    count: 4,
    data_class: "CITIZEN_REPORT_AGGREGATE" as const,
    classification: "UNVERIFIED" as const,
    attribution: "公民通報資料來源：見鼠雷達 ratdar.taipei（公開通報匯出，未經平台授權）",
  },
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
}));

vi.mock("@/components/map-view", () => ({
  MapView: ({
    onSelectCitizenCell,
    citizenCellCard,
  }: {
    onSelectCitizenCell?: (properties: typeof mockState.citizenCell) => void;
    citizenCellCard?: ReactNode;
  }) => (
    <div role="region" aria-label="互動式 GIS 地圖">
      {onSelectCitizenCell && (
        <button type="button" onClick={() => onSelectCitizenCell(mockState.citizenCell)}>
          Select citizen report cell
        </button>
      )}
      {citizenCellCard}
    </div>
  ),
}));

async function runSelectedCitizenCell() {
  const panel = screen.getByRole("region", { name: "公民通報彙整檢視" });
  await within(panel).findByText(/回傳 2 個/);
  fireEvent.click(await screen.findByRole("button", { name: "Select citizen report cell" }));
  fireEvent.click(screen.getByRole("button", { name: "以此格網起點執行模擬" }));
}

function renderDashboard() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const rendered = render(
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>,
  );
  return { ...rendered, queryClient };
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

beforeEach(() => {
  mockState.layerCatalogMode = "available";
  mockState.boundaryMode = "empty";
  mockState.stormwaterMode = "available";
  mockState.citizenMode = "available";
  mockState.previewMode = "available";
  mockState.previewTerminationReason = undefined;
  mockState.previewReachability = true;
  mockState.previewVisualization = false;
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
      if (url.includes("/api/v1/citizen-report-aggregates")) {
        if (mockState.citizenMode === "error") {
          return new Response("aggregate storage unavailable", { status: 503 });
        }
        if (mockState.citizenMode === "empty") {
          return new Response(
            JSON.stringify({
              type: "FeatureCollection",
              data_state: "empty",
              data_class: "CITIZEN_REPORT_AGGREGATE",
              classification: "UNVERIFIED",
              notice: "公民通報彙整只提供 250 公尺網格計數。",
              provenance: null,
              features: [],
              feature_count: 0,
              bbox: null,
              truncated: false,
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          );
        }
        return new Response(
          JSON.stringify({
            type: "FeatureCollection",
            data_state: "available",
            data_class: "CITIZEN_REPORT_AGGREGATE",
            classification: "UNVERIFIED",
            notice: "公民通報彙整只提供 250 公尺網格計數。",
            provenance: {
              schema_version: "1",
              source_kind: "public_citizen_report_export",
              dataset_id: "ratdar-taipei-public-export",
              resource_version: "2026-10-26T20:00:00Z",
              retrieved_at: "2026-10-26T20:00:00Z",
              content_sha256: "e".repeat(64),
              source_url: "https://ratdar.taipei/",
              license: "公開匯出，未取得再利用授權；僅發布彙整計數。",
              attribution: "公民通報資料來源：見鼠雷達 ratdar.taipei（公開通報匯出，未經平台授權）",
              source_crs: "EPSG:4326",
              target_crs: "EPSG:4326",
              processing: { tool: "test", tool_version: "0", steps: ["aggregate"] },
              aggregation: {
                cell_size_meters: 250,
                month_timezone_assumption: "Asia/Taipei wall clock",
                suppression_minimum: 3,
                dropped_fields: ["地點", "說明", "照片網址"],
              },
              counts: {
                parsed: 1435,
                used: 319,
                invalid_coordinates: 0,
                suppressed_records: 1116,
                suppressed_cells: 946,
              },
              synthetic: false,
              uncertainty: { currentness: "2026-05 only", note: "citizen reports" },
            },
            features: [
              {
                type: "Feature",
                geometry: {
                  type: "Polygon",
                  coordinates: [
                    [
                      [121.51, 25.0112],
                      [121.51, 25.0135],
                      [121.508, 25.0135],
                      [121.508, 25.0112],
                      [121.51, 25.0112],
                    ],
                  ],
                },
                properties: mockState.citizenCell,
              },
              {
                type: "Feature",
                geometry: {
                  type: "Polygon",
                  coordinates: [
                    [
                      [121.52, 25.0112],
                      [121.52, 25.0135],
                      [121.518, 25.0135],
                      [121.518, 25.0112],
                      [121.52, 25.0112],
                    ],
                  ],
                },
                properties: {
                  cell_id: "g250m:1:3",
                  month: "2026-05",
                  report_type: "sighting",
                  count: 3,
                  data_class: "CITIZEN_REPORT_AGGREGATE",
                  classification: "UNVERIFIED",
                  attribution:
                    "公民通報資料來源：見鼠雷達 ratdar.taipei（公開通報匯出，未經平台授權）",
                },
              },
            ],
            feature_count: 2,
            bbox: [121.5, 25.0, 121.53, 25.02],
            truncated: false,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      const requestBody = JSON.parse(String(init?.body ?? "{}")) as {
        study_area?: string;
        origin_node_id?: string;
        origin_cell_id?: string;
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
                  source_id: "taipei-expanded-ratdar-20261027.osm",
                  source_crs: "EPSG:4326",
                  note: "bounded OSM surface extract",
                },
          assumptions: ["synthetic fixture"],
          origin: {
            node_id: requestBody.origin_cell_id ? "n0" : (requestBody.origin_node_id ?? "n1"),
            coordinates: requestBody.origin_cell_id
              ? [121.53, 25.04]
              : requestBody.origin_node_id === "n2"
                ? [121.52, 25.02]
                : [121.5, 25],
            classification: "SIMULATED",
            selection:
              requestBody.origin_cell_id || mockState.previewMode === "cell_origin"
                ? "cell"
                : requestBody.origin_node_id
                  ? "user"
                  : "default",
            ...(requestBody.origin_cell_id
              ? { cell_id: requestBody.origin_cell_id }
              : mockState.previewMode === "cell_origin"
                ? { cell_id: "synthetic-cell-n0" }
                : {}),
            ...(requestBody.origin_cell_id && requestBody.study_area === "taipei_osm_songshan"
              ? {
                  node_ids: Array.from({ length: 83 }, (_, index) => `n${index}`),
                  cell_candidate_count: 83,
                  cell_resolver_version: "uniform-in-cell-v1",
                }
              : {}),
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
              visits: 0,
              probability: 0,
              classification: "SIMULATED",
            },
            {
              id: "n3",
              coordinates: [121.53, 25.03],
              visits: 0,
              probability: 0,
              classification: "SIMULATED",
            },
          ],
          reachability: mockState.previewReachability
            ? {
                origin_node_id: requestBody.origin_node_id ?? "n1",
                reachable_nodes: 2,
                total_nodes: 3,
                reachable_edges: 3,
                total_edges: 4,
                sampled_nodes: 1,
                component_count: 2,
                classification: "SIMULATED",
                note: "Graph reachability from the resolved origin; synthetic model input.",
              }
            : undefined,
          visualization: mockState.previewVisualization
            ? {
                mode: "local_reference",
                radius_meters: 750,
                returned_nodes: 3,
                returned_edges: 1,
                total_nodes: 3,
                total_edges: 4,
                note: "Map geometry is a local reference subset.",
              }
            : undefined,
          // n1 -> n3 only: n2 is disconnected and n3 is reachable but unsampled.
          edges: [
            {
              source: "n1",
              target: "n3",
              edge_id: "e3",
              movement_weight: 1,
              visits: 0,
              probability: 0,
              classification: "SIMULATED",
            },
          ],
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
              ...(mockState.previewTerminationReason
                ? { termination_reason: mockState.previewTerminationReason }
                : {}),
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
  it("renders the map, layers, and report-driven simulation controls", async () => {
    renderDashboard();
    expect(screen.getByRole("heading", { name: "見光鼠" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "互動式 GIS 地圖" })).toBeInTheDocument();
    // Simulation is only reachable from a selected citizen-report cell.
    expect(screen.queryByRole("button", { name: "開始模擬" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "合成模擬示範" })).not.toBeInTheDocument();
    expect(screen.getByText("尚未載入真實觀測資料")).toBeInTheDocument();
    expect(screen.getByText(/目前尚未載入已查證的鼠類觀測資料/)).toBeInTheDocument();
    expect(screen.getByText(/模擬結果不代表真實移動、風險或熱區/)).toBeInTheDocument();
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
    expect(links).toHaveLength(5);
    expect(within(index).getByRole("link", { name: "02 圖層" })).toHaveAttribute(
      "href",
      "#panel-layers",
    );
    expect(within(index).getByRole("link", { name: "03 行政區" })).toHaveAttribute(
      "href",
      "#panel-reference",
    );
    expect(within(index).getByRole("link", { name: "04 下水道" })).toHaveAttribute(
      "href",
      "#panel-stormwater",
    );
    expect(within(index).getByRole("link", { name: "05 公民通報" })).toHaveAttribute(
      "href",
      "#panel-citizen-aggregates",
    );
    expect(document.getElementById("panel-simulation")).toBeNull();
    expect(document.getElementById("panel-layers")).not.toBeNull();

    const glyphs = document.querySelectorAll(".layer-glyph");
    expect(glyphs.length).toBeGreaterThan(0);
    glyphs.forEach((glyph) => expect(glyph.textContent).toBe(""));
  });

  it("reports a catalog failure without calling the fallback catalog empty", async () => {
    mockState.layerCatalogMode = "error";
    renderDashboard();
    expect(await screen.findByText("圖層目錄無法使用")).toBeInTheDocument();
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
    expect(screen.getByText(/尚未記錄核准的資料來源或匯入程式/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "資料來源整備指南" })).toHaveAttribute(
      "href",
      "https://github.com/r05323028/rat-sight/blob/main/docs/infrastructure/data-sources.md",
    );
    expect(
      screen.getByText("公民通報彙整與模擬移動路徑會在資料載入或預覽完成後自動顯示。"),
    ).toBeInTheDocument();
    const unavailableGroup = screen.getByText("此版本尚未載入").parentElement;
    if (!unavailableGroup) throw new Error("Unavailable layer group was not rendered");
    expect(within(unavailableGroup).queryByLabelText("模擬移動路徑")).not.toBeInTheDocument();
  });

  it("shows simulated paths automatically after a report-cell run without a layer switch", async () => {
    renderDashboard();
    expect(screen.queryByLabelText("模擬移動路徑")).not.toBeInTheDocument();
    await runSelectedCitizenCell();
    const status = await screen.findByRole("status");
    expect(status).toHaveTextContent("可重現執行完成");
    expect(status).toHaveTextContent("模擬路徑已顯示");
    expect(screen.queryByLabelText("模擬移動路徑")).not.toBeInTheDocument();
  });

  it("links to operator-only import guides for supported layers", async () => {
    mockState.stormwaterMode = "empty";
    renderDashboard();
    expect(await screen.findByRole("link", { name: "行政區邊界匯入指南" })).toHaveAttribute(
      "href",
      "https://github.com/r05323028/rat-sight/blob/main/docs/infrastructure/administrative-boundaries-import.md",
    );
    expect(await screen.findByRole("link", { name: "雨水下水道匯入指南" })).toHaveAttribute(
      "href",
      "https://github.com/r05323028/rat-sight/blob/main/docs/infrastructure/stormwater-pipelines-import.md",
    );
  });

  it("counts visible layer rows once and offers no dead layer checkboxes", async () => {
    renderDashboard();
    for (const label of ["污水下水道", "地表移動廊道", "人類活動", "環境條件"]) {
      expect(screen.getAllByText(label)).toHaveLength(1);
      expect(screen.queryByLabelText(label)).not.toBeInTheDocument();
    }
    // Three switchable built-in rows plus four catalog entries.
    const badge = screen.getByLabelText(/個圖層列/);
    expect(badge).toHaveTextContent("7");
    // The displayed count must equal the rows actually rendered, not a stale total.
    expect(document.querySelectorAll(".layer-row")).toHaveLength(Number(badge.textContent));
    expect(screen.getAllByRole("checkbox")).toHaveLength(3);
    expect(screen.queryByLabelText("公民通報彙整")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("模擬移動路徑")).not.toBeInTheDocument();
  });

  it("surfaces an unavailable OSM network on the report-cell card", async () => {
    mockState.previewMode = "osm_unavailable";
    renderDashboard();
    await runSelectedCitizenCell();
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/來源網路無法使用：extract missing/);
    expect(alert).toHaveTextContent(/系統未以示意網路替代 OSM 結果/);
  });

  it("keeps the failure generic when the OSM source itself is not the reported cause", async () => {
    mockState.previewMode = "ui_error";
    renderDashboard();
    await runSelectedCitizenCell();
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Simulation preview failed (500)");
    expect(alert).not.toHaveTextContent(/來源網路無法使用/);
    expect(alert).not.toHaveTextContent(/未以示意網路替代/);
  });

  it("clears an earlier successful preview when a later report-cell run fails", async () => {
    renderDashboard();
    await runSelectedCitizenCell();
    expect(await screen.findByRole("status")).toHaveTextContent("模擬路徑已顯示");

    mockState.previewMode = "unknown_origin";
    fireEvent.click(screen.getByRole("button", { name: "以此格網起點執行模擬" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("合成起點不在模型網路內");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("summarizes evidence state and prohibited conclusions before any action", async () => {
    renderDashboard();
    const orientation = screen.getByRole("region", { name: "工作區狀態" });
    expect(within(orientation).getByText(/行政區邊界 · UNVERIFIED（未驗證）/)).toBeInTheDocument();
    expect(
      await within(orientation).findByText(
        "尚未載入：污水下水道、地表移動廊道、人類活動、環境條件。",
      ),
    ).toBeInTheDocument();
    expect(within(orientation).getByText("目前可回答")).toBeInTheDocument();
    expect(within(orientation).getByText("目前無法回答")).toBeInTheDocument();
    expect(within(orientation).getByText("真實移動路徑、熱區或介入效果")).toBeInTheDocument();
    expect(within(orientation).getByText(/未載入也不代表數量為零/)).toBeInTheDocument();
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

  it("shows suppressed citizen-report cell counts without presenting reports", async () => {
    renderDashboard();
    const panel = screen.getByRole("region", { name: "公民通報彙整檢視" });
    expect(
      await within(panel).findByText("CITIZEN_REPORT_AGGREGATE · UNVERIFIED（未驗證）"),
    ).toBeInTheDocument();
    expect(
      within(panel).getByText(/回傳 2 個\s*250 公尺網格、7 筆已發布的通報計數/),
    ).toBeInTheDocument();
    expect(within(panel).getByText(/每格每月每類型至少\s*3\s*筆才發布/)).toBeInTheDocument();
    expect(
      within(panel).getByText(/不是鼠類觀測、盛行率、族群、移動或風險估計/),
    ).toBeInTheDocument();
    fireEvent.click(within(panel).getByText("來源、授權、精度與抑制"));
    expect(within(panel).getByText("地點、說明、照片網址")).toBeInTheDocument();
    expect(within(panel).getByText(/解析 1435 筆 · 採用\s*319 筆 · 抑制/)).toBeInTheDocument();
    expect(screen.queryByLabelText("公民通報彙整")).not.toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: "Select citizen report cell" }),
    ).toBeInTheDocument();
  });

  it("opens aggregate details on marker focus without running a simulation", async () => {
    renderDashboard();
    const panel = screen.getByRole("region", { name: "公民通報彙整檢視" });
    expect(await within(panel).findByText(/回傳 2 個/)).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "Select citizen report cell" }));

    const card = screen.getByLabelText("公民通報彙整格詳細資料");
    expect(within(card).getByText("g250m:1:2")).toBeInTheDocument();
    expect(within(card).getByText("鼠蹤通報")).toBeInTheDocument();
    expect(within(card).getByText("4 筆")).toBeInTheDocument();
    expect(within(card).getByText(/250 公尺格網 · 標記在格網中心/)).toBeInTheDocument();
    expect(within(card).getByText(/不是個別通報點位/)).toBeInTheDocument();
    expect(within(card).getByText(mockState.citizenCell.attribution)).toBeInTheDocument();
    expect(screen.getByText(/公民通報彙整格焦點 · UNVERIFIED/)).toBeInTheDocument();
    expect(
      vi
        .mocked(fetch)
        .mock.calls.filter(([input]) => String(input).includes("/api/v1/simulations/preview")),
    ).toHaveLength(0);

    fireEvent.click(within(card).getByRole("button", { name: "關閉公民通報彙整格詳細資料" }));
    expect(screen.queryByLabelText("公民通報彙整格詳細資料")).not.toBeInTheDocument();
    expect(screen.getByText(/尚未選取圖徵/)).toBeInTheDocument();
  });

  it("runs the simulation from the focused aggregate cell", async () => {
    renderDashboard();
    const panel = screen.getByRole("region", { name: "公民通報彙整檢視" });
    expect(await within(panel).findByText(/回傳 2 個/)).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "Select citizen report cell" }));
    fireEvent.click(screen.getByRole("button", { name: "以此格網起點執行模擬" }));
    const status = await screen.findByRole("status");
    expect(status).toHaveTextContent("可重現執行完成 · 種子 42 · 模擬路徑已顯示");

    const previewCall = vi
      .mocked(fetch)
      .mock.calls.filter(([input]) => String(input).includes("/api/v1/simulations/preview"))
      .at(-1);
    const body = JSON.parse(String(previewCall?.[1]?.body));
    expect(body).toMatchObject({
      study_area: "taipei_osm_songshan",
      origin_cell_id: "g250m:1:2:2026-05:sighting",
    });
    expect(body).not.toHaveProperty("origin_node_id");
  });

  it("clears a selected aggregate cell when refreshed viewport data drops it", async () => {
    const { queryClient } = renderDashboard();
    const panel = screen.getByRole("region", { name: "公民通報彙整檢視" });
    expect(await within(panel).findByText(/回傳 2 個/)).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "Select citizen report cell" }));
    expect(
      screen.getByText(/g250m:1:2 · 2026-05 · 鼠蹤通報 · 公民通報彙整格焦點/),
    ).toBeInTheDocument();

    mockState.citizenMode = "empty";
    await queryClient.refetchQueries({ queryKey: ["citizen-report-aggregates"] });
    await waitFor(() => expect(screen.queryByText(/g250m:1:2/)).not.toBeInTheDocument());
    expect(screen.getByText(/尚未選取圖徵/)).toBeInTheDocument();
  });

  it("states that no aggregate is imported instead of substituting another layer", async () => {
    mockState.citizenMode = "empty";
    renderDashboard();
    const panel = screen.getByRole("region", { name: "公民通報彙整檢視" });
    expect(
      await within(panel).findByText(/尚未匯入公民通報彙整：資料庫尚未匯入/),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("公民通報彙整")).not.toBeInTheDocument();
  });
});
