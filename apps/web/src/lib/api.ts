export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

export type Layer = {
  id: string;
  label: string;
  available: boolean;
  classification: "OBSERVED" | "INFERRED" | "SIMULATED" | "UNVERIFIED" | null;
  message: string;
};

export type SimulationLineString = {
  type: "LineString";
  coordinates: [number, number][];
};

export type SimulationTrajectoryStep = {
  source: string;
  target: string;
  edge_id: string;
  geometry: [number, number][];
  classification: "SIMULATED";
  // Zero-based position in the trajectory; callers fall back to array order when absent.
  step_index?: number;
};

export type SimulationTrajectory = {
  walker_id: number;
  edges: SimulationTrajectoryStep[];
  terminated_early?: boolean;
  // Additive backend diagnosis; absent on older API builds, so treat absence as unknown.
  termination_reason?: "completed" | "dead_end" | "no_eligible_transition";
  classification: "SIMULATED";
};

export type SimulationPreview = {
  simulation_status: "completed";
  classification: "SIMULATED";
  model_id: string;
  model_version: string;
  parameters: {
    study_area: string;
    duration_steps: number;
    walkers: number;
    random_seed: number;
    movement_model: string;
    intervention_scenario: string;
    output_mode?: "aggregate" | "trajectory";
  };
  provenance: {
    classification: "SIMULATED";
    source_type: "synthetic_fixture" | "osm_surface_network";
    source_id: string;
    source_crs: "EPSG:4326";
    source_sha256?: string;
    source_url?: string;
    resource_version?: string;
    license?: string;
    attribution?: string;
    coverage?: string;
    note: string;
    network_type?: "SCHEMATIC" | "SOURCE_NETWORK" | "REFERENCE";
  };
  assumptions: string[];
  // Synthetic model input echoed by the API; `selection` separates the deterministic
  // default origin from one the analyst chose.
  origin?: {
    node_id: string;
    coordinates: [number, number];
    classification: "SIMULATED";
    selection: "default" | "user";
    note?: string;
  };
  origin_node_id?: string;
  /** Server-side counts over the returned graph; follows the resolved origin. */
  reachability?: {
    origin_node_id: string;
    reachable_nodes: number;
    total_nodes: number;
    reachable_edges: number;
    total_edges: number;
    component_count: number;
    classification: "SIMULATED";
    note: string;
  };
  nodes: {
    id: string;
    coordinates: [number, number];
    visits: number;
    probability: number;
    classification: "SIMULATED";
  }[];
  trajectory_count?: number;
  trajectory_truncated?: boolean;
  edges: {
    source: string;
    target: string;
    edge_id: string;
    movement_weight: number;
    visits: number;
    probability: number;
    classification: "SIMULATED";
    geometry?: SimulationLineString;
    source_id?: string;
  }[];
  trajectories?: SimulationTrajectory[];
};

export type ProvenanceProcessing = {
  tool: string;
  tool_version: string;
  steps: string[];
};

export type ProvenanceUncertainty = {
  currentness: string;
  note: string;
};

// Shared envelope for provenance-preserving reference FeatureCollections. The
// per-layer data_class, geometry and feature-property types stay explicit.
export type ReferenceFeatureCollection<
  TGeometry,
  TProperties,
  TDataClass extends string,
  TProvenance,
> = {
  type: "FeatureCollection";
  data_state: "empty" | "available";
  data_class: TDataClass;
  provenance: TProvenance | null;
  features: {
    type: "Feature";
    id?: string | number;
    geometry: TGeometry;
    properties: TProperties;
  }[];
};

// Administrative reference geometry. `data_class` is deliberately separate from the
// epistemic `classification` vocabulary used for rodent/infrastructure evidence.
export type AdministrativeDistrictGeometry =
  | { type: "Polygon"; coordinates: number[][][] }
  | { type: "MultiPolygon"; coordinates: number[][][][] };

export type AdministrativeDistrictProvenance = {
  schema_version: string;
  source_url: string;
  dataset_id: string;
  resource_version: string;
  retrieved_at: string;
  archive_sha256: string;
  license: string;
  attribution: string;
  source_crs: "EPSG:3826";
  target_crs: "EPSG:4326";
  processing: ProvenanceProcessing;
  uncertainty: ProvenanceUncertainty;
};

export type AdministrativeDistrictProperties = {
  district_id: string;
  district_name: string;
  data_class: "ADMINISTRATIVE_REFERENCE";
  classification: "UNVERIFIED";
  provenance_schema_version: string;
  dataset_id: string;
  resource_version: string;
  archive_sha256: string;
};

export type AdministrativeDistrictFeature = {
  type: "Feature";
  id?: string | number;
  geometry: AdministrativeDistrictGeometry;
  properties: AdministrativeDistrictProperties;
};

export type AdministrativeDistricts = ReferenceFeatureCollection<
  AdministrativeDistrictGeometry,
  AdministrativeDistrictProperties,
  "ADMINISTRATIVE_REFERENCE",
  AdministrativeDistrictProvenance
>;

export async function fetchLayers(): Promise<Layer[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/layers`);
  if (!response.ok) throw new Error(`Layer request failed (${response.status})`);
  return response.json() as Promise<Layer[]>;
}

const SOURCE_NETWORK_UNAVAILABLE_PREFIX = "來源網路無法使用：";

// Only the API's own code means "source network missing"; other failures stay generic.
export function isSourceNetworkUnavailable(error: unknown): boolean {
  return error instanceof Error && error.message.startsWith(SOURCE_NETWORK_UNAVAILABLE_PREFIX);
}

export async function requestPreview(input: {
  study_area: string;
  duration_steps: number;
  walkers: number;
  random_seed: number;
  movement_model: string;
  intervention_scenario: string;
  origin_node_id?: string;
}): Promise<SimulationPreview> {
  const response = await fetch(`${API_BASE_URL}/api/v1/simulations/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: { code?: string; message?: string; provisioning?: string };
    } | null;
    const detail = payload?.detail;
    throw new Error(
      detail?.code === "SOURCE_NETWORK_UNAVAILABLE"
        ? `${SOURCE_NETWORK_UNAVAILABLE_PREFIX}${detail.message ?? "未知錯誤"} ${
            detail.provisioning ?? ""
          }`
        : detail?.code === "ORIGIN_NODE_NOT_IN_GRAPH"
          ? `合成起點不在模型網路內：${detail.message ?? "未知錯誤"}`
          : `Simulation preview failed (${response.status})`,
    );
  }
  return response.json() as Promise<SimulationPreview>;
}

export async function fetchAdministrativeDistricts(): Promise<AdministrativeDistricts> {
  const response = await fetch(`${API_BASE_URL}/api/v1/administrative-districts`);
  if (!response.ok) {
    throw new Error(`Administrative districts request failed (${response.status})`);
  }
  return response.json() as Promise<AdministrativeDistricts>;
}

// Stormwater infrastructure reference lines. Properties carry the opaque
// segment_id plus the bounded publisher-attribute allowlist; data_class lives on
// the envelope and full provenance at the top level. No topology is exposed.
// Shared bounded-query bbox: four finite EPSG:4326 numbers in minX,minY,maxX,maxY order.
export type Bbox = [number, number, number, number];

/** @deprecated use Bbox */
export type StormwaterBbox = Bbox;

export type StormwaterGeometry = { type: "LineString"; coordinates: number[][] };

export type StormwaterProperties = {
  segment_id: string;
  data_class: "INFRASTRUCTURE_REFERENCE";
  classification: "UNVERIFIED";
  provenance_schema_version: string;
  dataset_id: string;
  resource_version: string;
  archive_sha256: string;
  category_code?: string | null;
  pipe_number?: string | null;
  start_node_id?: string | null;
  end_node_id?: string | null;
  managing_unit?: string | null;
  work_category?: string | null;
  installation_date?: string | null;
  dimension_unit?: string | null;
  diameter_width?: string | null;
  diameter_height?: string | null;
  conduit_count?: string | null;
  material?: string | null;
  start_burial_depth?: string | null;
  end_burial_depth?: string | null;
  length?: string | null;
  pipe_type?: string | null;
  use_status?: string | null;
  data_status?: string | null;
  notes?: string | null;
};

export type StormwaterProvenance = {
  schema_version: "1";
  source_url: string;
  download_url: string;
  dataset_id: string;
  resource_id: string;
  resource_version: string;
  retrieved_at: string;
  archive_sha256: string;
  license: string;
  attribution: string;
  source_crs: "EPSG:3826";
  target_crs: "EPSG:4326";
  z_handling: "dropped" | "retained" | "not_present";
  processing: ProvenanceProcessing;
  source_quality: {
    reference_only: boolean;
    missing_pipe_number_count: number;
    duplicate_pipe_number_value_count: number;
    missing_start_endpoint_count: number;
    missing_end_endpoint_count: number;
    missing_notes_count: number;
  };
  uncertainty: ProvenanceUncertainty;
};

export type StormwaterNetwork = ReferenceFeatureCollection<
  StormwaterGeometry,
  StormwaterProperties,
  "INFRASTRUCTURE_REFERENCE",
  StormwaterProvenance
> & {
  feature_count: number;
  bbox: StormwaterBbox | null;
  truncated: boolean;
};

// Shared bounded-query contract: width and height must not exceed 0.30 degrees.
export const BBOX_MAX_SPAN_DEGREES = 0.3;

export function isBboxTooBroad(bbox: Bbox): boolean {
  return bbox[2] - bbox[0] > BBOX_MAX_SPAN_DEGREES || bbox[3] - bbox[1] > BBOX_MAX_SPAN_DEGREES;
}

export const isStormwaterBboxTooBroad = isBboxTooBroad;

export async function fetchStormwaterPipelines(bbox?: StormwaterBbox): Promise<StormwaterNetwork> {
  const query = bbox ? `?bbox=${bbox.join(",")}` : "";
  const response = await fetch(`${API_BASE_URL}/api/v1/stormwater-pipelines${query}`);
  if (!response.ok) {
    throw new Error(`Stormwater pipelines request failed (${response.status})`);
  }
  return response.json() as Promise<StormwaterNetwork>;
}

// Synthetic rodent report-shaped fixtures. These are SIMULATED report records,
// not verified observations, prevalence, population, movement, or risk evidence.
export type RodentReportGeometry = { type: "Point"; coordinates: [number, number] };

export type RodentReportProperties = {
  report_id: string;
  source: "synthetic_fixture";
  report_type: "sighting_report" | "nuisance_report" | "service_request" | "unknown";
  reported_at: string;
  location_precision: "synthetic_point" | "coarse_grid_100m" | "coarse_grid_1km" | "unknown";
  review_status: "unreviewed" | "platform_moderated" | "municipal_reviewed" | "unknown";
  municipal_status: "not_assessed" | "confirmed_by_authority" | "rejected" | "unknown";
  action_status: "none_reported" | "inspection" | "treatment" | "unknown";
  data_class: "RODENT_REPORT";
  classification: "SIMULATED";
  provenance_schema_version: string;
  dataset_id: string;
  resource_version: string;
  content_sha256: string;
};

export type RodentReportProvenance = {
  schema_version: "1";
  source_kind: "synthetic_fixture";
  dataset_id: string;
  resource_version: string;
  retrieved_at: string;
  content_sha256: string;
  license: string;
  attribution: string;
  source_crs: "EPSG:4326";
  target_crs: "EPSG:4326";
  processing: ProvenanceProcessing;
  synthetic: true;
  uncertainty: ProvenanceUncertainty;
};

export type RodentReports = ReferenceFeatureCollection<
  RodentReportGeometry,
  RodentReportProperties,
  "RODENT_REPORT",
  RodentReportProvenance
> & {
  classification: "SIMULATED";
  feature_count: number;
  bbox: Bbox | null;
  reported_from: string | null;
  reported_to: string | null;
  truncated: boolean;
};

export type RodentReportFilters = {
  bbox?: Bbox;
  reportedFrom?: string | null;
  reportedTo?: string | null;
};

// Citizen-report aggregates are derived from a public citizen export: 250 m cell
// counts per month, with small cells suppressed. They are UNVERIFIED citizen
// reports, never observations, and never a simulation input.
export type CitizenReportCellGeometry = { type: "Polygon"; coordinates: number[][][] };

export type CitizenReportCellProperties = {
  cell_id: string;
  month: string;
  report_type: "sighting" | "bait_station" | "other";
  count: number;
  data_class: "CITIZEN_REPORT_AGGREGATE";
  classification: "UNVERIFIED";
  attribution: string;
};

export type CitizenReportAggregation = {
  cell_size_meters: number;
  month_timezone_assumption: string;
  suppression_minimum: number;
  dropped_fields: string[];
};

export type CitizenReportCounts = {
  parsed: number;
  used: number;
  invalid_coordinates: number;
  suppressed_records: number;
  suppressed_cells: number;
};

export type CitizenReportAggregateProvenance = {
  schema_version: "1";
  source_kind: "public_citizen_report_export";
  dataset_id: string;
  resource_version: string;
  retrieved_at: string;
  content_sha256: string;
  source_url: string;
  license: string;
  attribution: string;
  source_crs: "EPSG:4326";
  target_crs: "EPSG:4326";
  processing: ProvenanceProcessing;
  aggregation: CitizenReportAggregation;
  counts: CitizenReportCounts;
  synthetic: false;
  uncertainty: ProvenanceUncertainty;
};

export type CitizenReportAggregates = ReferenceFeatureCollection<
  CitizenReportCellGeometry,
  CitizenReportCellProperties,
  "CITIZEN_REPORT_AGGREGATE",
  CitizenReportAggregateProvenance
> & {
  classification: "UNVERIFIED";
  notice: string;
  feature_count: number;
  bbox: Bbox | null;
  truncated: boolean;
};

export async function fetchCitizenReportAggregates(
  filters: { bbox?: Bbox; months?: string } = {},
): Promise<CitizenReportAggregates> {
  const params = new URLSearchParams();
  if (filters.bbox) params.set("bbox", filters.bbox.join(","));
  if (filters.months) params.set("months", filters.months);
  const query = params.toString();
  const response = await fetch(
    `${API_BASE_URL}/api/v1/citizen-report-aggregates${query ? `?${query}` : ""}`,
  );
  if (!response.ok) {
    throw new Error(`Citizen report aggregates request failed (${response.status})`);
  }
  return response.json() as Promise<CitizenReportAggregates>;
}

// Asia/Taipei has been a fixed UTC+08:00 offset since 1979, so the conversion is
// plain arithmetic: no machine timezone, DST rule, or locale can change it.
const TAIPEI_UTC_OFFSET_HOURS = 8;

// datetime-local values are Asia/Taipei wall-clock; the backend filter contract
// takes RFC3339 UTC bounds at minute precision, so convert before sending.
export function taipeiLocalToUtc(value: string): string | null {
  if (!value) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(value);
  if (!match) return null;
  const [, year, month, day, hour, minute] = match;
  const [y, m, d, h, min] = [year, month, day, hour, minute].map(Number);
  const converted = new Date(Date.UTC(y, m - 1, d, h - TAIPEI_UTC_OFFSET_HOURS, min));
  const backToLocal = new Date(converted.getTime() + TAIPEI_UTC_OFFSET_HOURS * 3_600_000);
  // Date.UTC rolls impossible values over (month 13, year 0050 -> 1950), which
  // would silently query a different date; refuse them instead.
  if (
    backToLocal.getUTCFullYear() !== y ||
    backToLocal.getUTCMonth() !== m - 1 ||
    backToLocal.getUTCDate() !== d ||
    backToLocal.getUTCHours() !== h ||
    backToLocal.getUTCMinutes() !== min
  ) {
    return null;
  }
  return `${converted.toISOString().slice(0, 16)}:00Z`;
}

// Client-side guard so a reversed range never reaches the API. Both inputs are
// already normalized to the same RFC3339 Z shape, so lexical comparison is safe,
// and equal boundaries stay valid because both ends are inclusive.
export function isReportedRangeInvalid(from: string | null, to: string | null): boolean {
  return Boolean(from && to && from > to);
}

export async function fetchRodentReports(
  filters: RodentReportFilters = {},
): Promise<RodentReports> {
  const params = new URLSearchParams();
  if (filters.bbox) params.set("bbox", filters.bbox.join(","));
  if (filters.reportedFrom) params.set("reported_from", filters.reportedFrom);
  if (filters.reportedTo) params.set("reported_to", filters.reportedTo);
  const query = params.toString();
  const response = await fetch(`${API_BASE_URL}/api/v1/rodent-reports${query ? `?${query}` : ""}`);
  if (!response.ok) {
    throw new Error(`Rodent reports request failed (${response.status})`);
  }
  return response.json() as Promise<RodentReports>;
}
