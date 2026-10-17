"use client";

import { useEffect, useRef } from "react";
import {
  Map as MapLibreMap,
  NavigationControl,
  setWorkerUrl,
  type MapLayerMouseEvent,
} from "maplibre-gl";

import type {
  AdministrativeDistrictProperties,
  AdministrativeDistricts,
  RodentReportProperties,
  RodentReports,
  SimulationPreview,
  StormwaterBbox,
  StormwaterNetwork,
  StormwaterProperties,
} from "@/lib/api";

setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");

const STYLE_URL =
  process.env.NEXT_PUBLIC_MAP_STYLE_URL ??
  "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";
const SIMULATION_SOURCE = "ratsight-simulated-edges";
const SIMULATION_LAYER = "ratsight-simulated-edges-line";
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

type MapViewProps = {
  preview: SimulationPreview | null;
  showSimulatedPaths: boolean;
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
  onBoundsChange: (bbox: StormwaterBbox) => void;
};

export function MapView({
  preview,
  showSimulatedPaths,
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
  onBoundsChange,
}: MapViewProps) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const lastBoundsKey = useRef<string | null>(null);
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
    map.once("load", () => {
      container.current?.setAttribute("data-map-ready", "true");
    });
    map.addControl(new NavigationControl(), "top-right");
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      if (!map.isStyleLoaded()) return;
      if (map.getLayer(SIMULATION_LAYER)) map.removeLayer(SIMULATION_LAYER);
      if (map.getSource(SIMULATION_SOURCE)) map.removeSource(SIMULATION_SOURCE);
      if (!preview) return;
      const nodes = new Map(preview.nodes.map((node) => [node.id, node.coordinates]));
      const features = preview.edges
        .filter((edge) => edge.visits > 0)
        .flatMap((edge) => {
          const start = nodes.get(edge.source);
          const end = nodes.get(edge.target);
          return start && end
            ? [
                {
                  type: "Feature" as const,
                  properties: { visits: edge.visits, classification: "SIMULATED" },
                  geometry: { type: "LineString" as const, coordinates: [start, end] },
                },
              ]
            : [];
        });
      map.addSource(SIMULATION_SOURCE, {
        type: "geojson",
        data: { type: "FeatureCollection", features },
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
        paint: { "line-color": "#0f766e", "line-width": 3, "line-opacity": 0.8 },
      });
    };
    map.on("load", update);
    if (map.isStyleLoaded()) update();
    return () => {
      map.off("load", update);
    };
  }, [preview, showSimulatedPaths]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const removeBoundaryLayers = () => {
      if (map.getLayer(BOUNDARY_HIGHLIGHT_LAYER)) map.removeLayer(BOUNDARY_HIGHLIGHT_LAYER);
      if (map.getLayer(BOUNDARY_OUTLINE_LAYER)) map.removeLayer(BOUNDARY_OUTLINE_LAYER);
      if (map.getLayer(BOUNDARY_FILL_LAYER)) map.removeLayer(BOUNDARY_FILL_LAYER);
      if (map.getSource(BOUNDARY_SOURCE)) map.removeSource(BOUNDARY_SOURCE);
    };

    const update = () => {
      if (!map.isStyleLoaded()) return;
      removeBoundaryLayers();
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

    map.on("load", update);
    map.on("click", BOUNDARY_FILL_LAYER, handleClick);
    map.on("mouseenter", BOUNDARY_FILL_LAYER, handleMouseEnter);
    map.on("mouseleave", BOUNDARY_FILL_LAYER, handleMouseLeave);
    if (map.isStyleLoaded()) update();
    return () => {
      map.off("load", update);
      map.off("click", BOUNDARY_FILL_LAYER, handleClick);
      map.off("mouseenter", BOUNDARY_FILL_LAYER, handleMouseEnter);
      map.off("mouseleave", BOUNDARY_FILL_LAYER, handleMouseLeave);
    };
  }, [boundaries, showBoundaries, onSelectDistrict]);

  // Keep the map highlight synchronized with the selection made from the
  // keyboard-accessible district list or from a map click.
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
    };
    map.on("load", apply);
    if (map.isStyleLoaded()) apply();
    return () => {
      map.off("load", apply);
    };
  }, [selectedDistrictId, boundaries, showBoundaries]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const removeStormwaterLayers = () => {
      if (map.getLayer(STORMWATER_HIGHLIGHT_LAYER)) map.removeLayer(STORMWATER_HIGHLIGHT_LAYER);
      if (map.getLayer(STORMWATER_LINE_LAYER)) map.removeLayer(STORMWATER_LINE_LAYER);
      if (map.getSource(STORMWATER_SOURCE)) map.removeSource(STORMWATER_SOURCE);
    };

    const update = () => {
      if (!map.isStyleLoaded()) return;
      removeStormwaterLayers();
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

    map.on("load", update);
    map.on("click", STORMWATER_LINE_LAYER, handleClick);
    map.on("mouseenter", STORMWATER_LINE_LAYER, handleMouseEnter);
    map.on("mouseleave", STORMWATER_LINE_LAYER, handleMouseLeave);
    if (map.isStyleLoaded()) update();
    return () => {
      map.off("load", update);
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
    map.on("load", apply);
    if (map.isStyleLoaded()) apply();
    return () => {
      map.off("load", apply);
    };
  }, [selectedSegmentId, stormwater, showStormwater]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const removeRodentLayers = () => {
      if (map.getLayer(RODENT_REPORT_HIGHLIGHT_LAYER)) {
        map.removeLayer(RODENT_REPORT_HIGHLIGHT_LAYER);
      }
      if (map.getLayer(RODENT_REPORT_POINT_LAYER)) map.removeLayer(RODENT_REPORT_POINT_LAYER);
      if (map.getSource(RODENT_REPORT_SOURCE)) map.removeSource(RODENT_REPORT_SOURCE);
    };

    const update = () => {
      if (!map.isStyleLoaded()) return;
      removeRodentLayers();
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

    map.on("load", update);
    map.on("click", RODENT_REPORT_POINT_LAYER, handleClick);
    map.on("mouseenter", RODENT_REPORT_POINT_LAYER, handleMouseEnter);
    map.on("mouseleave", RODENT_REPORT_POINT_LAYER, handleMouseLeave);
    if (map.isStyleLoaded()) update();
    return () => {
      map.off("load", update);
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
    map.on("load", apply);
    if (map.isStyleLoaded()) apply();
    return () => {
      map.off("load", apply);
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
    map.on("load", emit);
    map.on("moveend", schedule);
    if (map.isStyleLoaded()) emit();
    return () => {
      map.off("load", emit);
      map.off("moveend", schedule);
      if (boundsTimer.current) clearTimeout(boundsTimer.current);
    };
  }, [onBoundsChange]);

  return (
    <div className="map-frame" role="region" aria-label="Interactive GIS map" ref={container} />
  );
}
