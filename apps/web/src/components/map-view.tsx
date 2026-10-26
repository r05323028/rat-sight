"use client";

import { useEffect, useRef } from "react";
import {
  Map as MapLibreMap,
  NavigationControl,
  setWorkerUrl,
  type FilterSpecification,
  type MapLayerMouseEvent,
} from "maplibre-gl";

import type {
  AdministrativeDistrictGeometry,
  AdministrativeDistrictProperties,
  AdministrativeDistricts,
  RodentReportProperties,
  RodentReports,
  SimulationPreview,
  SimulationTrajectoryStep,
  StormwaterBbox,
  StormwaterNetwork,
  StormwaterProperties,
} from "@/lib/api";

setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");

const STYLE_URL =
  process.env.NEXT_PUBLIC_MAP_STYLE_URL ??
  "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";
const NETWORK_REFERENCE_SOURCE = "ratsight-network-reference";
const NETWORK_REFERENCE_LAYER = "ratsight-network-reference-line";
const SIMULATION_SOURCE = "ratsight-simulated-edges";
const SIMULATION_LAYER = "ratsight-simulated-edges-line";
// Geometry-less schematic edges are dashed so a straight node-to-node shortcut is never
// read as surveyed road geometry.
const SIMULATION_SCHEMATIC_LAYER = "ratsight-simulated-edges-schematic";
const SCHEMATIC_EXCLUDED: FilterSpecification = ["!=", ["get", "schematic"], true];
const SCHEMATIC_ONLY: FilterSpecification = ["==", ["get", "schematic"], true];
// Wide transparent line so a click near a path still selects it.
const SIMULATION_HIT_LAYER = "ratsight-simulated-edges-hit";
const SIMULATION_STEP_SOURCE = "ratsight-simulated-current-step";
const SIMULATION_STEP_LAYER = "ratsight-simulated-current-step-line";
const ORIGIN_SOURCE = "ratsight-origin-nodes";
const ORIGIN_LAYER = "ratsight-origin-nodes-point";
const ORIGIN_SELECTED_LAYER = "ratsight-origin-nodes-selected";
const BOUNDARY_SOURCE = "ratsight-administrative-districts";
const BOUNDARY_FILL_LAYER = "ratsight-administrative-districts-fill";
const BOUNDARY_OUTLINE_LAYER = "ratsight-administrative-districts-outline";
const BOUNDARY_HIGHLIGHT_LAYER = "ratsight-administrative-districts-highlight";
const STORMWATER_SOURCE = "ratsight-stormwater-pipelines";
const STORMWATER_LINE_LAYER = "ratsight-stormwater-pipelines-line";
const STORMWATER_HIGHLIGHT_LAYER = "ratsight-stormwater-pipelines-highlight";
const RODENT_REPORT_SOURCE = "ratsight-rodent-reports";
const RODENT_REPORT_POINT_LAYER = "ratsight-rodent-reports-point";
const RODENT_REPORT_HIGHLIGHT_LAYER = "ratsight-rodent-reports-highlight";

function geometryBounds(
  geometry: AdministrativeDistrictGeometry,
): [[number, number], [number, number]] {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  const visit = (value: unknown): void => {
    if (Array.isArray(value) && typeof value[0] === "number" && typeof value[1] === "number") {
      const [x, y] = value as [number, number];
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
      return;
    }
    if (Array.isArray(value)) value.forEach(visit);
  };
  visit(geometry.coordinates);
  return [
    [minX, minY],
    [maxX, maxY],
  ];
}

function coordinateBounds(coordinates: unknown): [[number, number], [number, number]] | null {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  const visit = (value: unknown): void => {
    if (Array.isArray(value) && typeof value[0] === "number" && typeof value[1] === "number") {
      const [x, y] = value as [number, number];
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
      return;
    }
    if (Array.isArray(value)) value.forEach(visit);
  };
  visit(coordinates);
  return [minX, minY, maxX, maxY].every(Number.isFinite)
    ? [
        [minX, minY],
        [maxX, maxY],
      ]
    : null;
}

// isStyleLoaded() keeps reporting false while basemap tiles stream, so a redraw
// must be gated on the one-time style load instead of a live check.
function onStyled(map: MapLibreMap, ready: () => boolean, draw: () => void): () => void {
  if (ready()) {
    draw();
    return () => {};
  }
  const attempt = () => {
    if (ready()) draw();
  };
  map.on("load", attempt);
  return () => map.off("load", attempt);
}

function panDuration(): number {
  return typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ? 0
    : 500;
}

type MapViewProps = {
  preview: SimulationPreview | null;
  showSimulatedPaths: boolean;
  showNetworkReference?: boolean;
  outputMode?: "aggregate" | "trajectory";
  boundaries: AdministrativeDistricts | null;
  showBoundaries: boolean;
  selectedDistrictId: string | null;
  onSelectDistrict: (properties: AdministrativeDistrictProperties) => void;
  stormwater: StormwaterNetwork | null;
  showStormwater: boolean;
  selectedSegmentId: string | null;
  onSelectSegment: (properties: StormwaterProperties) => void;
  rodentReports: RodentReports | null;
  showRodentReports: boolean;
  selectedReportId: string | null;
  onSelectReport: (properties: RodentReportProperties) => void;
  onSelectTrajectory?: (trajectoryId: number) => void;
  // Number of returned trajectory edges to draw (0 = origin only); null/undefined draws all.
  activeStep?: number | null;
  selectedTrajectoryId?: number | null;
  // Eligible synthetic origin nodes come from the last preview response, not from clicks on arbitrary coordinates.
  originNodes?: { id: string; coordinates: [number, number] }[];
  selectedOriginNodeId?: string | null;
  onSelectOriginNode?: (nodeId: string) => void;
  onBoundsChange: (bbox: StormwaterBbox) => void;
};

export function MapView({
  preview,
  showSimulatedPaths,
  showNetworkReference = false,
  outputMode = "aggregate",
  boundaries,
  showBoundaries,
  selectedDistrictId,
  onSelectDistrict,
  stormwater,
  showStormwater,
  selectedSegmentId,
  onSelectSegment,
  rodentReports,
  showRodentReports,
  selectedReportId,
  onSelectReport,
  onSelectTrajectory,
  activeStep = null,
  selectedTrajectoryId = null,
  originNodes = [],
  selectedOriginNodeId = null,
  onSelectOriginNode,
  onBoundsChange,
}: MapViewProps) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const lastBoundsKey = useRef<string | null>(null);
  const fittedDistrictRef = useRef<string | null>(null);
  const fittedPreviewRef = useRef<SimulationPreview | null>(null);
  const styleReady = useRef(false);
  const boundsTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const map = new MapLibreMap({
      container: container.current,
      style: STYLE_URL,
      center: [121.5654, 25.033],
      zoom: 11.5,
      attributionControl: {},
    });
    mapRef.current = map;
    styleReady.current = map.isStyleLoaded() ?? false;
    map.once("load", () => {
      styleReady.current = true;
      container.current?.setAttribute("data-map-ready", "true");
    });
    map.addControl(new NavigationControl(), "top-right");
    const navigationLabels = [
      [".maplibregl-ctrl-zoom-in", "放大地圖"],
      [".maplibregl-ctrl-zoom-out", "縮小地圖"],
      [".maplibregl-ctrl-compass", "重設地圖方向"],
    ] as const;
    for (const [selector, label] of navigationLabels) {
      const control = container.current.querySelector<HTMLButtonElement>(selector);
      control?.setAttribute("aria-label", label);
      control?.setAttribute("title", label);
    }
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      if (!styleReady.current) return;
      if (map.getLayer(SIMULATION_STEP_LAYER)) map.removeLayer(SIMULATION_STEP_LAYER);
      if (map.getSource(SIMULATION_STEP_SOURCE)) map.removeSource(SIMULATION_STEP_SOURCE);
      if (map.getLayer(ORIGIN_SELECTED_LAYER)) map.removeLayer(ORIGIN_SELECTED_LAYER);
      if (map.getLayer(ORIGIN_LAYER)) map.removeLayer(ORIGIN_LAYER);
      if (map.getSource(ORIGIN_SOURCE)) map.removeSource(ORIGIN_SOURCE);
      if (map.getLayer(SIMULATION_HIT_LAYER)) map.removeLayer(SIMULATION_HIT_LAYER);
      if (map.getLayer(SIMULATION_SCHEMATIC_LAYER)) map.removeLayer(SIMULATION_SCHEMATIC_LAYER);
      if (map.getLayer(SIMULATION_LAYER)) map.removeLayer(SIMULATION_LAYER);
      if (map.getLayer(NETWORK_REFERENCE_LAYER)) map.removeLayer(NETWORK_REFERENCE_LAYER);
      if (map.getSource(SIMULATION_SOURCE)) map.removeSource(SIMULATION_SOURCE);
      if (map.getSource(NETWORK_REFERENCE_SOURCE)) map.removeSource(NETWORK_REFERENCE_SOURCE);
      if (!preview) return;
      // Source-network LineStrings come from API; endpoint fallback remains only for legacy synthetic fixtures.
      const nodes = new Map(preview.nodes.map((node) => [node.id, node.coordinates]));
      const networkFeatures = preview.edges.flatMap((edge) =>
        edge.geometry
          ? [
              {
                type: "Feature" as const,
                properties: {
                  edge_id: edge.edge_id,
                  source_id: edge.source_id ?? edge.edge_id,
                  classification: "REFERENCE",
                },
                geometry: edge.geometry,
              },
            ]
          : [],
      );
      const simulationFeatures = preview.edges.flatMap((edge) => {
        if (edge.geometry) return [];
        const start = nodes.get(edge.source);
        const end = nodes.get(edge.target);
        return start && end
          ? [
              {
                type: "Feature" as const,
                properties: { edge_id: edge.edge_id, classification: "SIMULATED", schematic: true },
                geometry: { type: "LineString" as const, coordinates: [start, end] },
              },
            ]
          : [];
      });
      const clampedStep =
        typeof activeStep === "number"
          ? Math.max(
              0,
              Math.min(
                activeStep,
                ...(preview.trajectories
                  ? preview.trajectories.map((trajectory) => trajectory.edges.length)
                  : [0]),
              ),
            )
          : null;
      const edgesThroughStep = (trajectoryEdges: SimulationTrajectoryStep[]) =>
        clampedStep === null ? trajectoryEdges : trajectoryEdges.slice(0, clampedStep);
      // Edges without any geometry mean the schematic graph: its trajectory segments are
      // straight node-to-node shortcuts, so they get the same dashed treatment.
      const networkIsSchematic =
        preview.edges.length > 0 && preview.edges.every((edge) => !edge.geometry);
      const simulatedFeatures =
        outputMode === "trajectory" && preview.trajectories
          ? preview.trajectories
              .map((trajectory) => ({ trajectory, edges: edgesThroughStep(trajectory.edges) }))
              .filter(({ edges }) => edges.length > 0)
              .map(({ trajectory, edges }) => ({
                type: "Feature" as const,
                properties: {
                  trajectory_id: trajectory.walker_id,
                  classification: "SIMULATED",
                  step: edges.length,
                  ...(networkIsSchematic ? { schematic: true } : {}),
                },
                geometry: {
                  type: "LineString" as const,
                  coordinates: edges.flatMap((edge, index) =>
                    index === 0 ? edge.geometry : edge.geometry.slice(1),
                  ),
                },
              }))
          : [...networkFeatures, ...simulationFeatures]
              .filter((feature) => {
                const edge = preview.edges.find(
                  (candidate) => candidate.edge_id === feature.properties.edge_id,
                );
                return edge?.visits ? edge.visits > 0 : false;
              })
              .map((feature) => ({
                ...feature,
                properties: {
                  ...feature.properties,
                  classification: "SIMULATED",
                  visits:
                    preview.edges.find((edge) => edge.edge_id === feature.properties.edge_id)
                      ?.visits ?? 0,
                },
              }));
      map.addSource(NETWORK_REFERENCE_SOURCE, {
        type: "geojson",
        data: { type: "FeatureCollection", features: networkFeatures },
      });
      map.addLayer({
        id: NETWORK_REFERENCE_LAYER,
        type: "line",
        source: NETWORK_REFERENCE_SOURCE,
        layout: {
          "line-cap": "round",
          "line-join": "round",
          visibility: showNetworkReference ? "visible" : "none",
        },
        paint: { "line-color": "#64748b", "line-width": 2, "line-opacity": 0.55 },
      });
      map.addSource(SIMULATION_SOURCE, {
        type: "geojson",
        data: { type: "FeatureCollection", features: simulatedFeatures },
      });
      map.addLayer({
        id: SIMULATION_LAYER,
        type: "line",
        source: SIMULATION_SOURCE,
        layout: {
          "line-cap": "round",
          "line-join": "round",
          visibility: showSimulatedPaths ? "visible" : "none",
        },
        filter: SCHEMATIC_EXCLUDED,
        paint: { "line-color": "#0f766e", "line-width": 3, "line-opacity": 0.8 },
      });
      map.addLayer({
        id: SIMULATION_SCHEMATIC_LAYER,
        type: "line",
        source: SIMULATION_SOURCE,
        filter: SCHEMATIC_ONLY,
        layout: {
          "line-cap": "butt",
          "line-join": "round",
          visibility: showSimulatedPaths ? "visible" : "none",
        },
        paint: {
          "line-color": "#0f766e",
          "line-width": 2,
          "line-opacity": 0.75,
          "line-dasharray": [1.5, 1.5],
        },
      });
      map.addLayer({
        id: SIMULATION_HIT_LAYER,
        type: "line",
        source: SIMULATION_SOURCE,
        layout: {
          "line-cap": "round",
          "line-join": "round",
          visibility: showSimulatedPaths ? "visible" : "none",
        },
        paint: { "line-color": "#0f766e", "line-opacity": 0, "line-width": 16 },
      });
      const currentStepFeatures =
        outputMode === "trajectory" && clampedStep && clampedStep > 0
          ? (preview.trajectories ?? [])
              .filter((trajectory) => trajectory.walker_id === selectedTrajectoryId)
              .flatMap((trajectory) => {
                const edge = trajectory.edges[clampedStep - 1];
                return edge
                  ? [
                      {
                        type: "Feature" as const,
                        properties: {
                          trajectory_id: trajectory.walker_id,
                          step_index: edge.step_index ?? clampedStep - 1,
                          classification: "SIMULATED",
                        },
                        geometry: { type: "LineString" as const, coordinates: edge.geometry },
                      },
                    ]
                  : [];
              })
          : [];
      map.addSource(SIMULATION_STEP_SOURCE, {
        type: "geojson",
        data: { type: "FeatureCollection", features: currentStepFeatures },
      });
      map.addLayer({
        id: SIMULATION_STEP_LAYER,
        type: "line",
        source: SIMULATION_STEP_SOURCE,
        layout: { "line-cap": "round", "line-join": "round", visibility: "visible" },
        paint: { "line-color": "#b91c1c", "line-width": 5, "line-opacity": 0.95 },
      });
      map.addSource(ORIGIN_SOURCE, {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: originNodes.map((node) => ({
            type: "Feature" as const,
            properties: { node_id: node.id, classification: "SIMULATED" },
            geometry: { type: "Point" as const, coordinates: node.coordinates },
          })),
        },
      });
      map.addLayer({
        id: ORIGIN_LAYER,
        type: "circle",
        source: ORIGIN_SOURCE,
        paint: {
          "circle-radius": 5,
          "circle-color": "#0f766e",
          "circle-opacity": 0.75,
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 1,
        },
      });
      map.addLayer({
        id: ORIGIN_SELECTED_LAYER,
        type: "circle",
        source: ORIGIN_SOURCE,
        filter: ["==", ["get", "node_id"], selectedOriginNodeId ?? ""],
        paint: {
          "circle-radius": 9,
          "circle-color": "#b91c1c",
          "circle-opacity": 0.9,
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 2,
        },
      });
    };
    const unsubscribe = onStyled(map, () => styleReady.current, update);
    const handleTrajectoryClick = (event: MapLayerMouseEvent) => {
      const trajectoryId = event.features?.[0]?.properties?.trajectory_id;
      if (typeof trajectoryId === "number") onSelectTrajectory?.(trajectoryId);
    };
    const handleMouseEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
    };
    map.on("click", SIMULATION_HIT_LAYER, handleTrajectoryClick);
    map.on("mouseenter", SIMULATION_HIT_LAYER, handleMouseEnter);
    map.on("mouseleave", SIMULATION_HIT_LAYER, handleMouseLeave);
    // Origin picks are limited to nodes the API returned, so no coordinate snapping happens here.
    const handleOriginClick = (event: MapLayerMouseEvent) => {
      const nodeId = event.features?.[0]?.properties?.node_id;
      if (typeof nodeId === "string") onSelectOriginNode?.(nodeId);
    };
    map.on("click", ORIGIN_LAYER, handleOriginClick);
    map.on("mouseenter", ORIGIN_LAYER, handleMouseEnter);
    map.on("mouseleave", ORIGIN_LAYER, handleMouseLeave);
    return () => {
      unsubscribe();
      map.off("click", SIMULATION_HIT_LAYER, handleTrajectoryClick);
      map.off("mouseenter", SIMULATION_HIT_LAYER, handleMouseEnter);
      map.off("mouseleave", SIMULATION_HIT_LAYER, handleMouseLeave);
      map.off("click", ORIGIN_LAYER, handleOriginClick);
      map.off("mouseenter", ORIGIN_LAYER, handleMouseEnter);
      map.off("mouseleave", ORIGIN_LAYER, handleMouseLeave);
    };
  }, [
    preview,
    outputMode,
    showSimulatedPaths,
    showNetworkReference,
    onSelectTrajectory,
    activeStep,
    selectedTrajectoryId,
    originNodes,
    selectedOriginNodeId,
    onSelectOriginNode,
  ]);

  // The study network is sub-kilometre while the default Taipei view is not, so
  // without fitting it the trajectory geometry is a few pixels and clicks land on
  // the basemap instead of the path.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !preview || fittedPreviewRef.current === preview) return;
    const bounds = coordinateBounds([
      preview.nodes.map((node) => node.coordinates),
      preview.edges.map((edge) => edge.geometry?.coordinates ?? null),
    ]);
    if (!bounds) return;
    // fitBounds only needs the camera transform: waiting for the style would mean
    // the fit lands only after a source finishes loading.
    fittedPreviewRef.current = preview;
    map.fitBounds(bounds, { padding: 56, duration: panDuration() });
  }, [preview]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const removeBoundaryLayer = () => {
      if (map.getLayer(BOUNDARY_HIGHLIGHT_LAYER)) map.removeLayer(BOUNDARY_HIGHLIGHT_LAYER);
      if (map.getLayer(BOUNDARY_OUTLINE_LAYER)) map.removeLayer(BOUNDARY_OUTLINE_LAYER);
      if (map.getLayer(BOUNDARY_FILL_LAYER)) map.removeLayer(BOUNDARY_FILL_LAYER);
      if (map.getSource(BOUNDARY_SOURCE)) map.removeSource(BOUNDARY_SOURCE);
    };

    const update = () => {
      if (!styleReady.current) return;
      removeBoundaryLayer();
      if (!boundaries || boundaries.features.length === 0) return;
      map.addSource(BOUNDARY_SOURCE, {
        type: "geojson",
        data: { type: "FeatureCollection", features: boundaries.features },
      });
      // Keep the administrative reference geometry beneath simulated movement.
      const beforeId = map.getLayer(SIMULATION_LAYER) ? SIMULATION_LAYER : undefined;
      const visibility = showBoundaries ? "visible" : "none";
      map.addLayer(
        {
          id: BOUNDARY_FILL_LAYER,
          type: "fill",
          source: BOUNDARY_SOURCE,
          layout: { visibility },
          paint: { "fill-color": "#b7791f", "fill-opacity": 0.08 },
        },
        beforeId,
      );
      map.addLayer(
        {
          id: BOUNDARY_OUTLINE_LAYER,
          type: "line",
          source: BOUNDARY_SOURCE,
          layout: { visibility, "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#8a5a12", "line-width": 1.25, "line-opacity": 0.9 },
        },
        beforeId,
      );
      map.addLayer(
        {
          id: BOUNDARY_HIGHLIGHT_LAYER,
          type: "line",
          source: BOUNDARY_SOURCE,
          layout: { visibility, "line-cap": "round", "line-join": "round" },
          filter: ["==", ["get", "district_id"], ""],
          paint: { "line-color": "#5c3d0a", "line-width": 2.75, "line-opacity": 1 },
        },
        beforeId,
      );
    };

    const handleClick = (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature?.properties) {
        onSelectDistrict(feature.properties as AdministrativeDistrictProperties);
      }
    };
    const handleMouseEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
    };

    const unsubscribe = onStyled(map, () => styleReady.current, update);
    map.on("click", BOUNDARY_FILL_LAYER, handleClick);
    map.on("mouseenter", BOUNDARY_FILL_LAYER, handleMouseEnter);
    map.on("mouseleave", BOUNDARY_FILL_LAYER, handleMouseLeave);
    return () => {
      unsubscribe();
      map.off("click", BOUNDARY_FILL_LAYER, handleClick);
      map.off("mouseenter", BOUNDARY_FILL_LAYER, handleMouseEnter);
      map.off("mouseleave", BOUNDARY_FILL_LAYER, handleMouseLeave);
    };
  }, [boundaries, showBoundaries, onSelectDistrict]);

  // Keep the map highlight synchronized with the selection made from the
  // keyboard-accessible district list or from a map click. List selections can
  // name a district outside the current viewport, so reveal it before it is
  // reported as selected.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = () => {
      if (!map.getLayer(BOUNDARY_HIGHLIGHT_LAYER)) return;
      map.setFilter(BOUNDARY_HIGHLIGHT_LAYER, [
        "==",
        ["get", "district_id"],
        selectedDistrictId ?? "",
      ]);
      const district = boundaries?.features.find(
        (feature) => feature.properties.district_id === selectedDistrictId,
      );
      if (!district || fittedDistrictRef.current === selectedDistrictId) return;
      const [[minX, minY], [maxX, maxY]] = geometryBounds(district.geometry);
      const view = map.getBounds();
      const inView =
        view.getWest() <= minX &&
        view.getEast() >= maxX &&
        view.getSouth() <= minY &&
        view.getNorth() >= maxY;
      if (inView) return;
      fittedDistrictRef.current = selectedDistrictId;
      map.fitBounds(
        [
          [minX, minY],
          [maxX, maxY],
        ],
        { padding: 40, duration: panDuration() },
      );
    };
    const unsubscribe = onStyled(map, () => styleReady.current, apply);
    return () => {
      unsubscribe();
    };
  }, [selectedDistrictId, boundaries, showBoundaries]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const removeStormwaterLayer = () => {
      if (map.getLayer(STORMWATER_HIGHLIGHT_LAYER)) map.removeLayer(STORMWATER_HIGHLIGHT_LAYER);
      if (map.getLayer(STORMWATER_LINE_LAYER)) map.removeLayer(STORMWATER_LINE_LAYER);
      if (map.getSource(STORMWATER_SOURCE)) map.removeSource(STORMWATER_SOURCE);
    };

    const update = () => {
      if (!styleReady.current) return;
      removeStormwaterLayer();
      if (!stormwater || stormwater.features.length === 0) return;
      map.addSource(STORMWATER_SOURCE, {
        type: "geojson",
        data: { type: "FeatureCollection", features: stormwater.features },
      });
      // Keep infrastructure reference geometry beneath simulated movement.
      const beforeId = map.getLayer(SIMULATION_LAYER) ? SIMULATION_LAYER : undefined;
      const visibility = showStormwater ? "visible" : "none";
      map.addLayer(
        {
          id: STORMWATER_LINE_LAYER,
          type: "line",
          source: STORMWATER_SOURCE,
          layout: { visibility, "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#2563eb", "line-width": 1.5, "line-opacity": 0.85 },
        },
        beforeId,
      );
      map.addLayer(
        {
          id: STORMWATER_HIGHLIGHT_LAYER,
          type: "line",
          source: STORMWATER_SOURCE,
          layout: { visibility, "line-cap": "round", "line-join": "round" },
          filter: ["==", ["get", "segment_id"], ""],
          paint: { "line-color": "#1e3a8a", "line-width": 3.25, "line-opacity": 1 },
        },
        beforeId,
      );
    };

    const handleClick = (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature?.properties) {
        onSelectSegment(feature.properties as StormwaterProperties);
      }
    };
    const handleMouseEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
    };

    const unsubscribe = onStyled(map, () => styleReady.current, update);
    map.on("click", STORMWATER_LINE_LAYER, handleClick);
    map.on("mouseenter", STORMWATER_LINE_LAYER, handleMouseEnter);
    map.on("mouseleave", STORMWATER_LINE_LAYER, handleMouseLeave);
    return () => {
      unsubscribe();
      map.off("click", STORMWATER_LINE_LAYER, handleClick);
      map.off("mouseenter", STORMWATER_LINE_LAYER, handleMouseEnter);
      map.off("mouseleave", STORMWATER_LINE_LAYER, handleMouseLeave);
    };
  }, [stormwater, showStormwater, onSelectSegment]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = () => {
      if (!map.getLayer(STORMWATER_HIGHLIGHT_LAYER)) return;
      map.setFilter(STORMWATER_HIGHLIGHT_LAYER, [
        "==",
        ["get", "segment_id"],
        selectedSegmentId ?? "",
      ]);
    };
    const unsubscribe = onStyled(map, () => styleReady.current, apply);
    return () => {
      unsubscribe();
    };
  }, [selectedSegmentId, stormwater, showStormwater]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const removeRodentLayer = () => {
      if (map.getLayer(RODENT_REPORT_HIGHLIGHT_LAYER)) {
        map.removeLayer(RODENT_REPORT_HIGHLIGHT_LAYER);
      }
      if (map.getLayer(RODENT_REPORT_POINT_LAYER)) map.removeLayer(RODENT_REPORT_POINT_LAYER);
      if (map.getSource(RODENT_REPORT_SOURCE)) map.removeSource(RODENT_REPORT_SOURCE);
    };

    const update = () => {
      const hasPoints = Boolean(rodentReports && rodentReports.features.length > 0);
      container.current?.setAttribute(
        "data-rodent-points",
        hasPoints && showRodentReports ? "visible" : "hidden",
      );
      if (!styleReady.current) return;
      removeRodentLayer();
      if (!rodentReports || rodentReports.features.length === 0) return;
      map.addSource(RODENT_REPORT_SOURCE, {
        type: "geojson",
        data: { type: "FeatureCollection", features: rodentReports.features },
      });
      // Keep report points beneath simulated movement so simulation stays distinct.
      const beforeId = map.getLayer(SIMULATION_LAYER) ? SIMULATION_LAYER : undefined;
      const visibility = showRodentReports ? "visible" : "none";
      map.addLayer(
        {
          id: RODENT_REPORT_POINT_LAYER,
          type: "circle",
          source: RODENT_REPORT_SOURCE,
          layout: { visibility },
          paint: {
            "circle-radius": 4,
            "circle-color": "#be123c",
            "circle-stroke-color": "#7f1d3a",
            "circle-stroke-width": 1,
            "circle-opacity": 0.9,
          },
        },
        beforeId,
      );
      map.addLayer(
        {
          id: RODENT_REPORT_HIGHLIGHT_LAYER,
          type: "circle",
          source: RODENT_REPORT_SOURCE,
          layout: { visibility },
          filter: ["==", ["get", "report_id"], ""],
          paint: {
            "circle-radius": 7,
            "circle-color": "rgba(190,18,60,0.25)",
            "circle-stroke-color": "#7f1d3a",
            "circle-stroke-width": 2,
          },
        },
        beforeId,
      );
    };

    const handleClick = (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature?.properties) {
        onSelectReport(feature.properties as RodentReportProperties);
      }
    };
    const handleMouseEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
    };

    const unsubscribe = onStyled(map, () => styleReady.current, update);
    map.on("click", RODENT_REPORT_POINT_LAYER, handleClick);
    map.on("mouseenter", RODENT_REPORT_POINT_LAYER, handleMouseEnter);
    map.on("mouseleave", RODENT_REPORT_POINT_LAYER, handleMouseLeave);
    return () => {
      unsubscribe();
      map.off("click", RODENT_REPORT_POINT_LAYER, handleClick);
      map.off("mouseenter", RODENT_REPORT_POINT_LAYER, handleMouseEnter);
      map.off("mouseleave", RODENT_REPORT_POINT_LAYER, handleMouseLeave);
    };
  }, [rodentReports, showRodentReports, onSelectReport]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = () => {
      if (!map.getLayer(RODENT_REPORT_HIGHLIGHT_LAYER)) return;
      map.setFilter(RODENT_REPORT_HIGHLIGHT_LAYER, [
        "==",
        ["get", "report_id"],
        selectedReportId ?? "",
      ]);
    };
    const unsubscribe = onStyled(map, () => styleReady.current, apply);
    return () => {
      unsubscribe();
    };
  }, [selectedReportId, rodentReports, showRodentReports]);

  // Request the current viewport on load and after debounced map movement so the
  // dashboard can issue bounded stormwater bbox queries instead of fetching all.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const round = (value: number) => Math.round(value * 1e5) / 1e5;
    const emit = () => {
      const bounds = map.getBounds();
      if (!bounds) return;
      const bbox: StormwaterBbox = [
        round(bounds.getWest()),
        round(bounds.getSouth()),
        round(bounds.getEast()),
        round(bounds.getNorth()),
      ];
      const key = bbox.join(",");
      if (lastBoundsKey.current === key) return;
      lastBoundsKey.current = key;
      onBoundsChange(bbox);
    };
    const schedule = () => {
      if (boundsTimer.current) clearTimeout(boundsTimer.current);
      boundsTimer.current = setTimeout(emit, 300);
    };
    map.on("moveend", schedule);
    const unsubscribe = onStyled(map, () => styleReady.current, emit);
    return () => {
      unsubscribe();
      map.off("moveend", schedule);
      if (boundsTimer.current) clearTimeout(boundsTimer.current);
    };
  }, [onBoundsChange]);

  return <div className="map-frame" role="region" aria-label="互動式 GIS 地圖" ref={container} />;
}
