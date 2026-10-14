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
