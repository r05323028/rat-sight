import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Dashboard } from "@/components/dashboard";
import type { CitizenReportCellProperties } from "@/lib/api";

const mockState = vi.hoisted(() => ({
  layerCatalogMode: "available" as "available" | "error" | "unknown",
  boundaryMode: "empty" as "empty" | "available" | "error",
  stormwaterMode: "available" as "available" | "empty" | "in_view" | "truncated" | "error",
  citizenMode: "available" as "available" | "empty" | "error" | "fixture",
  previewMode: "available" as
    | "available"
    | "osm_unavailable"
    | "ui_error"
    | "unknown_origin"
    | "cell_origin"
    | "version_conflict",
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
    origin_eligibility: {
      eligible: true,
      reason: "eligible_sighting_candidate",
      policy_version: "origin-report-category-v1",
      message: "鼠蹤通報可作為候選模擬起點；這是通報彙整，不是已驗證的動物位置。",
    } as const,
  },
  citizenFixtureCell: {
    cell_id: "g250m:1:2",
    month: "fixture-1",
    report_type: "sighting" as const,
    count: null,
    data_class: "SYNTHETIC_AGGREGATE_FIXTURE" as const,
    classification: "SIMULATED" as const,
    attribution: "SIMULATED local fixture; not citizen-report data.",
    origin_eligibility: {
      eligible: true,
      reason: "eligible_sighting_candidate",
      policy_version: "origin-report-category-v1",
      message: "本機合成測試格可作為模擬起點；不含任何公民通報。",
    } as const,
  },
  citizenBaitCell: {
    cell_id: "g250m:1:4",
    month: "2026-05",
    report_type: "bait_station" as const,
    count: 3,
    data_class: "CITIZEN_REPORT_AGGREGATE" as const,
    classification: "UNVERIFIED" as const,
    attribution: "公民通報資料來源：見鼠雷達 ratdar.taipei（公開通報匯出，未經平台授權）",
    origin_eligibility: {
      eligible: false,
      reason: "context_only_bait_station",
      policy_version: "origin-report-category-v1",
      message: "此類通報不直接代表鼠類出現位置，目前僅供資料參考，無法作為模擬起點。",
    } as const,
  },
  citizenBait: false,
  citizenResourceVersion: "2026-10-26T20:00:00Z",
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
    outputMode = "aggregate",
    activeStep,
    selectedTrajectoryId,
    onSelectTrajectory,
    playbackSpeed = 1,
    animationEnabled = true,
  }: {
    onSelectCitizenCell?: (properties: CitizenReportCellProperties) => void;
    outputMode?: "aggregate" | "trajectory";
    activeStep?: number | null;
    selectedTrajectoryId?: number | null;
    onSelectTrajectory?: (walkerId: number) => void;
    playbackSpeed?: number;
    animationEnabled?: boolean;
  }) => (
    <div role="region" aria-label="互動式 GIS 地圖">
      <div
        data-testid="map-playback-state"
        data-mode={outputMode}
        data-active-step={activeStep ?? ""}
        data-selected-trajectory={selectedTrajectoryId ?? ""}
        data-playback-speed={playbackSpeed}
        data-animation-enabled={animationEnabled}
      />
      {onSelectCitizenCell && (
        <>
          <button type="button" onClick={() => onSelectCitizenCell(mockState.citizenCell)}>
            Select citizen report cell
          </button>
          <button
            type="button"
            onClick={() =>
              onSelectCitizenCell({
                ...mockState.citizenCell,
                cell_id: "g250m:1:3",
              } as typeof mockState.citizenCell)
            }
          >
            Select another citizen report cell
          </button>
          <button type="button" onClick={() => onSelectCitizenCell(mockState.citizenFixtureCell)}>
            Select synthetic fixture cell
          </button>
          <button type="button" onClick={() => onSelectCitizenCell(mockState.citizenBaitCell)}>
            Select bait station cell
          </button>
        </>
      )}
      {outputMode === "trajectory" &&
        onSelectTrajectory &&
        [1, 2, 3].map((walkerId) => (
          <button key={walkerId} type="button" onClick={() => onSelectTrajectory(walkerId)}>
            Map walker {walkerId}
          </button>
        ))}
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
  mockState.citizenBait = false;
  mockState.citizenResourceVersion = "2026-10-26T20:00:00Z";
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
        if (mockState.citizenMode === "fixture") {
          return new Response(
            JSON.stringify({
              type: "FeatureCollection",
              data_state: "available",
              data_class: "SYNTHETIC_AGGREGATE_FIXTURE",
              classification: "SIMULATED",
              notice: "SIMULATED local fixture; not citizen-report data.",
              provenance: {
                schema_version: "1",
                source_kind: "synthetic_aggregate_fixture",
                dataset_id: "ratsight-smoke-browser",
                resource_version: "2026-10-27T00:00:00Z",
                content_sha256: "c".repeat(64),
                reference_source_id: "taipei-expanded-ratdar-20261027.osm",
                reference_source_sha256: "d".repeat(64),
                source_crs: "EPSG:4326",
                target_crs: "EPSG:4326",
                cell_size_meters: 250,
                test_scope: "isolated_disposable_postgis_smoke",
                synthetic: true,
                note: "Synthetic fixture only; not citizen-report data.",
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
                  properties: mockState.citizenFixtureCell,
                },
              ],
              feature_count: 1,
              bbox: [121.5, 25.0, 121.53, 25.02],
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
              resource_version: mockState.citizenResourceVersion,
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
                  origin_eligibility: mockState.citizenCell.origin_eligibility,
                },
              },
              ...(mockState.citizenBait
                ? [
                    {
                      type: "Feature",
                      geometry: {
                        type: "Polygon",
                        coordinates: [
                          [
                            [121.53, 25.0112],
                            [121.53, 25.0135],
                            [121.528, 25.0135],
                            [121.528, 25.0112],
                            [121.53, 25.0112],
                          ],
                        ],
                      },
                      properties: mockState.citizenBaitCell,
                    },
                  ]
                : []),
            ],
            feature_count: mockState.citizenBait ? 3 : 2,
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
        origin_source?: {
          dataset_id: string;
          resource_version: string;
          content_sha256: string;
        };
      };
      if (mockState.previewMode === "version_conflict") {
        return new Response(
          JSON.stringify({
            detail: {
              code: "ORIGIN_SOURCE_VERSION_CONFLICT",
              message: "The selected citizen-report dataset is no longer current.",
              action: "Refresh citizen reports and select an origin again.",
            },
          }),
          { status: 409, headers: { "Content-Type": "application/json" } },
        );
      }
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
            {
              walker_id: 3,
              classification: "SIMULATED",
              terminated_early: true,
              edges: [],
            },
          ],
          trajectory_count: 3,
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
    await screen.findByRole("region", { name: "模擬軌跡播放控制" });
    const card = screen.getByLabelText("公民通報彙整格詳細資料");
    const status = within(card).getByRole("status");
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
    await screen.findByRole("region", { name: "模擬軌跡播放控制" });
    expect(
      within(screen.getByLabelText("公民通報彙整格詳細資料")).getByRole("status"),
    ).toHaveTextContent("模擬路徑已顯示");

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

    const segmentButton = screen.getByRole("button", { name: "P-1（管段 S-1）" });
    expect(segmentButton).toHaveTextContent(/^P-1$/);
    expect(segmentButton).toHaveAccessibleName(/^P-1（管段 S-1）$/);
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

  it("labels isolated synthetic fixtures as SIMULATED without report counts", async () => {
    mockState.citizenMode = "fixture";
    renderDashboard();
    const panel = await screen.findByRole("region", { name: "本機合成測試格檢視" });
    expect(
      await within(panel).findByText("SIMULATED · 本機合成測試格（不含公民通報）"),
    ).toBeInTheDocument();
    expect(within(panel).getByText(/回傳 1 個 250 公尺 SIMULATED/)).toBeInTheDocument();
    expect(within(panel).queryByText(/筆已發布的通報計數/)).not.toBeInTheDocument();
    expect(within(panel).getByText("SIMULATED · 合成測試")).toBeInTheDocument();

    fireEvent.click(await screen.findByRole("button", { name: "Select synthetic fixture cell" }));
    const card = screen.getByLabelText("本機合成測試格詳細資料");
    expect(within(card).getByText("SIMULATED · 本機測試")).toBeInTheDocument();
    expect(within(card).queryByText("發布通報計數")).not.toBeInTheDocument();
    expect(within(card).getByText(/不含公民通報、通報計數或動物觀測/)).toBeInTheDocument();
    expect(screen.getByText(/SIMULATED 本機測試格（非公民通報）/)).toBeInTheDocument();

    fireEvent.click(within(card).getByRole("button", { name: "以此格網起點執行模擬" }));
    await screen.findByRole("region", { name: "模擬軌跡播放控制" });
    const previewCall = vi
      .mocked(fetch)
      .mock.calls.filter(([input]) => String(input).includes("/api/v1/simulations/preview"))
      .at(-1);
    expect(JSON.parse(String(previewCall?.[1]?.body))).toMatchObject({
      study_area: "taipei_osm_songshan",
      origin_cell_id: "g250m:1:2:fixture-1:sighting",
    });
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
    await screen.findByRole("region", { name: "模擬軌跡播放控制" });
    const status = within(screen.getByLabelText("公民通報彙整格詳細資料")).getByRole("status");
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

  it("clears the previous result when another published cell is focused", async () => {
    renderDashboard();
    await runSelectedCitizenCell();
    expect(await screen.findByRole("region", { name: "模擬軌跡播放控制" })).toHaveTextContent(
      "起點 g250m:1:2:2026-05:sighting",
    );

    fireEvent.click(screen.getByRole("button", { name: "Select another citizen report cell" }));

    const card = screen.getByLabelText("公民通報彙整格詳細資料");
    expect(within(card).getByText("g250m:1:3")).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "模擬軌跡播放控制" })).not.toBeInTheDocument();
    expect(within(card).queryByRole("status")).not.toBeInTheDocument();
    expect(screen.getByTestId("map-playback-state")).toHaveAttribute("data-mode", "aggregate");
  });

  it("plays individual trajectories and resets safely for each walker", async () => {
    renderDashboard();
    await runSelectedCitizenCell();
    const controls = await screen.findByRole("region", { name: "模擬軌跡播放控制" });
    fireEvent.click(within(controls).getByRole("button", { name: "個別路徑" }));
    expect(screen.getByTestId("map-playback-state")).toHaveAttribute("data-mode", "trajectory");

    const walker = within(controls).getByRole("combobox", { name: "選擇行走者" });
    fireEvent.change(walker, { target: { value: "1" } });
    expect(within(controls).getByText("步驟 0 / 1 · 非實際時間")).toBeInTheDocument();
    fireEvent.click(within(controls).getByRole("button", { name: "下一步" }));
    expect(within(controls).getByText("步驟 1 / 1 · 非實際時間")).toBeInTheDocument();
    expect(screen.getByTestId("map-playback-state")).toHaveAttribute("data-active-step", "1");
    fireEvent.click(within(controls).getByRole("button", { name: "上一步" }));
    expect(within(controls).getByText("步驟 0 / 1 · 非實際時間")).toBeInTheDocument();
    fireEvent.click(within(controls).getByRole("button", { name: "下一步" }));
    fireEvent.click(within(controls).getByRole("button", { name: "重設" }));
    expect(within(controls).getByText("步驟 0 / 1 · 非實際時間")).toBeInTheDocument();

    fireEvent.change(walker, { target: { value: "2" } });
    expect(within(controls).getByText("步驟 0 / 1 · 非實際時間")).toBeInTheDocument();
    fireEvent.click(within(controls).getByRole("button", { name: "播放" }));
    expect(within(controls).getByRole("button", { name: "暫停" })).toBeInTheDocument();
    fireEvent.click(within(controls).getByRole("button", { name: "暫停" }));
    expect(within(controls).getByText("步驟 0 / 1 · 非實際時間")).toBeInTheDocument();
    fireEvent.click(within(controls).getByRole("button", { name: "播放" }));
    await waitFor(() =>
      expect(within(controls).getByText("步驟 1 / 1 · 非實際時間")).toBeInTheDocument(),
    );
    expect(within(controls).getByRole("button", { name: "播放" })).toBeDisabled();

    fireEvent.change(walker, { target: { value: "3" } });
    expect(within(controls).getByText("此路徑沒有可播放的移動步驟。")).toBeInTheDocument();
    expect(within(controls).getByRole("button", { name: "下一步" })).toBeDisabled();
    fireEvent.click(within(controls).getByRole("button", { name: "彙整路線" }));
    expect(screen.getByTestId("map-playback-state")).toHaveAttribute("data-mode", "aggregate");
  });

  it("ignores a slower response after a newer origin run succeeds", async () => {
    const fetchMock = vi.mocked(fetch);
    const originalFetch = fetchMock.getMockImplementation();
    if (!originalFetch) throw new Error("Dashboard fetch fixture is not installed");
    const pending = new Map<string, () => Promise<void>>();
    fetchMock.mockImplementation(async (input, init) => {
      if (String(input).endsWith("/api/v1/simulations/preview")) {
        const body = JSON.parse(String(init?.body)) as { origin_cell_id: string };
        return await new Promise<Response>((resolve) => {
          pending.set(body.origin_cell_id, async () => {
            resolve(await originalFetch(input, init));
          });
        });
      }
      return originalFetch(input, init);
    });

    renderDashboard();
    const panel = screen.getByRole("region", { name: "公民通報彙整檢視" });
    expect(await within(panel).findByText(/回傳 2 個/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Select citizen report cell" }));
    fireEvent.click(screen.getByRole("button", { name: "以此格網起點執行模擬" }));
    const originA = "g250m:1:2:2026-05:sighting";
    await waitFor(() => expect(pending.has(originA)).toBe(true));

    fireEvent.click(screen.getByRole("button", { name: "Select another citizen report cell" }));
    fireEvent.click(screen.getByRole("button", { name: "以此格網起點執行模擬" }));
    const originB = "g250m:1:3:2026-05:sighting";
    await waitFor(() => expect(pending.has(originB)).toBe(true));
    await pending.get(originB)?.();
    const controls = await screen.findByRole("region", { name: "模擬軌跡播放控制" });
    expect(controls).toHaveTextContent(`起點 ${originB}`);

    await pending.get(originA)?.();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(controls).toHaveTextContent(`起點 ${originB}`);
    expect(controls).not.toHaveTextContent(`起點 ${originA}`);
  });

  it("binds the simulation request to the report snapshot that produced the selection", async () => {
    renderDashboard();
    await runSelectedCitizenCell();
    await screen.findByRole("region", { name: "模擬軌跡播放控制" });

    const previewCall = vi
      .mocked(fetch)
      .mock.calls.filter(([input]) => String(input).includes("/api/v1/simulations/preview"))
      .at(-1);
    expect(JSON.parse(String(previewCall?.[1]?.body))).toMatchObject({
      study_area: "taipei_osm_songshan",
      origin_cell_id: "g250m:1:2:2026-05:sighting",
      origin_source: {
        dataset_id: "ratdar-taipei-public-export",
        resource_version: "2026-10-26T20:00:00Z",
        content_sha256: "e".repeat(64),
      },
    });

    const card = screen.getByLabelText("公民通報彙整格詳細資料");
    expect(within(card).getByText("ratdar-taipei-public-export")).toBeInTheDocument();
    expect(within(card).getByText("2026-10-26T20:00:00Z")).toBeInTheDocument();
    expect(within(card).getByText("e".repeat(64))).toBeInTheDocument();
    expect(within(card).getByText("origin-report-category-v1")).toBeInTheDocument();
  });

  it("keeps context-only report categories inspectable but not runnable", async () => {
    mockState.citizenBait = true;
    renderDashboard();
    const panel = screen.getByRole("region", { name: "公民通報彙整檢視" });
    await within(panel).findByText(/回傳 3 個/);
    fireEvent.click(await screen.findByRole("button", { name: "Select bait station cell" }));

    const card = screen.getByLabelText("公民通報彙整格詳細資料");
    const note = within(card).getByRole("note");
    expect(note).toHaveTextContent("毒餌相關通報");
    expect(note).toHaveTextContent(
      /此類通報不直接代表鼠類出現位置，目前僅供資料參考，無法作為模擬起點。/,
    );
    const run = within(card).getByRole("button", { name: "此類通報無法作為模擬起點" });
    expect(run).toBeDisabled();
    fireEvent.click(run);
    expect(
      vi
        .mocked(fetch)
        .mock.calls.filter(([input]) => String(input).includes("/api/v1/simulations/preview")),
    ).toHaveLength(0);
    expect(screen.queryByRole("region", { name: "模擬軌跡播放控制" })).not.toBeInTheDocument();
  });

  it("invalidates the selection and result when the report snapshot changes", async () => {
    const { queryClient } = renderDashboard();
    await runSelectedCitizenCell();
    expect(await screen.findByRole("region", { name: "模擬軌跡播放控制" })).toBeInTheDocument();

    mockState.citizenResourceVersion = "2026-10-27T21:00:00Z";
    await queryClient.refetchQueries({ queryKey: ["citizen-report-aggregates"] });

    expect(
      await screen.findByText("公民通報資料已更新，請重新載入並選擇模擬起點。"),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("公民通報彙整格詳細資料")).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "模擬軌跡播放控制" })).not.toBeInTheDocument();
  });

  it("keeps the reviewed origin when a viewport refresh returns the same snapshot", async () => {
    const { queryClient } = renderDashboard();
    await runSelectedCitizenCell();
    await screen.findByRole("region", { name: "模擬軌跡播放控制" });

    await queryClient.refetchQueries({ queryKey: ["citizen-report-aggregates"] });

    expect(screen.getByLabelText("公民通報彙整格詳細資料")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "模擬軌跡播放控制" })).toBeInTheDocument();
    expect(screen.queryByText(/公民通報資料已更新/)).not.toBeInTheDocument();
  });

  it("reports a source-version conflict instead of reusing a stale result", async () => {
    renderDashboard();
    await runSelectedCitizenCell();
    await screen.findByRole("region", { name: "模擬軌跡播放控制" });

    mockState.previewMode = "version_conflict";
    fireEvent.click(screen.getByRole("button", { name: "以此格網起點執行模擬" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("公民通報資料已更新，請重新載入並選擇模擬起點。");
    expect(alert).not.toHaveTextContent("ORIGIN_SOURCE_VERSION_CONFLICT");
    expect(screen.queryByRole("region", { name: "模擬軌跡播放控制" })).not.toBeInTheDocument();
  });

  it("does not show an in-flight result whose report snapshot was superseded", async () => {
    const fetchMock = vi.mocked(fetch);
    const originalFetch = fetchMock.getMockImplementation();
    if (!originalFetch) throw new Error("Dashboard fetch fixture is not installed");
    const pending = new Map<string, () => Promise<void>>();
    fetchMock.mockImplementation(async (input, init) => {
      if (String(input).endsWith("/api/v1/simulations/preview")) {
        const body = JSON.parse(String(init?.body)) as { origin_cell_id: string };
        return await new Promise<Response>((resolve) => {
          pending.set(body.origin_cell_id, async () => {
            resolve(await originalFetch(input, init));
          });
        });
      }
      return originalFetch(input, init);
    });

    const { queryClient } = renderDashboard();
    const panel = screen.getByRole("region", { name: "公民通報彙整檢視" });
    await within(panel).findByText(/回傳 2 個/);
    fireEvent.click(await screen.findByRole("button", { name: "Select citizen report cell" }));
    fireEvent.click(screen.getByRole("button", { name: "以此格網起點執行模擬" }));
    const origin = "g250m:1:2:2026-05:sighting";
    await waitFor(() => expect(pending.has(origin)).toBe(true));

    mockState.citizenResourceVersion = "2026-10-27T21:00:00Z";
    await queryClient.refetchQueries({ queryKey: ["citizen-report-aggregates"] });
    await screen.findByText(/公民通報資料已更新/);

    await pending.get(origin)?.();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(screen.queryByRole("region", { name: "模擬軌跡播放控制" })).not.toBeInTheDocument();
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

  it("keeps selected-cell details in the control rail instead of over the map", async () => {
    renderDashboard();
    fireEvent.click(await screen.findByRole("button", { name: "Select citizen report cell" }));

    const rail = screen.getByRole("complementary", { name: "分析控制項" });
    const card = await within(rail).findByRole("region", { name: "公民通報彙整格詳細資料" });
    const map = screen.getByRole("region", { name: "互動式 GIS 地圖" });
    // The inspector must never be mounted inside the map region again.
    expect(
      within(map).queryByRole("region", { name: "公民通報彙整格詳細資料" }),
    ).not.toBeInTheDocument();
    expect(within(card).getByRole("button", { name: "以此格網起點執行模擬" })).toBeEnabled();

    fireEvent.click(within(card).getByRole("button", { name: "關閉公民通報彙整格詳細資料" }));
    await waitFor(() =>
      expect(
        screen.queryByRole("region", { name: "公民通報彙整格詳細資料" }),
      ).not.toBeInTheDocument(),
    );
  });

  it("lets context-only reports be inspected but never simulated", async () => {
    mockState.citizenBait = true;
    renderDashboard();
    fireEvent.click(await screen.findByRole("button", { name: "Select bait station cell" }));

    const card = await screen.findByRole("region", { name: "公民通報彙整格詳細資料" });
    expect(within(card).getAllByText("毒餌相關通報").length).toBeGreaterThan(0);
    expect(
      within(card).getByText(/此類通報不直接代表鼠類出現位置，目前僅供資料參考/),
    ).toBeInTheDocument();
    expect(within(card).getByRole("button", { name: "此類通報無法作為模擬起點" })).toBeDisabled();
    expect(
      vi.mocked(fetch).mock.calls.some(([input]) => String(input).includes("/simulations/preview")),
    ).toBe(false);
  });

  it("applies playback speed and the animation toggle to the map", async () => {
    renderDashboard();
    await runSelectedCitizenCell();
    const playback = await screen.findByRole("region", { name: "模擬軌跡播放控制" });
    const speed = within(playback).getByRole("combobox", { name: "播放速度" });
    expect(speed).toHaveValue("1");
    expect(within(playback).getByText("模擬播放速度，非實際鼠類移動速度")).toBeInTheDocument();

    const toggle = within(playback).getByRole("checkbox", { name: "動畫效果" });
    expect(toggle).toBeChecked();
    fireEvent.change(speed, { target: { value: "2" } });
    fireEvent.click(toggle);

    const state = screen.getByTestId("map-playback-state");
    expect(state).toHaveAttribute("data-playback-speed", "2");
    expect(state).toHaveAttribute("data-animation-enabled", "false");
  });

  it("starts with animation disabled when reduced motion is requested", async () => {
    const original = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: true,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    })) as unknown as typeof window.matchMedia;
    try {
      renderDashboard();
      await runSelectedCitizenCell();
      expect(await screen.findByRole("checkbox", { name: "動畫效果" })).not.toBeChecked();
      expect(screen.getByTestId("map-playback-state")).toHaveAttribute(
        "data-animation-enabled",
        "false",
      );
    } finally {
      window.matchMedia = original;
    }
  });
});
