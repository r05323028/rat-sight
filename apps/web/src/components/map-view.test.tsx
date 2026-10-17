import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  AdministrativeDistricts,
  RodentReports,
  SimulationPreview,
  StormwaterNetwork,
} from "@/lib/api";

const h = vi.hoisted(() => ({
  mapConstructor: vi.fn(),
  latest: { current: null as unknown },
}));

type HandlerEntry = { layerId?: string; handler: (...args: unknown[]) => void };

vi.mock("maplibre-gl", () => ({
  setWorkerUrl: vi.fn(),
  Map: class {
    handlers: Record<string, HandlerEntry[]> = {};
    sources = new Set<string>();
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
      this.sources.add(id);
      return this;
    });
    getSource = vi.fn((id: string) => (this.sources.has(id) ? { id } : undefined));
    removeSource = vi.fn((id: string) => {
      this.sources.delete(id);
      return this;
    });
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
    getBounds = () => ({
      getWest: () => 121.5,
      getSouth: () => 24.98,
      getEast: () => 121.63,
      getNorth: () => 25.09,
    });
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

const rodentReports: RodentReports = {
  type: "FeatureCollection",
  data_state: "available",
  data_class: "RODENT_REPORT",
  classification: "SIMULATED",
  feature_count: 1,
  bbox: [121.5, 24.98, 121.63, 25.09],
  reported_from: null,
  reported_to: null,
  truncated: false,
  provenance: null,
  features: [
    {
      type: "Feature",
      id: "report-1",
      geometry: { type: "Point", coordinates: [121.55, 25.02] },
      properties: {
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
  rodentReports?: RodentReports | null;
  showRodentReports?: boolean;
  selectedReportId?: string | null;
  onSelectReport?: (properties: unknown) => void;
  onBoundsChange?: (bbox: [number, number, number, number]) => void;
};

function mapElement({
  preview: previewValue = null,
  showSimulatedPaths = false,
  boundaries: boundariesValue = null,
  showBoundaries = false,
  selectedDistrictId = null,
  onSelectDistrict = vi.fn(),
  stormwater: stormwaterValue = null,
  showStormwater = false,
  selectedSegmentId = null,
  onSelectSegment = vi.fn(),
  rodentReports: rodentReportsValue = null,
  showRodentReports = false,
  selectedReportId = null,
  onSelectReport = vi.fn(),
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
      rodentReports={rodentReportsValue}
      showRodentReports={showRodentReports}
      selectedReportId={selectedReportId}
      onSelectReport={onSelectReport}
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
    expect(screen.getByRole("region", { name: "Interactive GIS map" })).toBeInTheDocument();
    expect(h.mapConstructor).toHaveBeenCalledWith(
      expect.objectContaining({
        style: expect.stringContaining("style.json"),
        center: [121.5654, 25.033],
        attributionControl: {},
      }),
    );
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
      undefined,
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-administrative-districts-outline",
        type: "line",
        layout: expect.objectContaining({ visibility: "visible" }),
        paint: expect.objectContaining({ "line-color": "#8a5a12" }),
      }),
      undefined,
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
      undefined,
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
      undefined,
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-stormwater-pipelines-highlight",
        type: "line",
        filter: ["==", ["get", "segment_id"], ""],
      }),
      undefined,
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

  it("adds the rodent report source and point/highlight layers", () => {
    render(mapElement({ rodentReports, showRodentReports: true }));
    const map = h.latest.current as {
      addSource: ReturnType<typeof vi.fn>;
      addLayer: ReturnType<typeof vi.fn>;
    };
    expect(map.addSource).toHaveBeenCalledWith(
      "ratsight-rodent-reports",
      expect.objectContaining({
        type: "geojson",
        data: { type: "FeatureCollection", features: rodentReports.features },
      }),
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-rodent-reports-point",
        type: "circle",
        layout: expect.objectContaining({ visibility: "visible" }),
        paint: expect.objectContaining({ "circle-color": "#be123c" }),
      }),
      undefined,
    );
    expect(map.addLayer).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ratsight-rodent-reports-highlight",
        type: "circle",
        filter: ["==", ["get", "report_id"], ""],
      }),
      undefined,
    );
  });

  it("calls onSelectReport when a rodent report point is clicked", () => {
    const onSelectReport = vi.fn();
    render(mapElement({ rodentReports, showRodentReports: true, onSelectReport }));
    const map = h.latest.current as { handlers: Record<string, HandlerEntry[]> };
    const click = map.handlers.click.find(
      (entry) => entry.layerId === "ratsight-rodent-reports-point",
    );
    expect(click).toBeDefined();
    click!.handler({ features: [{ properties: rodentReports.features[0].properties }] });
    expect(onSelectReport).toHaveBeenCalledWith(rodentReports.features[0].properties);
  });
});
