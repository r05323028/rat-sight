"use client";

import { useEffect, useRef } from "react";
import { Map as MapLibreMap, NavigationControl, setWorkerUrl } from "maplibre-gl";

import type { SimulationPreview } from "@/lib/api";

setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");

const STYLE_URL =
  process.env.NEXT_PUBLIC_MAP_STYLE_URL ??
  "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";
const SIMULATION_SOURCE = "ratsight-simulated-edges";
const SIMULATION_LAYER = "ratsight-simulated-edges-line";

type MapViewProps = { preview: SimulationPreview | null; showSimulatedPaths: boolean };

export function MapView({ preview, showSimulatedPaths }: MapViewProps) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);

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
      const features = preview.edges.flatMap((edge) => {
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

  return (
    <div className="map-frame" role="region" aria-label="Interactive GIS map" ref={container} />
  );
}
