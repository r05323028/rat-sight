import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Dashboard } from "@/components/dashboard";

const mockState = vi.hoisted(() => ({
  boundaryMode: "empty" as "empty" | "available" | "error",
  stormwaterMode: "available" as "available" | "empty" | "in_view" | "truncated" | "error",
  district: {
    district_id: "63000010",
    district_name: "松山區",
    data_class: "ADMINISTRATIVE_REFERENCE",
    classification: "UNVERIFIED",
    provenance_schema_version: "1",
    dataset_id: "121199",
    resource_version: "20220915",
    archive_sha256: "a".repeat(64),
  },
  stormwaterFeature: {
    segment_id: "S-1",
    data_class: "INFRASTRUCTURE_REFERENCE",
    classification: "UNVERIFIED",
    provenance_schema_version: "1",
    dataset_id: "97b82d58-faba-4ee4-9488-dd5d04a79efd",
    resource_version: "2026-02-23T17:10:41",
    archive_sha256: "b".repeat(64),
    pipe_number: "P-1",
    material: "RCP",
  },
}));

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

const PROVENANCE = {
  schema_version: "1",
  source_url: "https://data.taipei/example",
  dataset_id: "121199",
  resource_version: "20220915",
  retrieved_at: "2026-10-15T00:00:00Z",
  archive_sha256: "a".repeat(64),
  license: "政府資料開放授權條款-第1版",
  attribution: "臺北市政府民政局",
  source_crs: "EPSG:3826",
  target_crs: "EPSG:4326",
  processing: { tool: "test", tool_version: "0", steps: ["fixture"] },
  uncertainty: { currentness: "UNVERIFIED after 2022-09-15", note: "fixture" },
};

const STORMWATER_PROVENANCE = {
  schema_version: "1",
  source_url: "https://data.taipei/stormwater",
  download_url: "https://data.taipei/stormwater/download",
  dataset_id: "97b82d58-faba-4ee4-9488-dd5d04a79efd",
  resource_id: "5240223d-5187-454e-b323-63443a195639",
  resource_version: "2026-02-23T17:10:41",
  retrieved_at: "2026-10-16T16:58:44Z",
  archive_sha256: "b".repeat(64),
  license: "政府資料開放授權條款-第1版",
  attribution: "臺北市政府工務局",
  source_crs: "EPSG:3826",
  target_crs: "EPSG:4326",
  z_handling: "dropped",
  processing: { tool: "test", tool_version: "0", steps: ["fixture"] },
  source_quality: {
    reference_only: true,
    missing_pipe_number_count: 20,
    duplicate_pipe_number_value_count: 311,
    missing_start_endpoint_count: 991,
    missing_end_endpoint_count: 991,
    missing_notes_count: 17950,
  },
  uncertainty: { currentness: "Publisher reference-only; currentness UNVERIFIED", note: "fixture" },
};

beforeEach(() => {
  mockState.boundaryMode = "empty";
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
      if (url.endsWith("/api/v1/administrative-districts")) {
        if (mockState.boundaryMode === "error") {
          return new Response("storage unavailable", { status: 503 });
        }
        const features =
          mockState.boundaryMode === "available"
            ? [
                {
                  type: "Feature",
                  id: mockState.district.district_id,
                  geometry: {
                    type: "Polygon",
                    coordinates: [
                      [
                        [121.55, 25.02],
                        [121.58, 25.02],
                        [121.58, 25.06],
                        [121.55, 25.02],
                      ],
                    ],
                  },
                  properties: mockState.district,
                },
              ]
            : [];
        return new Response(
          JSON.stringify({
            type: "FeatureCollection",
            data_state: features.length > 0 ? "available" : "empty",
            data_class: "ADMINISTRATIVE_REFERENCE",
            provenance: features.length > 0 ? PROVENANCE : null,
            features,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      if (url.includes("/api/v1/stormwater-pipelines")) {
        if (mockState.stormwaterMode === "error") {
          return new Response("storage unavailable", { status: 503 });
        }
        const features =
          mockState.stormwaterMode === "empty" || mockState.stormwaterMode === "in_view"
            ? []
            : [
                {
                  type: "Feature",
                  id: mockState.stormwaterFeature.segment_id,
                  geometry: {
                    type: "LineString",
                    coordinates: [
                      [121.55, 25.02],
                      [121.58, 25.06],
                    ],
                  },
                  properties: mockState.stormwaterFeature,
                },
              ];
        return new Response(
          JSON.stringify({
            type: "FeatureCollection",
            data_state: mockState.stormwaterMode === "empty" ? "empty" : "available",
            data_class: "INFRASTRUCTURE_REFERENCE",
            provenance: mockState.stormwaterMode === "empty" ? null : STORMWATER_PROVENANCE,
            feature_count: features.length,
            bbox: [121.5, 24.98, 121.63, 25.09],
            truncated: mockState.stormwaterMode === "truncated",
            features,
          }),
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

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

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

  it("shows the empty administrative boundary state without fabricating geometry", async () => {
    renderDashboard();
    const reference = screen.getByRole("region", {
      name: "Administrative reference inspection",
    });
    expect(await within(reference).findByText("No boundaries imported")).toBeInTheDocument();
    expect(screen.getByLabelText("Administrative districts")).toBeDisabled();
  });

  it("selects a district through the keyboard-accessible list and shows provenance", async () => {
    mockState.boundaryMode = "available";
    renderDashboard();
    const toggle = await screen.findByLabelText("Administrative districts");
    await waitFor(() => expect(toggle).toBeEnabled());
    expect(toggle).not.toBeChecked();
    fireEvent.click(toggle);
    expect(toggle).toBeChecked();

    const districtButton = screen.getByRole("button", { name: "松山區" });
    districtButton.focus();
    expect(districtButton).toHaveFocus();
    fireEvent.click(districtButton);
    expect(districtButton).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("63000010")).toBeInTheDocument();
    expect(screen.getByText("121199")).toBeInTheDocument();

    const sourceLink = screen.getByRole("link", { name: "https://data.taipei/example" });
    expect(sourceLink).toHaveAttribute("href", "https://data.taipei/example");
    expect(sourceLink).toHaveAttribute("target", "_blank");
    expect(sourceLink).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.getByText("臺北市政府民政局")).toBeInTheDocument();
    expect(screen.getByText("UNVERIFIED after 2022-09-15")).toBeInTheDocument();
  });

  it("communicates an unavailable boundary service", async () => {
    mockState.boundaryMode = "error";
    renderDashboard();
    const reference = screen.getByRole("region", {
      name: "Administrative reference inspection",
    });
    expect(await within(reference).findByText("Boundary service unavailable")).toBeInTheDocument();
    expect(screen.getByLabelText("Administrative districts")).toBeDisabled();
  });

  it("reports the storage-empty stormwater state", async () => {
    mockState.stormwaterMode = "empty";
    renderDashboard();
    expect(await screen.findByText("No pipelines imported")).toBeInTheDocument();
    expect(
      await screen.findByText("No stormwater pipelines have been imported."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Stormwater pipelines")).toBeDisabled();
  });

  it("distinguishes an in-view miss from an empty store", async () => {
    mockState.stormwaterMode = "in_view";
    renderDashboard();
    const panel = screen.getByRole("region", { name: "Stormwater pipeline inspection" });
    expect(await within(panel).findByText("No pipelines in view")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("Stormwater pipelines")).toBeEnabled());
  });

  it("shows the capped partial-data state", async () => {
    mockState.stormwaterMode = "truncated";
    renderDashboard();
    const panel = screen.getByRole("region", { name: "Stormwater pipeline inspection" });
    expect(await within(panel).findByText("Showing partial data · zoom in")).toBeInTheDocument();
  });

  it("communicates an unavailable stormwater service", async () => {
    mockState.stormwaterMode = "error";
    renderDashboard();
    const panel = screen.getByRole("region", { name: "Stormwater pipeline inspection" });
    expect(await within(panel).findByText("Stormwater service unavailable")).toBeInTheDocument();
    expect(screen.getByLabelText("Stormwater pipelines")).toBeDisabled();
  });

  it("inspects a selected stormwater pipeline with reference-only provenance", async () => {
    mockState.stormwaterMode = "available";
    renderDashboard();
    const toggle = await screen.findByLabelText("Stormwater pipelines");
    await waitFor(() => expect(toggle).toBeEnabled());
    fireEvent.click(toggle);
    expect(toggle).toBeChecked();

    const segmentButton = screen.getByRole("button", { name: "S-1" });
    segmentButton.focus();
    expect(segmentButton).toHaveFocus();
    fireEvent.click(segmentButton);
    expect(segmentButton).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("RCP")).toBeInTheDocument();
    expect(screen.getByText("Source Z dropped — no documented vertical CRS")).toBeInTheDocument();
    expect(screen.getByText(/Not verified physical connectivity/)).toBeInTheDocument();
    expect(screen.getByText(/Publisher reference-only warning/)).toBeInTheDocument();
    const sourceLink = screen.getByRole("link", { name: "https://data.taipei/stormwater" });
    expect(sourceLink).toHaveAttribute("target", "_blank");
    expect(sourceLink).toHaveAttribute("rel", "noopener noreferrer");
  });
});
