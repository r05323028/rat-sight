"use client";

import { useEffect, useRef, useState } from "react";
import {
  Map as MapLibreMap,
  NavigationControl,
  setWorkerUrl,
  type ExpressionSpecification,
  type FilterSpecification,
  type MapLayerMouseEvent,
} from "maplibre-gl";
import gsap from "gsap";

import type {
  AdministrativeDistrictGeometry,
  AdministrativeDistrictProperties,
  AdministrativeDistricts,
  CitizenReportAggregates,
  CitizenReportCellProperties,
  SimulationPreview,
  StormwaterBbox,
  StormwaterNetwork,
  StormwaterProperties,
} from "@/lib/api";
import { flowPoints, pointAtFraction, type LngLat } from "@/lib/simulation-geometry";

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
const TRAJECTORY_SOURCE = "ratsight-trajectory-path";
const TRAJECTORY_FULL_LAYER = "ratsight-trajectory-path-upcoming";
const TRAJECTORY_PROGRESS_LAYER = "ratsight-trajectory-path-traversed";
const SIMULATION_STEP_SOURCE = "ratsight-simulated-current-step";
const SIMULATION_STEP_LAYER = "ratsight-simulated-current-step-line";
const WALKER_SOURCE = "ratsight-walker-position";
const WALKER_LAYER = "ratsight-walker-position-point";
const FLOW_SOURCE = "ratsight-route-flow";
const FLOW_LAYER = "ratsight-route-flow-point";
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
const CITIZEN_AGGREGATE_SOURCE = "ratsight-citizen-report-aggregates";
const CITIZEN_AGGREGATE_POINT_LAYER = "ratsight-citizen-report-aggregates-point";
const CITIZEN_AGGREGATE_HIGHLIGHT_LAYER = "ratsight-citizen-report-aggregates-highlight";
const EMPTY_COLLECTION = { type: "FeatureCollection" as const, features: [] };

// Width encodes how often an edge was traversed, never a report count or a
// biological density. Values clamp so a long-tailed walk still stays readable.
const SIMULATION_WIDTH: ExpressionSpecification = [
  "interpolate",
  ["linear"],
  ["get", "visits"],
  1,
  2.5,
  5,
  4,
  25,
  6,
  100,
  8,
];
const FULL_TEAL: ExpressionSpecification = [
  "interpolate",
  ["linear"],
  ["line-progress"],
  0,
  "#0f766e",
  1,
  "#0f766e",
];

// Progressive reveal: each simulated edge paints from its own start toward its
// end. line-progress is per feature, so every edge grows out of the origin side
// without the map needing to rebuild geometry.
function revealGradient(fraction: number): ExpressionSpecification {
  const stop = Math.min(0.9999, Math.max(0.0001, fraction));
  return [
    "interpolate",
    ["linear"],
    ["line-progress"],
    0,
    "#0f766e",
    stop,
    "#0f766e",
    Math.min(1, stop + 0.0001),
    "rgba(15,118,110,0)",
  ];
}

type LineFeature = {
  type: "Feature";
  properties: Record<string, unknown>;
  geometry: { type: "LineString"; coordinates: LngLat[] };
};
type PointFeature = {
  type: "Feature";
  properties: Record<string, unknown>;
  geometry: { type: "Point"; coordinates: LngLat };
};
type Collection<T> = { type: "FeatureCollection"; features: T[] };

type TrajectoryGeometry = {
  coordinates: LngLat[];
  // Index of the last coordinate after each simulated step.
  stepEnds: number[];
};

type PreviewCache = {
  preview: SimulationPreview;
  network: LineFeature[];
  aggregate: LineFeature[];
  trajectories: Map<number, TrajectoryGeometry>;
  schematic: boolean;
};

// Rendering counters are published as a DOM attribute so performance checks can
// read real numbers instead of trusting a visual impression.
type MapTelemetry = {
  renders: number;
  layerBuilds: number;
  sourceBuilds: number;
  setDataCalls: number;
  geojsonBuildMs: number;
  animationFrames: number;
};

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

function prefersReducedMotion(): boolean {
  return (
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

function panDuration(): number {
  return prefersReducedMotion() ? 0 : 500;
}

function lineFeature(coordinates: LngLat[], properties: Record<string, unknown>): LineFeature {
  return { type: "Feature", properties, geometry: { type: "LineString", coordinates } };
}

function pointFeature(coordinates: LngLat, properties: Record<string, unknown>): PointFeature {
  return { type: "Feature", properties, geometry: { type: "Point", coordinates } };
}

function setSourceData(map: MapLibreMap, sourceId: string, data: unknown): boolean {
  const source = map.getSource(sourceId) as { setData?: (value: unknown) => void } | undefined;
  if (!source || typeof source.setData !== "function") return false;
  source.setData(data);
  return true;
}

function setLayerVisibility(map: MapLibreMap, layerId: string, visible: boolean): void {
  if (!map.getLayer(layerId)) return;
  map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
}

function buildPreviewCache(preview: SimulationPreview): PreviewCache {
  const nodes = new Map(preview.nodes.map((node) => [node.id, node.coordinates]));
  const network: LineFeature[] = [];
  const aggregate: LineFeature[] = [];
  for (const edge of preview.edges) {
    if (edge.geometry) {
      network.push(
        lineFeature(edge.geometry.coordinates, {
          edge_id: edge.edge_id,
          source_id: edge.source_id ?? edge.edge_id,
          classification: "REFERENCE",
        }),
      );
    }
    if (!edge.visits || edge.visits <= 0) continue;
    // Endpoint fallback exists only for geometry-less legacy synthetic fixtures.
    const coordinates =
      edge.geometry?.coordinates ??
      (nodes.has(edge.source) && nodes.has(edge.target)
        ? [nodes.get(edge.source)!, nodes.get(edge.target)!]
        : null);
    if (!coordinates || coordinates.length < 2) continue;
    aggregate.push(
      lineFeature(coordinates, {
        edge_id: edge.edge_id,
        // Keep the OSM way id on the simulated overlay so a rendered segment can
        // be traced back to its source geometry rather than only to the walk.
        source_id: edge.source_id ?? edge.edge_id,
        classification: "SIMULATED",
        visits: edge.visits,
        ...(edge.geometry ? {} : { schematic: true }),
      }),
    );
  }
  const trajectories = new Map<number, TrajectoryGeometry>();
  for (const trajectory of preview.trajectories ?? []) {
    const coordinates: LngLat[] = [];
    const stepEnds: number[] = [];
    for (const step of trajectory.edges) {
      const geometry = step.geometry ?? [];
      if (geometry.length < 2) continue;
      if (coordinates.length === 0) coordinates.push(...geometry);
      else coordinates.push(...geometry.slice(1));
      stepEnds.push(coordinates.length - 1);
    }
    if (coordinates.length >= 2) trajectories.set(trajectory.walker_id, { coordinates, stepEnds });
  }
  return {
    preview,
    network,
    aggregate,
    trajectories,
    schematic: preview.edges.length > 0 && preview.edges.every((edge) => !edge.geometry),
  };
}

// One cached geometry per preview. The dashboard keeps the preview object for the
// lifetime of a result, so identity is a safe cache key; a new result always gets
// a new object and therefore new geometry.
type CacheBox = { preview: SimulationPreview | null; cache: PreviewCache | null };

function cacheFor(box: CacheBox, preview: SimulationPreview | null): PreviewCache | null {
  if (!preview) return null;
  if (box.preview !== preview) {
    box.preview = preview;
    box.cache = buildPreviewCache(preview);
  }
  return box.cache;
}

type MapViewProps = {
  preview: SimulationPreview | null;
  // Defaults on; callers may opt out, but the dashboard treats paths as part of the result.
  showSimulatedPaths?: boolean;
  showNetworkReference?: boolean;
  outputMode?: "aggregate" | "trajectory";
  // Presentation only: never interpreted as rodent speed.
  playbackSpeed?: number;
  animationEnabled?: boolean;
  boundaries: AdministrativeDistricts | null;
  showBoundaries: boolean;
  selectedDistrictId: string | null;
  onSelectDistrict: (properties: AdministrativeDistrictProperties) => void;
  stormwater: StormwaterNetwork | null;
  showStormwater: boolean;
  selectedSegmentId: string | null;
  onSelectSegment: (properties: StormwaterProperties) => void;
  citizenAggregates?: CitizenReportAggregates | null;
  // Defaults on; report cells are workflow inputs, not an optional layer toggle.
  showCitizenAggregates?: boolean;
  selectedCitizenCellKey?: string | null;
  onSelectCitizenCell?: (properties: CitizenReportCellProperties) => void;
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
  showSimulatedPaths = true,
  showNetworkReference = false,
  outputMode = "aggregate",
  playbackSpeed = 1,
  animationEnabled = true,
  boundaries,
  showBoundaries,
  selectedDistrictId,
  onSelectDistrict,
  stormwater,
  showStormwater,
  selectedSegmentId,
  onSelectSegment,
  citizenAggregates = null,
  showCitizenAggregates = true,
  selectedCitizenCellKey = null,
  onSelectCitizenCell,
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
  // A state flag, not only the ref, so data effects retry after the map style loads.
  const [styleLoaded, setStyleLoaded] = useState(false);
  const cacheBox = useRef<CacheBox>({ preview: null, cache: null });
  const telemetry = useRef<MapTelemetry>({
    renders: 0,
    layerBuilds: 0,
    sourceBuilds: 0,
    setDataCalls: 0,
    geojsonBuildMs: 0,
    animationFrames: 0,
  });
  // MapLibre event handlers are registered once per style load and read the
  // newest callbacks from this ref, so a parent re-render cannot re-register them.
  const callbacks = useRef({ onSelectTrajectory, onSelectOriginNode });
  const motion = useRef({ playbackSpeed, animationEnabled });

  // Handlers and motion settings are synchronized after commit, never during
  // render. The effect has no dependency list so it runs on every commit, before
  // the map effects that read these refs.
  useEffect(() => {
    callbacks.current = { onSelectTrajectory, onSelectOriginNode };
    motion.current = { playbackSpeed, animationEnabled };
  });

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
    const handleLoad = () => {
      styleReady.current = true;
      setStyleLoaded(true);
      container.current?.setAttribute("data-map-ready", "true");
    };
    map.once("load", handleLoad);
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
      map.off("load", handleLoad);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Publish render/rebuild counters after every render. This is a plain attribute
  // write, not state, so it cannot feed back into the render loop.
  useEffect(() => {
    const current = telemetry.current;
    current.renders += 1;
    container.current?.setAttribute("data-map-perf", JSON.stringify(current));
  });

  // Stable layer identities: created once per style load, then only mutated with
  // setData / setFilter / setLayoutProperty. Playback, selection and React
  // re-renders never remove or recreate these sources or layers.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const create = () => {
      if (!styleReady.current) return;
      const current = telemetry.current;
      if (!map.getSource(NETWORK_REFERENCE_SOURCE)) {
        map.addSource(NETWORK_REFERENCE_SOURCE, { type: "geojson", data: EMPTY_COLLECTION });
        current.sourceBuilds += 1;
      }
      if (!map.getLayer(NETWORK_REFERENCE_LAYER)) {
        map.addLayer({
          id: NETWORK_REFERENCE_LAYER,
          type: "line",
          source: NETWORK_REFERENCE_SOURCE,
          layout: {
            "line-cap": "round",
            "line-join": "round",
            visibility: showNetworkReference ? "visible" : "none",
          },
          paint: { "line-color": "#64748b", "line-width": 1.75, "line-opacity": 0.45 },
        });
        current.layerBuilds += 1;
      }
      if (!map.getSource(SIMULATION_SOURCE)) {
        // lineMetrics is required by line-gradient, which drives the route reveal.
        map.addSource(SIMULATION_SOURCE, {
          type: "geojson",
          data: EMPTY_COLLECTION,
          lineMetrics: true,
        });
        current.sourceBuilds += 1;
      }
      if (!map.getLayer(SIMULATION_LAYER)) {
        map.addLayer({
          id: SIMULATION_LAYER,
          type: "line",
          source: SIMULATION_SOURCE,
          filter: SCHEMATIC_EXCLUDED,
          layout: { "line-cap": "round", "line-join": "round", visibility: "none" },
          paint: {
            "line-color": "#0f766e",
            "line-width": SIMULATION_WIDTH,
            "line-opacity": 0.82,
            "line-gradient": FULL_TEAL,
          },
        });
        current.layerBuilds += 1;
      }
      if (!map.getLayer(SIMULATION_SCHEMATIC_LAYER)) {
        map.addLayer({
          id: SIMULATION_SCHEMATIC_LAYER,
          type: "line",
          source: SIMULATION_SOURCE,
          filter: SCHEMATIC_ONLY,
          layout: { "line-cap": "butt", "line-join": "round", visibility: "none" },
          paint: {
            "line-color": "#0f766e",
            "line-width": 2,
            "line-opacity": 0.75,
            "line-dasharray": [1.5, 1.5],
          },
        });
        current.layerBuilds += 1;
      }
      if (!map.getLayer(SIMULATION_HIT_LAYER)) {
        map.addLayer({
          id: SIMULATION_HIT_LAYER,
          type: "line",
          source: SIMULATION_SOURCE,
          layout: { "line-cap": "round", "line-join": "round", visibility: "none" },
          paint: { "line-color": "#0f766e", "line-opacity": 0, "line-width": 16 },
        });
        current.layerBuilds += 1;
      }
      if (!map.getSource(TRAJECTORY_SOURCE)) {
        map.addSource(TRAJECTORY_SOURCE, { type: "geojson", data: EMPTY_COLLECTION });
        current.sourceBuilds += 1;
      }
      if (!map.getLayer(TRAJECTORY_FULL_LAYER)) {
        map.addLayer({
          id: TRAJECTORY_FULL_LAYER,
          type: "line",
          source: TRAJECTORY_SOURCE,
          layout: { "line-cap": "round", "line-join": "round", visibility: "none" },
          paint: { "line-color": "#94a3b8", "line-width": 2, "line-opacity": 0.6 },
        });
        current.layerBuilds += 1;
      }
      if (!map.getLayer(TRAJECTORY_PROGRESS_LAYER)) {
        map.addLayer({
          id: TRAJECTORY_PROGRESS_LAYER,
          type: "line",
          source: TRAJECTORY_SOURCE,
          layout: { "line-cap": "round", "line-join": "round", visibility: "none" },
          paint: { "line-color": "#0f766e", "line-width": 4.5, "line-opacity": 0.95 },
        });
        current.layerBuilds += 1;
      }
      if (!map.getSource(SIMULATION_STEP_SOURCE)) {
        map.addSource(SIMULATION_STEP_SOURCE, { type: "geojson", data: EMPTY_COLLECTION });
        current.sourceBuilds += 1;
      }
      if (!map.getLayer(SIMULATION_STEP_LAYER)) {
        map.addLayer({
          id: SIMULATION_STEP_LAYER,
          type: "line",
          source: SIMULATION_STEP_SOURCE,
          layout: { "line-cap": "round", "line-join": "round", visibility: "none" },
          paint: { "line-color": "#b91c1c", "line-width": 5, "line-opacity": 0.95 },
        });
        current.layerBuilds += 1;
      }
      if (!map.getSource(WALKER_SOURCE)) {
        map.addSource(WALKER_SOURCE, { type: "geojson", data: EMPTY_COLLECTION });
        current.sourceBuilds += 1;
      }
      if (!map.getLayer(WALKER_LAYER)) {
        map.addLayer({
          id: WALKER_LAYER,
          type: "circle",
          source: WALKER_SOURCE,
          layout: { visibility: "none" },
          paint: {
            "circle-radius": 6,
            "circle-color": "#ffffff",
            "circle-stroke-color": "#b91c1c",
            "circle-stroke-width": 3,
          },
        });
        current.layerBuilds += 1;
      }
      if (!map.getSource(FLOW_SOURCE)) {
        map.addSource(FLOW_SOURCE, { type: "geojson", data: EMPTY_COLLECTION });
        current.sourceBuilds += 1;
      }
      if (!map.getLayer(FLOW_LAYER)) {
        map.addLayer({
          id: FLOW_LAYER,
          type: "circle",
          source: FLOW_SOURCE,
          layout: { visibility: "none" },
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 12, 1.8, 16, 3.2],
            "circle-color": "#0f766e",
            "circle-opacity": 0.85,
          },
        });
        current.layerBuilds += 1;
      }
      if (!map.getSource(ORIGIN_SOURCE)) {
        map.addSource(ORIGIN_SOURCE, { type: "geojson", data: EMPTY_COLLECTION });
        current.sourceBuilds += 1;
      }
      if (!map.getLayer(ORIGIN_LAYER)) {
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
        current.layerBuilds += 1;
      }
      if (!map.getLayer(ORIGIN_SELECTED_LAYER)) {
        map.addLayer({
          id: ORIGIN_SELECTED_LAYER,
          type: "circle",
          source: ORIGIN_SOURCE,
          filter: ["==", ["get", "node_id"], ""],
          paint: {
            "circle-radius": 9,
            "circle-color": "#b91c1c",
            "circle-opacity": 0.9,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
          },
        });
        current.layerBuilds += 1;
      }
      container.current?.setAttribute("data-map-perf", JSON.stringify(current));
    };

    const handleTrajectoryClick = (event: MapLayerMouseEvent) => {
      const trajectoryId = event.features?.[0]?.properties?.trajectory_id;
      if (typeof trajectoryId === "number") callbacks.current.onSelectTrajectory?.(trajectoryId);
    };
    // Origin picks are limited to nodes the API returned, so no coordinate snapping happens here.
    const handleOriginClick = (event: MapLayerMouseEvent) => {
      const nodeId = event.features?.[0]?.properties?.node_id;
      if (typeof nodeId === "string") callbacks.current.onSelectOriginNode?.(nodeId);
    };
    const handleMouseEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
    };

    const unsubscribe = onStyled(map, () => styleReady.current, create);
    map.on("click", SIMULATION_HIT_LAYER, handleTrajectoryClick);
    map.on("mouseenter", SIMULATION_HIT_LAYER, handleMouseEnter);
    map.on("mouseleave", SIMULATION_HIT_LAYER, handleMouseLeave);
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
  }, [styleLoaded, showNetworkReference]);

  // New simulation data replaces source content. It never removes a layer, and it
  // runs once per result rather than once per playback tick.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const cache = cacheFor(cacheBox.current, preview);
    const apply = () => {
      if (!styleReady.current) return;
      const started = performance.now();
      setSourceData(map, NETWORK_REFERENCE_SOURCE, {
        type: "FeatureCollection",
        features: cache?.network ?? [],
      } satisfies Collection<LineFeature>);
      setSourceData(map, SIMULATION_SOURCE, {
        type: "FeatureCollection",
        features: cache?.aggregate ?? [],
      } satisfies Collection<LineFeature>);
      telemetry.current.setDataCalls += 2;
      telemetry.current.geojsonBuildMs += performance.now() - started;
    };
    const unsubscribe = onStyled(map, () => styleReady.current, apply);
    return unsubscribe;
  }, [preview]);

  // Camera fit is keyed on the preview identity only, so panning does not re-fit
  // and playback does not move the camera.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !preview || fittedPreviewRef.current === preview) return;
    const bounds = coordinateBounds([
      preview.nodes.map((node) => node.coordinates),
      preview.edges.map((edge) => edge.geometry?.coordinates ?? null),
    ]);
    if (!bounds) return;
    fittedPreviewRef.current = preview;
    map.fitBounds(bounds, { padding: 56, duration: panDuration() });
  }, [preview]);

  // Aggregate route reveal. GSAP drives a plain object; only MapLibre paint state
  // changes per frame, never React state.
  useEffect(() => {
    const map = mapRef.current;
    const cache = cacheFor(cacheBox.current, preview);
    if (!map || !cache) return;
    let tween: gsap.core.Tween | null = null;
    const apply = () => {
      if (!map.getLayer(SIMULATION_LAYER)) return;
      const animate = motion.current.animationEnabled && !prefersReducedMotion();
      if (!animate) {
        map.setPaintProperty(SIMULATION_LAYER, "line-gradient", FULL_TEAL);
        map.setPaintProperty(SIMULATION_SCHEMATIC_LAYER, "line-opacity", 0.75);
        return;
      }
      const state = { progress: 0 };
      map.setPaintProperty(SIMULATION_LAYER, "line-gradient", revealGradient(0));
      map.setPaintProperty(SIMULATION_SCHEMATIC_LAYER, "line-opacity", 0.15);
      tween = gsap.to(state, {
        progress: 1,
        duration: 1.1 / Math.max(0.5, motion.current.playbackSpeed),
        ease: "power1.inOut",
        onUpdate: () => {
          telemetry.current.animationFrames += 1;
          map.setPaintProperty(SIMULATION_LAYER, "line-gradient", revealGradient(state.progress));
          map.setPaintProperty(
            SIMULATION_SCHEMATIC_LAYER,
            "line-opacity",
            0.15 + 0.6 * state.progress,
          );
        },
        onComplete: () => {
          map.setPaintProperty(SIMULATION_LAYER, "line-gradient", FULL_TEAL);
        },
      });
    };
    const unsubscribe = onStyled(map, () => styleReady.current, apply);
    return () => {
      unsubscribe();
      tween?.kill();
    };
  }, [preview]);

  // Selection, mode and playback: data + visibility only. The only tween here is
  // the walker's movement across the newly traversed segment.
  useEffect(() => {
    const map = mapRef.current;
    const cache = cacheFor(cacheBox.current, preview);
    if (!map) return;
    let walkerTween: gsap.core.Tween | null = null;
    let walkerAnimating = false;
    const apply = () => {
      walkerAnimating = false;
      if (!styleReady.current) return;
      const aggregateVisible = outputMode === "aggregate" && showSimulatedPaths;
      const trajectoryVisible = outputMode === "trajectory" && showSimulatedPaths;
      setLayerVisibility(map, SIMULATION_LAYER, aggregateVisible && !cache?.schematic);
      setLayerVisibility(
        map,
        SIMULATION_SCHEMATIC_LAYER,
        aggregateVisible && Boolean(cache?.schematic),
      );
      setLayerVisibility(map, SIMULATION_HIT_LAYER, aggregateVisible);
      setLayerVisibility(map, FLOW_LAYER, aggregateVisible && motion.current.animationEnabled);
      setLayerVisibility(map, TRAJECTORY_FULL_LAYER, trajectoryVisible);
      setLayerVisibility(map, TRAJECTORY_PROGRESS_LAYER, trajectoryVisible);
      setLayerVisibility(map, SIMULATION_STEP_LAYER, trajectoryVisible);
      setLayerVisibility(map, WALKER_LAYER, trajectoryVisible);

      if (!cache) {
        setSourceData(map, TRAJECTORY_SOURCE, EMPTY_COLLECTION);
        setSourceData(map, SIMULATION_STEP_SOURCE, EMPTY_COLLECTION);
        setSourceData(map, WALKER_SOURCE, EMPTY_COLLECTION);
        setSourceData(map, FLOW_SOURCE, EMPTY_COLLECTION);
        return;
      }
      // Flow markers ride on the returned directed edges, so a two-way street is
      // shown in both directions instead of a false one-way current.
      const flowFeatures = motion.current.animationEnabled
        ? cache.aggregate.slice(0, 24).flatMap((feature) =>
            flowPoints(feature.geometry.coordinates, 2, 0).map((coordinates) =>
              pointFeature(coordinates, {
                classification: "SIMULATED",
                edge_id: feature.properties.edge_id,
              }),
            ),
          )
        : [];
      if (!aggregateVisible || flowFeatures.length === 0) {
        setSourceData(map, FLOW_SOURCE, EMPTY_COLLECTION);
      }

      const selected =
        selectedTrajectoryId === null
          ? [...cache.trajectories.entries()]
          : [...cache.trajectories.entries()].filter(([id]) => id === selectedTrajectoryId);
      const fullFeatures = selected.map(([id, geometry]) =>
        lineFeature(geometry.coordinates, { trajectory_id: id, classification: "SIMULATED" }),
      );
      const clampedStep =
        activeStep === null
          ? null
          : Math.max(
              0,
              Math.min(
                activeStep,
                Math.max(...selected.map(([, geometry]) => geometry.stepEnds.length), 0),
              ),
            );
      const progressFeatures = trajectoryVisible
        ? selected.flatMap(([id, geometry]) => {
            if (clampedStep === null) return [];
            if (clampedStep === 0) return [];
            const end = geometry.stepEnds[clampedStep - 1];
            if (end === undefined) return [];
            return [
              lineFeature(geometry.coordinates.slice(0, end + 1), {
                trajectory_id: id,
                classification: "SIMULATED",
                step: clampedStep,
              }),
            ];
          })
        : [];
      const stepFeatures =
        trajectoryVisible && clampedStep !== null && clampedStep > 0
          ? selected.flatMap(([id, geometry]) => {
              const start = clampedStep >= 2 ? geometry.stepEnds[clampedStep - 2] : 0;
              const end = geometry.stepEnds[clampedStep - 1];
              if (end === undefined) return [];
              return [
                lineFeature(geometry.coordinates.slice(start, end + 1), {
                  trajectory_id: id,
                  classification: "SIMULATED",
                }),
              ];
            })
          : [];
      setSourceData(map, TRAJECTORY_SOURCE, {
        type: "FeatureCollection",
        features: [...fullFeatures, ...progressFeatures],
      } satisfies Collection<LineFeature>);
      setSourceData(map, SIMULATION_STEP_SOURCE, {
        type: "FeatureCollection",
        features: stepFeatures,
      } satisfies Collection<LineFeature>);
      telemetry.current.setDataCalls += 2;

      const walker = selected[0];
      let walkerCoordinates: LngLat | null = null;
      if (walker && clampedStep !== null) {
        const [, geometry] = walker;
        const end = clampedStep > 0 ? geometry.stepEnds[clampedStep - 1] : 0;
        walkerCoordinates = geometry.coordinates[end] ?? geometry.coordinates[0] ?? null;
        // Animate only one forward step; seeking or changing walker jumps directly
        // so the marker never appears to travel backwards through time.
        const previous = clampedStep >= 2 ? geometry.stepEnds[clampedStep - 2] : 0;
        const segment = geometry.coordinates.slice(previous, end + 1);
        const start = segment.length >= 2 ? pointAtFraction(segment, 0) : null;
        if (
          start &&
          motion.current.animationEnabled &&
          !prefersReducedMotion() &&
          clampedStep > 1 &&
          end > previous
        ) {
          walkerAnimating = true;
          // Sit on the segment start before the first tween frame, then follow the
          // returned polyline instead of a straight chord between endpoints.
          setSourceData(map, WALKER_SOURCE, {
            type: "FeatureCollection",
            features: [pointFeature(start, { classification: "SIMULATED" })],
          } satisfies Collection<PointFeature>);
          const state = { fraction: 0 };
          walkerTween = gsap.to(state, {
            fraction: 1,
            duration: 0.32 / Math.max(0.5, motion.current.playbackSpeed),
            ease: "none",
            onUpdate: () => {
              const point = pointAtFraction(segment, state.fraction);
              if (point) {
                setSourceData(map, WALKER_SOURCE, {
                  type: "FeatureCollection",
                  features: [pointFeature(point, { classification: "SIMULATED" })],
                } satisfies Collection<PointFeature>);
              }
            },
          });
        }
      }
      setLayerVisibility(map, WALKER_LAYER, trajectoryVisible && Boolean(walkerCoordinates));
      // A running tween owns the marker position; writing the destination here
      // would make the first animated frame snap to the end of the segment.
      if (!walkerAnimating) {
        setSourceData(map, WALKER_SOURCE, {
          type: "FeatureCollection",
          features: walkerCoordinates
            ? [pointFeature(walkerCoordinates, { classification: "SIMULATED" })]
            : [],
        } satisfies Collection<PointFeature>);
      }
      if (flowFeatures.length > 0) {
        setSourceData(map, FLOW_SOURCE, {
          type: "FeatureCollection",
          features: flowFeatures,
        } satisfies Collection<PointFeature>);
      }
    };
    const unsubscribe = onStyled(map, () => styleReady.current, apply);
    return () => {
      unsubscribe();
      walkerTween?.kill();
    };
  }, [preview, outputMode, showSimulatedPaths, activeStep, selectedTrajectoryId]);

  // Lightweight layer toggles never rebuild sources or layers.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    // Simulation layers are owned by the mode/playback effect below; this effect
    // only handles the independent reference toggle.
    onStyled(
      map,
      () => styleReady.current,
      () => {
        setLayerVisibility(map, NETWORK_REFERENCE_LAYER, showNetworkReference);
      },
    );
  }, [showNetworkReference, mapRef]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = () => {
      if (!styleReady.current) return;
      setSourceData(map, ORIGIN_SOURCE, {
        type: "FeatureCollection",
        features: originNodes.map((node) =>
          pointFeature(node.coordinates, { node_id: node.id, classification: "SIMULATED" }),
        ),
      });
      if (map.getLayer(ORIGIN_SELECTED_LAYER)) {
        map.setFilter(ORIGIN_SELECTED_LAYER, [
          "==",
          ["get", "node_id"],
          selectedOriginNodeId ?? "",
        ]);
      }
    };
    const unsubscribe = onStyled(map, () => styleReady.current, apply);
    return unsubscribe;
  }, [originNodes, selectedOriginNodeId]);

  // Continuous flow markers. Paused while the user drags the map, in a hidden tab
  // and under reduced-motion, so decoration never competes with navigation.
  useEffect(() => {
    const map = mapRef.current;
    const cache = cacheFor(cacheBox.current, preview);
    if (!map) return;
    const clearFlow = () =>
      onStyled(
        map,
        () => styleReady.current,
        () => {
          setLayerVisibility(map, FLOW_LAYER, false);
          setSourceData(map, FLOW_SOURCE, EMPTY_COLLECTION);
        },
      );
    // Turning the effect off (or leaving aggregate mode) must remove the last
    // painted markers instead of freezing them on the map.
    if (!cache) return clearFlow();
    if (
      !animationEnabled ||
      prefersReducedMotion() ||
      outputMode !== "aggregate" ||
      !showSimulatedPaths
    ) {
      return clearFlow();
    }
    const edges = cache.aggregate.slice(0, 24);
    if (edges.length === 0) return;
    const showFlow = onStyled(
      map,
      () => styleReady.current,
      () => {
        setLayerVisibility(map, FLOW_LAYER, true);
      },
    );
    const state = { phase: 0 };
    const tween = gsap.to(state, {
      phase: 1,
      duration: 7,
      ease: "none",
      repeat: -1,
      onUpdate: () => {
        telemetry.current.animationFrames += 1;
        const features = edges.flatMap((feature) =>
          flowPoints(feature.geometry.coordinates, 2, state.phase).map((coordinates) =>
            pointFeature(coordinates, {
              classification: "SIMULATED",
              edge_id: feature.properties.edge_id,
            }),
          ),
        );
        setSourceData(map, FLOW_SOURCE, { type: "FeatureCollection", features });
      },
    });
    const pause = () => tween.pause();
    const resume = () => tween.resume();
    const handleVisibility = () => {
      if (document.hidden) tween.pause();
      else tween.resume();
    };
    map.on("dragstart", pause);
    map.on("dragend", resume);
    document.addEventListener("visibilitychange", handleVisibility);
    return () => {
      showFlow();
      tween.kill();
      map.off("dragstart", pause);
      map.off("dragend", resume);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [preview, outputMode, showSimulatedPaths, animationEnabled]);

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

    const removeCitizenAggregateLayers = () => {
      if (map.getLayer(CITIZEN_AGGREGATE_HIGHLIGHT_LAYER))
        map.removeLayer(CITIZEN_AGGREGATE_HIGHLIGHT_LAYER);
      if (map.getLayer(CITIZEN_AGGREGATE_POINT_LAYER))
        map.removeLayer(CITIZEN_AGGREGATE_POINT_LAYER);
      if (map.getSource(CITIZEN_AGGREGATE_SOURCE)) map.removeSource(CITIZEN_AGGREGATE_SOURCE);
    };

    const update = () => {
      const hasCells = Boolean(citizenAggregates && citizenAggregates.features.length > 0);
      container.current?.setAttribute(
        "data-citizen-aggregates",
        hasCells && showCitizenAggregates ? "visible" : "hidden",
      );
      if (!styleReady.current) return;
      removeCitizenAggregateLayers();
      if (!citizenAggregates || citizenAggregates.features.length === 0) return;
      const markerFeatures = citizenAggregates.features.map((feature) => {
        const ring = feature.geometry.coordinates[0] ?? [];
        const points = ring.slice(0, -1);
        const center = points.reduce(
          ([longitude, latitude], [pointLongitude, pointLatitude]) => [
            longitude + pointLongitude,
            latitude + pointLatitude,
          ],
          [0, 0],
        );
        const count = points.length || 1;
        return {
          type: "Feature" as const,
          id: feature.id,
          geometry: {
            type: "Point" as const,
            coordinates: [center[0] / count, center[1] / count],
          },
          properties: {
            ...feature.properties,
            feature_key: `${feature.properties.cell_id}:${feature.properties.month}:${feature.properties.report_type}`,
          },
        };
      });
      map.addSource(CITIZEN_AGGREGATE_SOURCE, {
        type: "geojson",
        data: { type: "FeatureCollection", features: markerFeatures },
      });
      const beforeId = map.getLayer(SIMULATION_LAYER) ? SIMULATION_LAYER : undefined;
      const visibility = showCitizenAggregates ? "visible" : "none";
      map.addLayer(
        {
          id: CITIZEN_AGGREGATE_POINT_LAYER,
          type: "circle",
          source: CITIZEN_AGGREGATE_SOURCE,
          layout: { visibility },
          paint: {
            // Citizen aggregates stay red; isolated synthetic fixtures use slate so
            // they cannot be mistaken for published reports.
            "circle-color": [
              "case",
              ["==", ["get", "data_class"], "SYNTHETIC_AGGREGATE_FIXTURE"],
              "#5b6b7a",
              "#a3243c",
            ],
            "circle-radius": 7,
            "circle-stroke-color": "#fff",
            "circle-stroke-width": 2,
          },
        },
        beforeId,
      );
      map.addLayer(
        {
          id: CITIZEN_AGGREGATE_HIGHLIGHT_LAYER,
          type: "circle",
          source: CITIZEN_AGGREGATE_SOURCE,
          layout: { visibility },
          filter: ["==", ["get", "feature_key"], ""],
          paint: {
            "circle-color": [
              "case",
              ["==", ["get", "data_class"], "SYNTHETIC_AGGREGATE_FIXTURE"],
              "#5b6b7a",
              "#a3243c",
            ],
            "circle-opacity": 0.18,
            "circle-radius": 12,
            "circle-stroke-color": [
              "case",
              ["==", ["get", "data_class"], "SYNTHETIC_AGGREGATE_FIXTURE"],
              "#5b6b7a",
              "#a3243c",
            ],
            "circle-stroke-width": 2,
          },
        },
        beforeId,
      );
    };

    const unsubscribe = onStyled(map, () => styleReady.current, update);
    return () => {
      unsubscribe();
    };
  }, [citizenAggregates, showCitizenAggregates, styleLoaded]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = () => {
      if (!map.getLayer(CITIZEN_AGGREGATE_HIGHLIGHT_LAYER)) return;
      map.setFilter(CITIZEN_AGGREGATE_HIGHLIGHT_LAYER, [
        "==",
        ["get", "feature_key"],
        selectedCitizenCellKey ?? "",
      ]);
    };
    const unsubscribe = onStyled(map, () => styleReady.current, apply);
    return () => {
      unsubscribe();
    };
  }, [citizenAggregates, selectedCitizenCellKey, showCitizenAggregates]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !onSelectCitizenCell) return;
    const handleClick = (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (!feature?.properties) return;
      const cell = citizenAggregates?.features.find(
        (item) =>
          item.properties.cell_id === String(feature.properties.cell_id) &&
          item.properties.month === String(feature.properties.month) &&
          item.properties.report_type === String(feature.properties.report_type),
      );
      if (cell) onSelectCitizenCell(cell.properties);
    };
    const showPointer = () => {
      if (container.current) container.current.style.cursor = "pointer";
    };
    const hidePointer = () => {
      if (container.current) container.current.style.cursor = "";
    };
    map.on("click", CITIZEN_AGGREGATE_POINT_LAYER, handleClick);
    map.on("mouseenter", CITIZEN_AGGREGATE_POINT_LAYER, showPointer);
    map.on("mouseleave", CITIZEN_AGGREGATE_POINT_LAYER, hidePointer);
    return () => {
      map.off("click", CITIZEN_AGGREGATE_POINT_LAYER, handleClick);
      map.off("mouseenter", CITIZEN_AGGREGATE_POINT_LAYER, showPointer);
      map.off("mouseleave", CITIZEN_AGGREGATE_POINT_LAYER, hidePointer);
      hidePointer();
    };
  }, [citizenAggregates, onSelectCitizenCell]);

  // Request the current viewport on load and after debounced map movement so the
  // dashboard can issue bounded stormwater bbox queries instead of fetching all.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const round = (value: number) => Math.round(value * 1e5) / 1e5;
    const emit = () => {
      const bounds = map.getBounds();
      if (!bounds) return;
      const center = map.getCenter();
      container.current?.setAttribute(
        "data-map-center",
        `${round(center.lng)},${round(center.lat)}`,
      );
      container.current?.setAttribute(
        "data-map-zoom",
        String(Math.round(map.getZoom() * 1000) / 1000),
      );
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
