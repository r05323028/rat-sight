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
  processing: { tool: string; tool_version: string; steps: string[] };
  uncertainty: { currentness: string; note: string };
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

export type AdministrativeDistricts = {
  type: "FeatureCollection";
  data_state: "empty" | "available";
  data_class: "ADMINISTRATIVE_REFERENCE";
  provenance: AdministrativeDistrictProvenance | null;
  features: AdministrativeDistrictFeature[];
};

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
