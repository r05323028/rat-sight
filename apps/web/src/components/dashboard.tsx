"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { MapView } from "@/components/map-view";
import { Button } from "@/components/ui/button";
import {
  fetchAdministrativeDistricts,
  fetchLayers,
  fetchStormwaterPipelines,
  isStormwaterBboxTooBroad,
  requestPreview,
  type AdministrativeDistrictProperties,
  type Layer,
  type SimulationPreview,
  type StormwaterBbox,
  type StormwaterProperties,
} from "@/lib/api";

const DEFAULT_LAYERS: Layer[] = [
  ["rodent_observations", "Rodent observations"],
  ["sewer_networks", "Sewer networks"],
  ["surface_corridors", "Surface movement corridors"],
  ["human_activity", "Human activity"],
  ["environmental_conditions", "Environmental conditions"],
  ["simulated_paths", "Simulated movement paths"],
].map(([id, label]) => ({
  id,
  label,
  available: false,
  classification: id === "simulated_paths" ? "SIMULATED" : null,
  message: id === "simulated_paths" ? "Available after a synthetic preview." : "No dataset loaded.",
}));

const LAYER_GLYPHS: Record<string, string> = {
  rodent_observations: "●",
  sewer_networks: "━",
  surface_corridors: "╱",
  human_activity: "◌",
  environmental_conditions: "◍",
  simulated_paths: "⌁",
};

function isSafeExternalUrl(value: string): boolean {
  return /^https?:\/\//i.test(value);
}

// Approximates the initial map center until MapView reports the real viewport bbox.
const DEFAULT_STORMWATER_BBOX: StormwaterBbox = [121.5, 24.98, 121.63, 25.09];
const MAX_VISIBLE_PIPELINE_LIST_ITEMS = 100;

const STORMWATER_ATTRIBUTE_LABELS: [keyof StormwaterProperties, string][] = [
  ["segment_id", "Segment ID"],
  ["category_code", "Category code"],
  ["pipe_number", "Pipe number"],
  ["start_node_id", "Start node (publisher attribute)"],
  ["end_node_id", "End node (publisher attribute)"],
  ["managing_unit", "Managing unit"],
  ["work_category", "Work category"],
  ["installation_date", "Installation date"],
  ["dimension_unit", "Dimension unit"],
  ["diameter_width", "Diameter / width"],
  ["diameter_height", "Diameter / height"],
  ["conduit_count", "Conduit count"],
  ["material", "Material"],
  ["start_burial_depth", "Start burial depth"],
  ["end_burial_depth", "End burial depth"],
  ["length", "Length"],
  ["pipe_type", "Pipe type"],
  ["use_status", "Use status"],
  ["data_status", "Data status"],
  ["notes", "Notes"],
];

function zHandlingText(zHandling: "dropped" | "retained" | "not_present"): string {
  if (zHandling === "dropped") return "Source Z dropped — no documented vertical CRS";
  if (zHandling === "retained") return "Source Z retained";
  return "No source Z present";
}

function stormwaterQualitySummary(quality: {
  missing_pipe_number_count: number;
  duplicate_pipe_number_value_count: number;
  missing_start_endpoint_count: number;
  missing_end_endpoint_count: number;
  missing_notes_count: number;
}): string {
  return [
    `Missing pipe numbers: ${quality.missing_pipe_number_count}`,
    `Duplicate pipe-number values: ${quality.duplicate_pipe_number_value_count}`,
    `Missing start endpoints: ${quality.missing_start_endpoint_count}`,
    `Missing end endpoints: ${quality.missing_end_endpoint_count}`,
    `Missing notes: ${quality.missing_notes_count}`,
  ].join(" · ");
}

export function Dashboard() {
  const layersQuery = useQuery({ queryKey: ["layers"], queryFn: fetchLayers });
  const districtsQuery = useQuery({
    queryKey: ["administrative-districts"],
    queryFn: fetchAdministrativeDistricts,
  });
  const [viewportBbox, setViewportBbox] = useState<StormwaterBbox>(DEFAULT_STORMWATER_BBOX);
  const bboxTooBroad = isStormwaterBboxTooBroad(viewportBbox);
  const stormwaterQuery = useQuery({
    queryKey: ["stormwater-pipelines", viewportBbox],
    queryFn: () => fetchStormwaterPipelines(viewportBbox),
    enabled: !bboxTooBroad,
  });
  const [preview, setPreview] = useState<SimulationPreview | null>(null);
  const [showSimulatedPaths, setShowSimulatedPaths] = useState(false);
  const [showBoundaries, setShowBoundaries] = useState(false);
  const [showStormwater, setShowStormwater] = useState(false);
  const [selectedDistrict, setSelectedDistrict] = useState<AdministrativeDistrictProperties | null>(
    null,
  );
  const [selectedSegment, setSelectedSegment] = useState<StormwaterProperties | null>(null);
  const [duration, setDuration] = useState(12);
  const [seed, setSeed] = useState(42);
  const [walkers, setWalkers] = useState(24);
  const mutation = useMutation({ mutationFn: requestPreview, onSuccess: setPreview });
  const layers = layersQuery.data ?? DEFAULT_LAYERS;
  const districts = districtsQuery.data ?? null;
  const hasDistricts = (districts?.features.length ?? 0) > 0;
  const boundaryStatus = districtsQuery.isPending
    ? "Loading boundaries…"
    : districtsQuery.isError
      ? "Boundary service unavailable"
      : hasDistricts
        ? "Administrative reference · UNVERIFIED"
        : "No boundaries imported";
  const stormwater = stormwaterQuery.data ?? null;
  const hasStormwater = stormwater?.data_state === "available";
  const selectedVisibleSegment =
    stormwaterQuery.isError || stormwater?.data_state !== "available"
      ? null
      : (stormwater.features.find(
          (feature) => feature.properties.segment_id === selectedSegment?.segment_id,
        )?.properties ?? null);
  const stormwaterStatus = bboxTooBroad
    ? "Zoom in to load pipelines"
    : stormwaterQuery.isPending
      ? "Loading pipelines…"
      : stormwaterQuery.isError
        ? "Stormwater service unavailable"
        : stormwater?.data_state === "empty"
          ? "No pipelines imported"
          : (stormwater?.feature_count ?? 0) === 0
            ? "No pipelines in view"
            : stormwater?.truncated
              ? "Showing partial data · zoom in"
              : "Infrastructure reference · UNVERIFIED";

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            見
          </div>
          <div>
            <h1>見光鼠</h1>
            <p>RatSight · Urban movement analysis</p>
          </div>
        </div>
        <div className="header-status">
          <span className="status-dot" /> Research workspace{" "}
          <span className="status-divider">/</span> Taipei City
        </div>
      </header>

      <div className="workspace-heading">
        <div>
          <p className="eyebrow">DECISION SUPPORT · INITIALIZATION BUILD</p>
          <h2>Movement analysis workspace</h2>
        </div>
        <span className="notice-chip">No real observation data loaded</span>
      </div>

      <div className="workspace-grid">
        <section className="map-column" aria-label="Spatial workspace">
          <div className="map-toolbar">
            <div>
              <strong>Spatial context</strong>
              <span>
                Basemap · reference boundaries ·{" "}
                {hasStormwater ? "stormwater reference data" : "no stormwater data"} · no rodent
                observations
              </span>
            </div>
            <span className="map-coordinate">25.033° N · 121.565° E</span>
          </div>
          <MapView
            preview={preview}
            showSimulatedPaths={showSimulatedPaths}
            boundaries={districts}
            showBoundaries={showBoundaries}
            selectedDistrictId={selectedDistrict?.district_id ?? null}
            onSelectDistrict={setSelectedDistrict}
            stormwater={stormwater}
            showStormwater={showStormwater}
            selectedSegmentId={selectedVisibleSegment?.segment_id ?? null}
            onSelectSegment={setSelectedSegment}
            onBoundsChange={setViewportBbox}
          />
          <div className="map-legend">
            <span className="legend-item">
              <i className="legend-basemap" /> Basemap
            </span>
            <span className="legend-item">
              <i className="legend-administrative" /> Administrative reference
            </span>
            <span className="legend-item">
              <i className="legend-stormwater" /> Stormwater (reference)
            </span>
            <span className="legend-item">
              <i className="legend-simulated" /> Simulated · synthetic fixture
            </span>
          </div>
          <div className="data-boundary">
            <strong>Data boundary</strong>
            <span>
              Map center is a navigational starting point. Infrastructure reference data is separate
              from animal observations; no rodent observations are loaded.
            </span>
          </div>
        </section>

        <aside className="control-rail" aria-label="Analysis controls">
          <section className="panel layer-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">MAP CONTENT</p>
                <h3>Layers</h3>
              </div>
              <span className="panel-count">{layers.length}</span>
            </div>
            {layersQuery.isError && (
              <p className="inline-note">API unavailable; showing empty layer catalog.</p>
            )}
            <div className="layer-list">
              <label className={`layer-row ${hasDistricts ? "" : "is-unavailable"}`}>
                <span className="layer-glyph glyph-administrative_boundaries" aria-hidden="true">
                  ▦
                </span>
                <span className="layer-name">
                  Administrative districts
                  <small>{boundaryStatus}</small>
                </span>
                <input
                  type="checkbox"
                  aria-label="Administrative districts"
                  disabled={!hasDistricts}
                  checked={showBoundaries}
                  onChange={(event) => setShowBoundaries(event.target.checked)}
                />
              </label>
              <label className={`layer-row ${hasStormwater ? "" : "is-unavailable"}`}>
                <span className="layer-glyph glyph-stormwater" aria-hidden="true">
                  ═
                </span>
                <span className="layer-name">
                  Stormwater pipelines
                  <small>{stormwaterStatus}</small>
                </span>
                <input
                  type="checkbox"
                  aria-label="Stormwater pipelines"
                  disabled={!hasStormwater}
                  checked={showStormwater}
                  onChange={(event) => setShowStormwater(event.target.checked)}
                />
              </label>
              {layers
                .filter((layer) => layer.id !== "stormwater_networks")
                .map((layer) => {
                  const previewReady = layer.id === "simulated_paths" && preview !== null;
                  const available = layer.available || previewReady;
                  return (
                    <label
                      className={`layer-row ${available ? "" : "is-unavailable"}`}
                      key={layer.id}
                    >
                      <span className={`layer-glyph glyph-${layer.id}`}>
                        {LAYER_GLYPHS[layer.id] ?? "·"}
                      </span>
                      <span className="layer-name">
                        {layer.label}
                        <small>
                          {available
                            ? (layer.classification ?? "AVAILABLE")
                            : layer.id === "simulated_paths"
                              ? "Run preview to generate"
                              : "No dataset loaded"}
                        </small>
                      </span>
                      <input
                        type="checkbox"
                        aria-label={layer.label}
                        disabled={!available || layer.id !== "simulated_paths"}
                        checked={layer.id === "simulated_paths" && showSimulatedPaths}
                        onChange={(event) => setShowSimulatedPaths(event.target.checked)}
                      />
                    </label>
                  );
                })}
            </div>
          </section>

          <section
            className="panel reference-panel"
            aria-label="Administrative reference inspection"
          >
            <div className="panel-heading">
              <div>
                <p className="eyebrow">ADMINISTRATIVE REFERENCE</p>
                <h3>District inspection</h3>
              </div>
              <span className="classification-badge">UNVERIFIED</span>
            </div>
            {hasDistricts && districts ? (
              <>
                <p className="reference-label" id="district-list-label">
                  Districts · select to inspect
                </p>
                <ul className="district-list" aria-labelledby="district-list-label">
                  {districts.features.map((feature) => {
                    const selected =
                      selectedDistrict?.district_id === feature.properties.district_id;
                    return (
                      <li key={feature.properties.district_id}>
                        <button
                          type="button"
                          className={`district-button ${selected ? "is-selected" : ""}`}
                          aria-pressed={selected}
                          onClick={() => setSelectedDistrict(feature.properties)}
                        >
                          {feature.properties.district_name}
                        </button>
                      </li>
                    );
                  })}
                </ul>
                {selectedDistrict ? (
                  <div className="reference-details" aria-live="polite">
                    <div className="analysis-row">
                      <span>District</span>
                      <strong>{selectedDistrict.district_name}</strong>
                    </div>
                    <div className="analysis-row">
                      <span>District ID</span>
                      <strong>{selectedDistrict.district_id}</strong>
                    </div>
                    <div className="analysis-row">
                      <span>Data class</span>
                      <strong>{selectedDistrict.data_class}</strong>
                    </div>
                    <div className="analysis-row">
                      <span>Classification</span>
                      <strong>{selectedDistrict.classification}</strong>
                    </div>
                    <div className="analysis-row">
                      <span>Dataset</span>
                      <strong>{selectedDistrict.dataset_id || "Unknown"}</strong>
                    </div>
                    <div className="analysis-row">
                      <span>Resource version</span>
                      <strong>{selectedDistrict.resource_version || "Unknown"}</strong>
                    </div>
                  </div>
                ) : (
                  <p className="inline-note" aria-live="polite">
                    Select a district from the list or the map to inspect its name and source.
                  </p>
                )}
              </>
            ) : (
              <p className="inline-note" aria-live="polite">
                {boundaryStatus}
              </p>
            )}
            <p className="reference-note">
              Administrative reference geometry. Not rodent observations, inferred connectivity, or
              simulated movement.
            </p>
            {districts?.provenance && (
              <div className="provenance-block" aria-label="Administrative source provenance">
                <span>Source URL</span>
                {isSafeExternalUrl(districts.provenance.source_url) ? (
                  <a
                    href={districts.provenance.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {districts.provenance.source_url}
                  </a>
                ) : (
                  <strong>{districts.provenance.source_url}</strong>
                )}
                <span>Attribution</span>
                <strong>{districts.provenance.attribution}</strong>
                <span>License</span>
                <strong>{districts.provenance.license}</strong>
                <span>Currentness</span>
                <strong>{districts.provenance.uncertainty.currentness}</strong>
              </div>
            )}
          </section>

          <section className="panel stormwater-panel" aria-label="Stormwater pipeline inspection">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">INFRASTRUCTURE REFERENCE</p>
                <h3>Stormwater pipelines</h3>
              </div>
              <span className="classification-badge">UNVERIFIED</span>
            </div>
            {hasStormwater ? (
              <>
                <p className="reference-label">{stormwaterStatus}</p>
                <p className="reference-label" id="segment-list-label">
                  Pipelines · select to inspect
                </p>
                <ul className="district-list" aria-labelledby="segment-list-label">
                  {stormwater?.features.slice(0, MAX_VISIBLE_PIPELINE_LIST_ITEMS).map((feature) => {
                    const selected =
                      selectedVisibleSegment?.segment_id === feature.properties.segment_id;
                    return (
                      <li key={feature.properties.segment_id}>
                        <button
                          type="button"
                          className={`district-button ${selected ? "is-selected" : ""}`}
                          aria-pressed={selected}
                          aria-label={feature.properties.segment_id}
                          onClick={() => setSelectedSegment(feature.properties)}
                        >
                          {feature.properties.pipe_number || feature.properties.segment_id}
                        </button>
                      </li>
                    );
                  })}
                </ul>
                {(stormwater?.features.length ?? 0) > MAX_VISIBLE_PIPELINE_LIST_ITEMS && (
                  <p className="inline-note">
                    Showing the first {MAX_VISIBLE_PIPELINE_LIST_ITEMS} pipelines; select other
                    features directly on the map.
                  </p>
                )}
                {selectedVisibleSegment ? (
                  <div className="reference-details" aria-live="polite">
                    {STORMWATER_ATTRIBUTE_LABELS.map(([key, label]) => (
                      <div className="analysis-row" key={key}>
                        <span>{label}</span>
                        <strong>{selectedVisibleSegment[key] || "Unavailable"}</strong>
                      </div>
                    ))}
                    <div className="analysis-row">
                      <span>Data class</span>
                      <strong>{selectedVisibleSegment.data_class}</strong>
                    </div>
                    <div className="analysis-row">
                      <span>Classification</span>
                      <strong>{selectedVisibleSegment.classification}</strong>
                    </div>
                  </div>
                ) : (
                  <p className="inline-note" aria-live="polite">
                    Select a pipeline from the list or the map to inspect its source attributes.
                  </p>
                )}
                <p className="reference-note">
                  Not verified physical connectivity. Start/end node values are publisher attributes
                  only.
                </p>
              </>
            ) : (
              <p className="inline-note" aria-live="polite">
                {stormwaterStatus === "No pipelines imported"
                  ? "No stormwater pipelines have been imported."
                  : stormwaterStatus}
              </p>
            )}
            {stormwater?.provenance && (
              <div className="provenance-block" aria-label="Stormwater source provenance">
                <span>Source URL</span>
                {isSafeExternalUrl(stormwater.provenance.source_url) ? (
                  <a
                    href={stormwater.provenance.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {stormwater.provenance.source_url}
                  </a>
                ) : (
                  <strong>{stormwater.provenance.source_url}</strong>
                )}
                <span>Download URL</span>
                {isSafeExternalUrl(stormwater.provenance.download_url) ? (
                  <a
                    href={stormwater.provenance.download_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {stormwater.provenance.download_url}
                  </a>
                ) : (
                  <strong>{stormwater.provenance.download_url}</strong>
                )}
                <span>Attribution</span>
                <strong>{stormwater.provenance.attribution}</strong>
                <span>License</span>
                <strong>{stormwater.provenance.license}</strong>
                <span>Resource version</span>
                <strong>{stormwater.provenance.resource_version}</strong>
                <span>Currentness</span>
                <strong>{stormwater.provenance.uncertainty.currentness}</strong>
                <span>Vertical coordinate</span>
                <strong>{zHandlingText(stormwater.provenance.z_handling)}</strong>
                <span>Source quality</span>
                <strong>{stormwaterQualitySummary(stormwater.provenance.source_quality)}</strong>
                {stormwater.provenance.source_quality.reference_only && (
                  <small>
                    Publisher reference-only warning: use as a reference; obtain exact data from the
                    responsible utility agency.
                  </small>
                )}
              </div>
            )}
          </section>

          <section className="panel simulation-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">SYNTHETIC DEMO</p>
                <h3>Simulation preview</h3>
              </div>
              <span className="classification-badge">SIMULATED</span>
            </div>
            <div className="form-field">
              <label htmlFor="study-area">Study area</label>
              <select id="study-area" value="taipei_synthetic_demo" disabled>
                <option value="taipei_synthetic_demo">Taipei · synthetic demonstration</option>
              </select>
              <small>Coordinates in fixture are schematic, not a real study area.</small>
            </div>
            <div className="form-field">
              <label htmlFor="duration">Duration · steps</label>
              <input
                id="duration"
                type="number"
                min={1}
                max={100}
                value={duration}
                onChange={(event) => setDuration(Number(event.target.value))}
              />
            </div>
            <div className="field-pair">
              <div className="form-field">
                <label htmlFor="seed">Random seed</label>
                <input
                  id="seed"
                  type="number"
                  min={0}
                  value={seed}
                  onChange={(event) => setSeed(Number(event.target.value))}
                />
              </div>
              <div className="form-field">
                <label htmlFor="walkers">Walkers</label>
                <input
                  id="walkers"
                  type="number"
                  min={1}
                  max={1000}
                  value={walkers}
                  onChange={(event) => setWalkers(Number(event.target.value))}
                />
              </div>
            </div>
            <div className="form-field">
              <label htmlFor="model">Movement model</label>
              <select id="model" value="weighted_random_walk" disabled>
                <option value="weighted_random_walk">Weighted random walk · demo</option>
              </select>
            </div>
            <div className="form-field">
              <label htmlFor="scenario">Intervention scenario</label>
              <select id="scenario" value="baseline" disabled>
                <option value="baseline">Baseline · no intervention</option>
              </select>
            </div>
            <Button
              className="run-button"
              disabled={mutation.isPending || duration < 1 || walkers < 1 || seed < 0}
              onClick={() =>
                mutation.mutate({
                  study_area: "taipei_synthetic_demo",
                  duration_steps: duration,
                  walkers,
                  random_seed: seed,
                  movement_model: "weighted_random_walk",
                  intervention_scenario: "baseline",
                })
              }
            >
              {mutation.isPending ? "Running preview…" : "Run synthetic preview"}
            </Button>
            {mutation.isError && (
              <p className="error-note" role="alert">
                Preview unavailable. Confirm API is running, then retry.
              </p>
            )}
            {mutation.isSuccess && (
              <p className="success-note" role="status">
                Reproducible run complete · seed {preview?.parameters.random_seed}
              </p>
            )}
          </section>

          <section className="panel analysis-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">RESULTS & PROVENANCE</p>
                <h3>Analysis</h3>
              </div>
            </div>
            <div className="analysis-row">
              <span>Observation summary</span>
              <strong>Not available</strong>
            </div>
            <div className="analysis-row">
              <span>Potential corridors</span>
              <strong>{preview ? `${preview.edges.length} synthetic edges` : "Not modeled"}</strong>
            </div>
            <div className="analysis-row">
              <span>Relative risk</span>
              <strong>Not estimated</strong>
            </div>
            <div className="analysis-row">
              <span>Model uncertainty</span>
              <strong>Not quantified</strong>
            </div>
            <div className="provenance-block">
              <span>Evidence provenance</span>
              <strong>{preview ? preview.provenance.source_id : "No evidence dataset"}</strong>
              <small>Simulated paths are not observed animal migration routes.</small>
            </div>
            {preview && (
              <div className="result-summary" aria-label="Simulation summary">
                <span>{preview.nodes.reduce((sum, node) => sum + node.visits, 0)} node visits</span>
                <span>·</span>
                <span>
                  {preview.model_id} v{preview.model_version}
                </span>
              </div>
            )}
          </section>
        </aside>
      </div>
      <footer className="footer-note">
        RatSight initialization build <span>·</span> Observed data unavailable <span>·</span>{" "}
        Simulation outputs are synthetic and explicitly labeled
      </footer>
    </main>
  );
}
