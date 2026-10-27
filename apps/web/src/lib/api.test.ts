import { afterEach, describe, expect, it, vi } from "vitest";

import {
  fetchAdministrativeDistricts,
  fetchStormwaterPipelines,
  isStormwaterBboxTooBroad,
} from "@/lib/api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("fetchAdministrativeDistricts", () => {
  it("requests the administrative districts endpoint and parses the envelope", async () => {
    const envelope = {
      type: "FeatureCollection",
      data_state: "empty",
      data_class: "ADMINISTRATIVE_REFERENCE",
      provenance: null,
      features: [],
    };
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify(envelope), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchAdministrativeDistricts()).resolves.toEqual(envelope);
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/administrative-districts");
  });

  it("throws when the boundary endpoint fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("storage unavailable", { status: 503 })),
    );
    await expect(fetchAdministrativeDistricts()).rejects.toThrow(/503/);
  });
});

describe("fetchStormwaterPipelines", () => {
  it("requests the stormwater endpoint without a bbox", async () => {
    const envelope = {
      type: "FeatureCollection",
      data_state: "empty",
      data_class: "INFRASTRUCTURE_REFERENCE",
      provenance: null,
      feature_count: 0,
      bbox: null,
      truncated: false,
      features: [],
    };
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify(envelope), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchStormwaterPipelines()).resolves.toEqual(envelope);
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/stormwater-pipelines");
  });

  it("passes the viewport bbox as a minX,minY,maxX,maxY query parameter", async () => {
    const envelope = {
      type: "FeatureCollection",
      data_state: "available",
      data_class: "INFRASTRUCTURE_REFERENCE",
      provenance: null,
      feature_count: 0,
      bbox: [121.5, 24.98, 121.63, 25.09],
      truncated: false,
      features: [],
    };
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(envelope), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await fetchStormwaterPipelines([121.5, 24.98, 121.63, 25.09]);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/stormwater-pipelines?bbox=121.5,24.98,121.63,25.09",
    );
  });

  it("throws when the bbox query is rejected", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("invalid bbox", { status: 422 })),
    );
    await expect(fetchStormwaterPipelines([121.5, 24.98, 121.63, 25.09])).rejects.toThrow(/422/);
  });
});

describe("isStormwaterBboxTooBroad", () => {
  it("accepts the documented 0.30 degree viewport limit", () => {
    expect(isStormwaterBboxTooBroad([121.5, 24.98, 121.63, 25.09])).toBe(false);
  });

  it("rejects spans wider or taller than 0.30 degrees", () => {
    expect(isStormwaterBboxTooBroad([121.4, 24.98, 121.71, 25.09])).toBe(true);
    expect(isStormwaterBboxTooBroad([121.5, 24.9, 121.63, 25.21])).toBe(true);
  });
});
