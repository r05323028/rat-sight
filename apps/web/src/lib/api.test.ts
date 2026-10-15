import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchAdministrativeDistricts } from "@/lib/api";

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
