import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Dashboard } from "@/components/dashboard";

vi.mock("@/components/map-view", () => ({
  MapView: () => <div role="region" aria-label="Interactive GIS map" />,
}));

function renderDashboard() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/v1/layers")) {
        return new Response(
          JSON.stringify([
            {
              id: "rodent_observations",
              label: "Rodent observations",
              available: false,
              classification: null,
              message: "No observation dataset loaded.",
            },
            {
              id: "sewer_networks",
              label: "Sewer networks",
              available: false,
              classification: null,
              message: "No sewer dataset loaded.",
            },
            {
              id: "stormwater_networks",
              label: "Stormwater networks",
              available: false,
              classification: null,
              message: "No stormwater dataset loaded.",
            },
            {
              id: "surface_corridors",
              label: "Surface movement corridors",
              available: false,
              classification: null,
              message: "No corridor dataset loaded.",
            },
            {
              id: "human_activity",
              label: "Human activity",
              available: false,
              classification: null,
              message: "No human-activity dataset loaded.",
            },
            {
              id: "environmental_conditions",
              label: "Environmental conditions",
              available: false,
              classification: null,
              message: "No environmental dataset loaded.",
            },
            {
              id: "simulated_paths",
              label: "Simulated movement paths",
              available: false,
              classification: "SIMULATED",
              message: "Available after a synthetic preview.",
            },
          ]),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(
        JSON.stringify({
          simulation_status: "completed",
          classification: "SIMULATED",
          model_id: "synthetic_weighted_random_walk",
          model_version: "0.1.0",
          parameters: {
            study_area: "taipei_synthetic_demo",
            duration_steps: 12,
            walkers: 24,
            random_seed: 42,
            movement_model: "weighted_random_walk",
            intervention_scenario: "baseline",
          },
          provenance: {
            classification: "SIMULATED",
            source_type: "synthetic_fixture",
            source_id: "ratsight-synthetic-graph-v1",
            source_crs: "EPSG:4326",
            note: "synthetic only",
          },
          assumptions: ["synthetic fixture"],
          nodes: [],
          edges: [],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }),
  );
});

afterEach(cleanup);

describe("RatSight dashboard", () => {
  it("renders map, layer controls, and simulation controls", async () => {
    renderDashboard();
    expect(screen.getByRole("heading", { name: "見光鼠" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Interactive GIS map" })).toBeInTheDocument();
    expect(screen.getByLabelText("Rodent observations")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Run synthetic preview" })).toBeInTheDocument();
    expect(screen.getByText("No real observation data loaded")).toBeInTheDocument();
  });

  it("requests and labels synthetic preview output", async () => {
    renderDashboard();
    fireEvent.click(screen.getByRole("button", { name: "Run synthetic preview" }));
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Reproducible run complete · seed 42",
    );
    expect(screen.getByText("ratsight-synthetic-graph-v1")).toBeInTheDocument();
  });
});
