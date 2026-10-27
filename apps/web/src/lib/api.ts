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
    origin_node_id?: string;
    origin_node_ids?: string[];
    origin_cell_id?: string;
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
    node_ids?: string[];
    coordinates: [number, number];
    classification: "SIMULATED";
    selection: "default" | "user" | "cell";
    cell_id?: string;
    /** Present only when a real aggregate cell resolved the origin. */
    cell_candidate_count?: number | null;
    cell_resolver_version?: string | null;
    note?: string;
  };
  origin_node_id?: string;
  /** Server-side counts over the returned graph; follows the resolved origin. */
  reachability?: {
    origin_node_id: string;
    origin_node_ids?: string[];
    reachable_nodes: number;
    total_nodes: number;
    reachable_edges: number;
    total_edges: number;
    component_count: number;
    /** Full-graph nodes with at least one simulation visit; absent on older API builds. */
    sampled_nodes?: number;
    classification: "SIMULATED";
    note: string;
  };
  /** Absent on older API builds that returned the full graph as map geometry. */
  visualization?: {
    mode: "full_graph" | "local_reference";
    radius_meters?: number | null;
    returned_nodes: number;
    returned_edges: number;
    total_nodes: number;
    total_edges: number;
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

type SimulationPreviewRequestBase = {
  duration_steps: number;
  walkers: number;
  random_seed: number;
  movement_model: string;
  intervention_scenario: string;
};

export type SimulationPreviewRequest =
  | (SimulationPreviewRequestBase & {
      study_area: "taipei_osm_songshan";
      origin_cell_id: string;
      origin_node_id?: never;
    })
  | (SimulationPreviewRequestBase & {
      study_area: "taipei_synthetic_demo";
      origin_node_id: string;
      origin_cell_id?: never;
    })
  | (SimulationPreviewRequestBase & {
      study_area: "taipei_synthetic_demo";
      origin_cell_id: string;
      origin_node_id?: never;
    });

export async function requestPreview(input: SimulationPreviewRequest): Promise<SimulationPreview> {
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
          : detail?.code === "ORIGIN_CELL_NOT_RESOLVABLE"
            ? `公民通報格網起點無法解析：${detail.message ?? "未知錯誤"}`
            : detail?.code === "ORIGIN_CELL_STORAGE_UNAVAILABLE"
              ? `公民通報彙整儲存無法使用：${detail.message ?? "未知錯誤"}`
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

// Citizen-report aggregates are derived from a public citizen export: 250 m cell
// counts per month, with small cells suppressed. They are UNVERIFIED citizen
// reports, never observations. Counts never become simulation weights; the bounded
// origin path may resolve one selected cell to every strictly in-cell node, with one
// strict candidate or uniform seeded starts across multiple candidates.
export type CitizenReportCellGeometry = { type: "Polygon"; coordinates: number[][][] };

export type CitizenReportCellProperties = {
  cell_id: string;
  month: string;
  report_type: "sighting" | "bait_station" | "other";
  count: number | null;
  data_class: "CITIZEN_REPORT_AGGREGATE" | "SYNTHETIC_AGGREGATE_FIXTURE";
  classification: "UNVERIFIED" | "SIMULATED";
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

export type CitizenReportAggregateProvenance =
  | {
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
    }
  | {
      schema_version: "1";
      source_kind: "synthetic_aggregate_fixture";
      dataset_id: string;
      resource_version: string;
      content_sha256: string;
      reference_source_id: string;
      reference_source_sha256: string;
      source_crs: "EPSG:4326";
      target_crs: "EPSG:4326";
      cell_size_meters: 250;
      test_scope: "isolated_disposable_postgis_smoke";
      synthetic: true;
      note: string;
    };

export type CitizenReportAggregates = ReferenceFeatureCollection<
  CitizenReportCellGeometry,
  CitizenReportCellProperties,
  "CITIZEN_REPORT_AGGREGATE" | "SYNTHETIC_AGGREGATE_FIXTURE",
  CitizenReportAggregateProvenance
> & {
  classification: "UNVERIFIED" | "SIMULATED";
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
