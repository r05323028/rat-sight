import { afterEach, describe, expect, it, vi } from "vitest";

import {
  taipeiLocalToUtc,
  fetchAdministrativeDistricts,
  fetchRodentReports,
  fetchStormwaterPipelines,
  isReportedRangeInvalid,
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

describe("fetchRodentReports", () => {
  const envelope = {
    type: "FeatureCollection",
    data_state: "empty",
    data_class: "RODENT_REPORT",
    classification: "SIMULATED",
    provenance: null,
    feature_count: 0,
    bbox: null,
    reported_from: null,
    reported_to: null,
    truncated: false,
    features: [],
  };

  it("requests the rodent report endpoint without filters", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify(envelope), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchRodentReports()).resolves.toEqual(envelope);
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/rodent-reports");
  });

  it("normalizes bbox and RFC3339 UTC time filters into the query", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(envelope), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await fetchRodentReports({
      bbox: [121.5, 24.98, 121.63, 25.09],
      reportedFrom: "2026-10-01T00:00:00Z",
      reportedTo: "2026-10-02T00:00:00Z",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/rodent-reports?bbox=121.5%2C24.98%2C121.63%2C25.09&reported_from=2026-10-01T00%3A00%3A00Z&reported_to=2026-10-02T00%3A00%3A00Z",
    );
  });

  it("throws when the rodent report endpoint fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("storage unavailable", { status: 503 })),
    );
    await expect(fetchRodentReports()).rejects.toThrow(/503/);
  });
});

describe("taipeiLocalToUtc", () => {
  it("converts an Asia/Taipei wall-clock value to UTC RFC3339 Z", () => {
    expect(taipeiLocalToUtc("2026-10-01T08:30")).toBe("2026-10-01T00:30:00Z");
  });

  it("rolls back across the previous day boundary", () => {
    expect(taipeiLocalToUtc("2026-10-01T07:30")).toBe("2026-09-30T23:30:00Z");
  });

  it("does not depend on the machine timezone", () => {
    const originalTimezone = process.env.TZ;
    process.env.TZ = "America/New_York";
    try {
      expect(taipeiLocalToUtc("2026-10-01T08:30")).toBe("2026-10-01T00:30:00Z");
    } finally {
      process.env.TZ = originalTimezone;
    }
  });

  it("treats empty and invalid values as absent", () => {
    expect(taipeiLocalToUtc("")).toBeNull();
    expect(taipeiLocalToUtc("not-a-date")).toBeNull();
    expect(taipeiLocalToUtc("2026-13-45T10:00")).toBeNull();
    expect(taipeiLocalToUtc("0050-01-01T00:00")).toBeNull();
  });
});

describe("isReportedRangeInvalid", () => {
  it("flags a reversed normalized UTC range", () => {
    expect(isReportedRangeInvalid("2026-10-10T00:00:00Z", "2026-10-01T00:00:00Z")).toBe(true);
  });

  it("accepts ordered or partial ranges", () => {
    expect(isReportedRangeInvalid("2026-10-01T00:00:00Z", "2026-10-10T00:00:00Z")).toBe(false);
    expect(isReportedRangeInvalid(null, "2026-10-10T00:00:00Z")).toBe(false);
    expect(isReportedRangeInvalid("2026-10-01T00:00:00Z", null)).toBe(false);
  });

  it("keeps equal boundaries valid because both ends are inclusive", () => {
    expect(isReportedRangeInvalid("2026-10-01T00:30:00Z", "2026-10-01T00:30:00Z")).toBe(false);
  });
});
