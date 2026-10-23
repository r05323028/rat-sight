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
  };
  provenance: {
    classification: "SIMULATED";
    source_type: "synthetic_fixture";
    source_id: string;
    source_crs: "EPSG:4326";
    note: string;
  };
  assumptions: string[];
  nodes: {
    id: string;
    coordinates: [number, number];
    visits: number;
    probability: number;
    classification: "SIMULATED";
  }[];
  edges: {
    source: string;
    target: string;
    edge_id: string;
    movement_weight: number;
    visits: number;
    probability: number;
    classification: "SIMULATED";
  }[];
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

export async function requestPreview(input: {
  study_area: string;
  duration_steps: number;
  walkers: number;
  random_seed: number;
  movement_model: string;
  intervention_scenario: string;
}): Promise<SimulationPreview> {
  const response = await fetch(`${API_BASE_URL}/api/v1/simulations/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error(`Simulation preview failed (${response.status})`);
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
