import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  AdministrativeDistricts,
  CitizenReportAggregates,
  SimulationPreview,
  StormwaterNetwork,
} from "@/lib/api";

const h = vi.hoisted(() => ({
  mapConstructor: vi.fn(),
  latest: { current: null as unknown },
}));

type HandlerEntry = { layerId?: string; handler: (...args: unknown[]) => void };

vi.mock("gsap", () => ({
  default: {
    to: vi.fn(() => ({ kill: vi.fn(), pause: vi.fn(), resume: vi.fn() })),
  },
}));

vi.mock("maplibre-gl", () => ({
  setWorkerUrl: vi.fn(),
  Map: class {
    handlers: Record<string, HandlerEntry[]> = {};
    sources = new Map<string, { id: string; setData: ReturnType<typeof vi.fn> }>();
    layers = new Set<string>();
    addControl = vi.fn();
    once = vi.fn();
    on = vi.fn(
      (type: string, layerOrHandler: unknown, maybeHandler?: (...args: unknown[]) => void) => {
        const entry: HandlerEntry =
          typeof layerOrHandler === "function"
            ? { handler: layerOrHandler as (...args: unknown[]) => void }
            : { layerId: layerOrHandler as string, handler: maybeHandler! };
        (this.handlers[type] ??= []).push(entry);
        return this;
      },
    );
    off = vi.fn();
    isStyleLoaded = () => true;
    addSource = vi.fn((id: string) => {
      this.sources.set(id, { id, setData: vi.fn() });
      return this;
    });
    getSource = vi.fn((id: string) => this.sources.get(id));
    removeSource = vi.fn((id: string) => {
      this.sources.delete(id);
      return this;
    });
    setLayoutProperty = vi.fn();
    setPaintProperty = vi.fn();
    addLayer = vi.fn((layer: { id: string }) => {
      this.layers.add(layer.id);
      return this;
    });
    getLayer = vi.fn((id: string) => (this.layers.has(id) ? { id } : undefined));
    removeLayer = vi.fn((id: string) => {
      this.layers.delete(id);
      return this;
    });
    setFilter = vi.fn();
    fitBounds = vi.fn();
    getBounds = () => ({
      getWest: () => 121.5,
      getSouth: () => 24.98,
      getEast: () => 121.63,
      getNorth: () => 25.09,
    });
    getCenter = () => ({ lng: 121.565, lat: 25.035 });
    getZoom = () => 13.5;
    getCanvas = () => ({ style: { cursor: "" } });
    remove = vi.fn();
    constructor(options: unknown) {
      h.mapConstructor(options);
      h.latest.current = this;
    }
  },
  NavigationControl: class {},
}));

import { MapView } from "@/components/map-view";

// Static layers are created once and receive data through setData; tests read
// the most recent payload rather than the initial empty source creation.
function latestSourceData(sourceId: string): {
  features: { properties: Record<string, unknown>; geometry: unknown }[];
} {
  const map = h.latest.current as {
    getSource: (id: string) => { setData: ReturnType<typeof vi.fn> } | undefined;
  };
  const source = map.getSource(sourceId);
  if (!source) throw new Error("source was not created: " + sourceId);
  const calls = source.setData.mock.calls;
  if (calls.length === 0) throw new Error("source received no data: " + sourceId);
  return calls.at(-1)![0] as {
    features: { properties: Record<string, unknown>; geometry: unknown }[];
  };
}

const boundaries: AdministrativeDistricts = {
  type: "FeatureCollection",
  data_state: "available",
  data_class: "ADMINISTRATIVE_REFERENCE",
  provenance: null,
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

const preview: SimulationPreview = {
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
      coordinates: [121.58, 25.06],
      visits: 1,
      probability: 0.5,
      classification: "SIMULATED",
    },
  ],
  edges: [
    {
      source: "a",
      target: "b",
      edge_id: "a-b",
      movement_weight: 1,
      visits: 1,
      probability: 1,
      classification: "SIMULATED",
    },
  ],
};

const stormwater: StormwaterNetwork = {
  type: "FeatureCollection",
  data_state: "available",
  data_class: "INFRASTRUCTURE_REFERENCE",
  feature_count: 1,
  bbox: [121.5, 24.98, 121.63, 25.09],
  truncated: false,
  provenance: null,
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
      },
    },
  ],
};

const citizenAggregates: CitizenReportAggregates = {
  type: "FeatureCollection",
  data_state: "available",
  data_class: "CITIZEN_REPORT_AGGREGATE",
  classification: "UNVERIFIED",
  notice: "公民通報彙整只提供 250 公尺網格計數。",
  feature_count: 1,
  bbox: [121.5, 25.0, 121.53, 25.02],
  truncated: false,
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
      properties: {
        cell_id: "g250m:1:2",
        month: "2026-05",
        report_type: "sighting",
        count: 4,
        data_class: "CITIZEN_REPORT_AGGREGATE",
        classification: "UNVERIFIED",
        attribution: "公民通報資料來源：見鼠雷達 ratdar.taipei（公開通報匯出，未經平台授權）",
        origin_eligibility: {
          eligible: true,
          reason: "eligible_sighting_candidate",
          policy_version: "origin-report-category-v1",
          message: "鼠蹤通報可作為候選模擬起點；這是通報彙整，不是已驗證的動物位置。",
        },
      },
    },
  ],
};

type MapViewProps = {
  preview?: SimulationPreview | null;
  showSimulatedPaths?: boolean;
  boundaries?: AdministrativeDistricts | null;
  showBoundaries?: boolean;
  selectedDistrictId?: string | null;
  onSelectDistrict?: (properties: unknown) => void;
  stormwater?: StormwaterNetwork | null;
  showStormwater?: boolean;
  selectedSegmentId?: string | null;
  onSelectSegment?: (properties: unknown) => void;
  citizenAggregates?: CitizenReportAggregates | null;
  showCitizenAggregates?: boolean;
  selectedCitizenCellKey?: string | null;
  onSelectCitizenCell?: (properties: unknown) => void;
  onSelectTrajectory?: (trajectoryId: number) => void;
  outputMode?: "aggregate" | "trajectory";
  activeStep?: number | null;
  selectedTrajectoryId?: number | null;
  onBoundsChange?: (bbox: [number, number, number, number]) => void;
};

function mapElement({
  preview: previewValue = null,
  showSimulatedPaths,
  boundaries: boundariesValue = null,
  showBoundaries = false,
  selectedDistrictId = null,
  onSelectDistrict = vi.fn(),
  stormwater: stormwaterValue = null,
  showStormwater = false,
  selectedSegmentId = null,
  onSelectSegment = vi.fn(),
  citizenAggregates: citizenAggregatesValue = null,
  showCitizenAggregates,
  selectedCitizenCellKey = null,
  onSelectCitizenCell = vi.fn(),
  onSelectTrajectory = vi.fn(),
  outputMode = "aggregate",
  activeStep = null,
  selectedTrajectoryId = null,
  onBoundsChange = vi.fn(),
}: MapViewProps = {}) {
  return (
    <MapView
      preview={previewValue}
      showSimulatedPaths={showSimulatedPaths}
      boundaries={boundariesValue}
      showBoundaries={showBoundaries}
      selectedDistrictId={selectedDistrictId}
      onSelectDistrict={onSelectDistrict}
      stormwater={stormwaterValue}
      showStormwater={showStormwater}
      selectedSegmentId={selectedSegmentId}
      onSelectSegment={onSelectSegment}
      citizenAggregates={citizenAggregatesValue}
      showCitizenAggregates={showCitizenAggregates}
      selectedCitizenCellKey={selectedCitizenCellKey}
      onSelectCitizenCell={onSelectCitizenCell}
      onSelectTrajectory={onSelectTrajectory}
      outputMode={outputMode}
      activeStep={activeStep}
      selectedTrajectoryId={selectedTrajectoryId}
      onBoundsChange={onBoundsChange}
    />
  );
}

afterEach(() => {
  cleanup();
  h.mapConstructor.mockClear();
  h.latest.current = null;
});

describe("MapView", () => {
  it("initializes an interactive MapLibre map with configured basemap and attribution", () => {
    render(mapElement());
    expect(screen.getByRole("region", { name: "互動式 GIS 地圖" })).toBeInTheDocument();
    expect(h.mapConstructor).toHaveBeenCalledWith(
      expect.objectContaining({
        style: expect.stringContaining("style.json"),
        center: [121.5654, 25.033],
        attributionControl: {},
      }),
    );
  });

  it("renders API edge geometry without rebuilding node-to-node lines", () => {
    const networkPreview = {
      ...preview,
      edges: [
        {
          ...preview.edges[0],
          geometry: {
            type: "LineString" as const,
            coordinates: [
              [121.55, 25.02] as [number, number],
              [121.56, 25.04] as [number, number],
              [121.58, 25.06] as [number, number],
            ],
          },
          source_id: "osm-way-1",
        },
      ],
    };
    render(mapElement({ preview: networkPreview, showSimulatedPaths: true }));
    const simulation = latestSourceData("ratsight-simulated-edges");
    expect(simulation.features).toHaveLength(1);
    expect(simulation.features[0].properties).toMatchObject({ source_id: "osm-way-1" });
    expect(simulation.features[0].geometry).toEqual(networkPreview.edges[0].geometry);
    expect(latestSourceData("ratsight-network-reference").features.length).toBeGreaterThan(0);
  });

  it("does not render unvisited synthetic edges", () => {
    const unvisitedPreview = {
      ...preview,
      edges: [{ ...preview.edges[0], visits: 0 }],
    };
    render(mapElement({ preview: unvisitedPreview, showSimulatedPaths: true }));
    const map = h.latest.current as { addSource: ReturnType<typeof vi.fn> };
    expect(map.addSource).toHaveBeenCalledWith(
      "ratsight-simulated-edges",
      expect.objectContaining({
        data: { type: "FeatureCollection", features: [] },
      }),
    );
  });

  it("dashes geometry-less schematic edges instead of drawing them as road lines", () => {
    render(mapElement({ preview, showSimulatedPaths: true }));
    const map = h.latest.current as {
      addSource: ReturnType<typeof vi.fn>;
      addLayer: ReturnType<typeof vi.fn>;
    };
    // The fixture graph has no edge geometry, so its single visited edge is schematic.
    const simulation = latestSourceData("ratsight-simulated-edges");
    expect(simulation.features[0].properties).toMatchObject({ schematic: true });
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-simulated-edges-schematic",
        type: "line",
        filter: ["==", ["get", "schematic"], true],
        paint: expect.objectContaining({ "line-dasharray": [1.5, 1.5] }),
      }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-simulated-edges-line",
        filter: ["!=", ["get", "schematic"], true],
      }),
    );
  });

  it("fits the map to the simulated network extent after a preview", () => {
    render(mapElement({ preview, showSimulatedPaths: true }));
    const map = h.latest.current as { fitBounds: ReturnType<typeof vi.fn> };
    expect(map.fitBounds).toHaveBeenCalledWith(
      [
        [121.55, 25.02],
        [121.58, 25.06],
      ],
      { padding: 56, duration: 500 },
    );
  });

  it("renders only the selected walker and clamps to its own step count", () => {
    const trajectoryPreview: SimulationPreview = {
      ...preview,
      trajectories: [
        {
          walker_id: 7,
          classification: "SIMULATED",
          edges: [
            {
              source: "a",
              target: "b",
              edge_id: "a-b",
              classification: "SIMULATED",
              geometry: [
                [121.55, 25.02],
                [121.56, 25.03],
              ],
            },
            {
              source: "b",
              target: "c",
              edge_id: "b-c",
              classification: "SIMULATED",
              geometry: [
                [121.56, 25.03],
                [121.57, 25.04],
              ],
            },
            {
              source: "c",
              target: "d",
              edge_id: "c-d",
              classification: "SIMULATED",
              geometry: [
                [121.57, 25.04],
                [121.58, 25.05],
              ],
            },
          ],
        },
        {
          walker_id: 8,
          classification: "SIMULATED",
          edges: [
            {
              source: "a",
              target: "b",
              edge_id: "a-b-short",
              classification: "SIMULATED",
              geometry: [
                [121.55, 25.02],
                [121.56, 25.03],
              ],
            },
          ],
        },
      ],
    };
    render(
      mapElement({
        preview: trajectoryPreview,
        outputMode: "trajectory",
        selectedTrajectoryId: 7,
        activeStep: 2,
      }),
    );
    const trajectory = latestSourceData("ratsight-trajectory-path");
    // Full route plus the traversed prefix for the selected walker only.
    expect(trajectory.features).toHaveLength(2);
    const [full, traversed] = trajectory.features;
    expect(full.properties.trajectory_id).toBe(7);
    expect(full.geometry).toEqual({
      type: "LineString",
      coordinates: [
        [121.55, 25.02],
        [121.56, 25.03],
        [121.57, 25.04],
        [121.58, 25.05],
      ],
    });
    expect(traversed.properties).toMatchObject({ trajectory_id: 7, step: 2 });
    expect(traversed.geometry).toEqual({
      type: "LineString",
      coordinates: [
        [121.55, 25.02],
        [121.56, 25.03],
        [121.57, 25.04],
      ],
    });
    expect(trajectory.features.some((feature) => feature.properties.trajectory_id === 8)).toBe(
      false,
    );
  });

  it("selects a trajectory when its map path is clicked", () => {
    const onSelectTrajectory = vi.fn();
    const trajectoryPreview: SimulationPreview = {
      ...preview,
      trajectories: [
        {
          walker_id: 7,
          classification: "SIMULATED",
          edges: [
            {
              source: "a",
              target: "b",
              edge_id: "a-b",
              classification: "SIMULATED",
              geometry: [
                [121.55, 25.02],
                [121.58, 25.06],
              ],
            },
          ],
        },
      ],
    };
    render(
      mapElement({
        preview: trajectoryPreview,
        showSimulatedPaths: true,
        outputMode: "trajectory",
        onSelectTrajectory,
      }),
    );
    const map = h.latest.current as { handlers: Record<string, HandlerEntry[]> };
    const click = map.handlers.click.find(
      (entry) => entry.layerId === "ratsight-simulated-edges-hit",
    );
    expect(click).toBeDefined();
    click!.handler({ features: [{ properties: { trajectory_id: 7 } }] });
    expect(onSelectTrajectory).toHaveBeenCalledWith(7);
  });

  it("adds the administrative source and fill/outline layers after style load", () => {
    render(mapElement({ boundaries, showBoundaries: true }));
    const map = h.latest.current as {
      addSource: ReturnType<typeof vi.fn>;
      addLayer: ReturnType<typeof vi.fn>;
    };
    expect(map.addSource).toHaveBeenCalledWith(
      "ratsight-administrative-districts",
      expect.objectContaining({
        type: "geojson",
        data: { type: "FeatureCollection", features: boundaries.features },
      }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-administrative-districts-fill",
        type: "fill",
        layout: expect.objectContaining({ visibility: "visible" }),
        paint: expect.objectContaining({ "fill-color": "#b7791f" }),
      }),
      "ratsight-simulated-edges-line",
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-administrative-districts-outline",
        type: "line",
        layout: expect.objectContaining({ visibility: "visible" }),
        paint: expect.objectContaining({ "line-color": "#8a5a12" }),
      }),
      "ratsight-simulated-edges-line",
    );
  });

  it("inserts boundaries beneath the simulated layer and respects visibility", () => {
    render(mapElement({ preview, showSimulatedPaths: false, boundaries, showBoundaries: false }));
    const map = h.latest.current as { addLayer: ReturnType<typeof vi.fn> };
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-administrative-districts-fill",
        layout: expect.objectContaining({ visibility: "none" }),
      }),
      "ratsight-simulated-edges-line",
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-administrative-districts-outline",
        layout: expect.objectContaining({ visibility: "none" }),
      }),
      "ratsight-simulated-edges-line",
    );
  });

  it("calls onSelectDistrict when a boundary feature is clicked", () => {
    const onSelectDistrict = vi.fn();
    render(mapElement({ boundaries, showBoundaries: true, onSelectDistrict }));
    const map = h.latest.current as { handlers: Record<string, HandlerEntry[]> };
    const click = map.handlers.click.find(
      (entry) => entry.layerId === "ratsight-administrative-districts-fill",
    );
    expect(click).toBeDefined();
    click!.handler({ features: [{ properties: boundaries.features[0].properties }] });
    expect(onSelectDistrict).toHaveBeenCalledWith(boundaries.features[0].properties);
  });

  it("highlights the selected district and updates the filter when selection changes", () => {
    const { rerender } = render(
      mapElement({ boundaries, showBoundaries: true, selectedDistrictId: "63000010" }),
    );
    const map = h.latest.current as {
      addLayer: ReturnType<typeof vi.fn>;
      setFilter: ReturnType<typeof vi.fn>;
    };
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-administrative-districts-highlight",
        type: "line",
        filter: ["==", ["get", "district_id"], ""],
      }),
      "ratsight-simulated-edges-line",
    );
    expect(map.setFilter).toHaveBeenCalledWith("ratsight-administrative-districts-highlight", [
      "==",
      ["get", "district_id"],
      "63000010",
    ]);
    map.setFilter.mockClear();
    rerender(mapElement({ boundaries, showBoundaries: false, selectedDistrictId: "63000010" }));
    rerender(mapElement({ boundaries, showBoundaries: true, selectedDistrictId: "63000010" }));
    expect(map.setFilter).toHaveBeenCalledWith("ratsight-administrative-districts-highlight", [
      "==",
      ["get", "district_id"],
      "63000010",
    ]);
    map.setFilter.mockClear();
    rerender(mapElement({ boundaries, showBoundaries: true, selectedDistrictId: null }));
    expect(map.setFilter).toHaveBeenCalledWith("ratsight-administrative-districts-highlight", [
      "==",
      ["get", "district_id"],
      "",
    ]);
  });

  it("pans the map to a district selected outside the viewport, once per selection", () => {
    const outside: AdministrativeDistricts = {
      ...boundaries,
      features: [
        {
          ...boundaries.features[0],
          id: "63000120",
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [121.0, 24.5],
                [121.05, 24.5],
                [121.05, 24.55],
                [121.0, 24.5],
              ],
            ],
          },
          properties: { ...boundaries.features[0].properties, district_id: "63000120" },
        },
      ],
    };
    const { rerender } = render(
      mapElement({ boundaries: outside, showBoundaries: true, selectedDistrictId: "63000120" }),
    );
    const map = h.latest.current as { fitBounds: ReturnType<typeof vi.fn> };
    expect(map.fitBounds).toHaveBeenCalledWith(
      [
        [121.0, 24.5],
        [121.05, 24.55],
      ],
      { padding: 40, duration: 500 },
    );
    rerender(
      mapElement({ boundaries: outside, showBoundaries: true, selectedDistrictId: "63000120" }),
    );
    expect(map.fitBounds).toHaveBeenCalledTimes(1);
  });

  it("pans without animation when the user prefers reduced motion", () => {
    const outside: AdministrativeDistricts = {
      ...boundaries,
      features: [
        {
          ...boundaries.features[0],
          id: "63000120",
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [121.0, 24.5],
                [121.05, 24.5],
                [121.05, 24.55],
                [121.0, 24.5],
              ],
            ],
          },
          properties: { ...boundaries.features[0].properties, district_id: "63000120" },
        },
      ],
    };
    const original = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: query === "(prefers-reduced-motion: reduce)",
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })) as unknown as typeof window.matchMedia;
    try {
      render(
        mapElement({ boundaries: outside, showBoundaries: true, selectedDistrictId: "63000120" }),
      );
      const map = h.latest.current as { fitBounds: ReturnType<typeof vi.fn> };
      expect(map.fitBounds).toHaveBeenCalledWith(
        [
          [121.0, 24.5],
          [121.05, 24.55],
        ],
        { padding: 40, duration: 0 },
      );
    } finally {
      window.matchMedia = original;
    }
  });

  it("leaves the camera alone for a district already in view", () => {
    render(mapElement({ boundaries, showBoundaries: true, selectedDistrictId: "63000010" }));
    const map = h.latest.current as { fitBounds: ReturnType<typeof vi.fn> };
    expect(map.fitBounds).not.toHaveBeenCalled();
  });

  it("removes stale boundary layers when the collection becomes empty", () => {
    const { rerender } = render(mapElement({ boundaries, showBoundaries: true }));
    const map = h.latest.current as {
      addSource: ReturnType<typeof vi.fn>;
      removeLayer: ReturnType<typeof vi.fn>;
      removeSource: ReturnType<typeof vi.fn>;
    };
    map.addSource.mockClear();
    rerender(mapElement({ boundaries: null, showBoundaries: true }));
    expect(map.removeLayer).toHaveBeenCalledWith("ratsight-administrative-districts-fill");
    expect(map.removeLayer).toHaveBeenCalledWith("ratsight-administrative-districts-outline");
    expect(map.removeSource).toHaveBeenCalledWith("ratsight-administrative-districts");
    expect(map.addSource).not.toHaveBeenCalled();
  });

  it("requests the current viewport bbox after style load", () => {
    const onBoundsChange = vi.fn();
    render(mapElement({ onBoundsChange }));
    expect(onBoundsChange).toHaveBeenCalledWith([121.5, 24.98, 121.63, 25.09]);
  });

  it("adds the stormwater source and line/highlight layers beneath simulation", () => {
    render(mapElement({ stormwater, showStormwater: true }));
    const map = h.latest.current as {
      addSource: ReturnType<typeof vi.fn>;
      addLayer: ReturnType<typeof vi.fn>;
    };
    expect(map.addSource).toHaveBeenCalledWith(
      "ratsight-stormwater-pipelines",
      expect.objectContaining({
        type: "geojson",
        data: { type: "FeatureCollection", features: stormwater.features },
      }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-stormwater-pipelines-line",
        type: "line",
        layout: expect.objectContaining({ visibility: "visible" }),
        paint: expect.objectContaining({ "line-color": "#2563eb" }),
      }),
      "ratsight-simulated-edges-line",
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-stormwater-pipelines-highlight",
        type: "line",
        filter: ["==", ["get", "segment_id"], ""],
      }),
      "ratsight-simulated-edges-line",
    );
  });

  it("calls onSelectSegment when a stormwater line is clicked", () => {
    const onSelectSegment = vi.fn();
    render(mapElement({ stormwater, showStormwater: true, onSelectSegment }));
    const map = h.latest.current as { handlers: Record<string, HandlerEntry[]> };
    const click = map.handlers.click.find(
      (entry) => entry.layerId === "ratsight-stormwater-pipelines-line",
    );
    expect(click).toBeDefined();
    click!.handler({ features: [{ properties: stormwater.features[0].properties }] });
    expect(onSelectSegment).toHaveBeenCalledWith(stormwater.features[0].properties);
  });

  it("removes stale stormwater layers when the collection is empty", () => {
    const { rerender } = render(mapElement({ stormwater, showStormwater: true }));
    const map = h.latest.current as {
      addSource: ReturnType<typeof vi.fn>;
      removeLayer: ReturnType<typeof vi.fn>;
      removeSource: ReturnType<typeof vi.fn>;
    };
    map.addSource.mockClear();
    rerender(mapElement({ stormwater: null, showStormwater: true }));
    expect(map.removeLayer).toHaveBeenCalledWith("ratsight-stormwater-pipelines-line");
    expect(map.removeLayer).toHaveBeenCalledWith("ratsight-stormwater-pipelines-highlight");
    expect(map.removeSource).toHaveBeenCalledWith("ratsight-stormwater-pipelines");
    expect(map.addSource).not.toHaveBeenCalled();
  });

  it("draws citizen-report aggregates as a suppressed cell layer", () => {
    render(mapElement({ citizenAggregates, showCitizenAggregates: true }));
    expect(screen.getByRole("region", { name: "互動式 GIS 地圖" })).toHaveAttribute(
      "data-citizen-aggregates",
      "visible",
    );
    const map = h.latest.current as {
      addSource: ReturnType<typeof vi.fn>;
      addLayer: ReturnType<typeof vi.fn>;
    };
    expect(map.addSource).toHaveBeenCalledWith(
      "ratsight-citizen-report-aggregates",
      expect.objectContaining({
        type: "geojson",
        data: expect.objectContaining({
          type: "FeatureCollection",
          features: [
            expect.objectContaining({
              geometry: expect.objectContaining({ type: "Point" }),
              properties: expect.objectContaining({
                ...citizenAggregates.features[0].properties,
                feature_key: "g250m:1:2:2026-05:sighting",
              }),
            }),
          ],
        }),
      }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-citizen-report-aggregates-point",
        type: "circle",
        layout: expect.objectContaining({ visibility: "visible" }),
        paint: expect.objectContaining({
          "circle-color": [
            "case",
            ["==", ["get", "data_class"], "SYNTHETIC_AGGREGATE_FIXTURE"],
            "#5b6b7a",
            "#a3243c",
          ],
        }),
      }),
      "ratsight-simulated-edges-line",
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-citizen-report-aggregates-highlight",
        type: "circle",
        filter: ["==", ["get", "feature_key"], ""],
      }),
      "ratsight-simulated-edges-line",
    );
  });

  it("highlights the focused citizen-report marker", () => {
    const { rerender } = render(
      mapElement({
        citizenAggregates,
        showCitizenAggregates: true,
        selectedCitizenCellKey: "g250m:1:2:2026-05:sighting",
      }),
    );
    const map = h.latest.current as { setFilter: ReturnType<typeof vi.fn> };
    rerender(
      mapElement({
        citizenAggregates,
        showCitizenAggregates: true,
        selectedCitizenCellKey: "g250m:9:9:2026-06:other",
      }),
    );
    expect(map.setFilter).toHaveBeenCalledWith("ratsight-citizen-report-aggregates-highlight", [
      "==",
      ["get", "feature_key"],
      "g250m:9:9:2026-06:other",
    ]);
  });

  it("selects representative citizen-report markers", () => {
    const onSelectCitizenCell = vi.fn();
    render(mapElement({ citizenAggregates, showCitizenAggregates: true, onSelectCitizenCell }));
    const map = h.latest.current as { handlers: Record<string, HandlerEntry[]> };
    const click = map.handlers.click.find(
      (entry) => entry.layerId === "ratsight-citizen-report-aggregates-point",
    );
    expect(click).toBeDefined();
    click!.handler({ features: [{ properties: citizenAggregates.features[0].properties }] });
    expect(onSelectCitizenCell).toHaveBeenCalledWith(citizenAggregates.features[0].properties);
  });

  it("draws isolated synthetic fixtures with non-report styling", () => {
    const fixture: CitizenReportAggregates = {
      ...citizenAggregates,
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
          geometry: citizenAggregates.features[0].geometry,
          properties: {
            ...citizenAggregates.features[0].properties,
            count: null,
            data_class: "SYNTHETIC_AGGREGATE_FIXTURE",
            classification: "SIMULATED",
            attribution: "SIMULATED local fixture; not citizen-report data.",
          },
        },
      ],
    };
    render(mapElement({ citizenAggregates: fixture, showCitizenAggregates: true }));
    const map = h.latest.current as { addLayer: ReturnType<typeof vi.fn> };
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-citizen-report-aggregates-point",
        paint: expect.objectContaining({
          "circle-color": [
            "case",
            ["==", ["get", "data_class"], "SYNTHETIC_AGGREGATE_FIXTURE"],
            "#5b6b7a",
            "#a3243c",
          ],
        }),
      }),
      "ratsight-simulated-edges-line",
    );
  });

  it("honors an explicit caller opt-out for citizen-report cells", () => {
    render(mapElement({ citizenAggregates, showCitizenAggregates: false }));
    expect(screen.getByRole("region", { name: "互動式 GIS 地圖" })).toHaveAttribute(
      "data-citizen-aggregates",
      "hidden",
    );
  });
});
