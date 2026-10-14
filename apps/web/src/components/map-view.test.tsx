import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const mapConstructor = vi.hoisted(() => vi.fn());
vi.mock("maplibre-gl", () => ({
  setWorkerUrl: vi.fn(),
  Map: class {
    constructor(options: unknown) {
      mapConstructor(options);
    }
    addControl = vi.fn();
    once = vi.fn();
    on = vi.fn();
    off = vi.fn();
    isStyleLoaded = () => false;
    remove = vi.fn();
  },
  NavigationControl: class {},
}));

import { MapView } from "@/components/map-view";

describe("MapView", () => {
  it("initializes an interactive MapLibre map with configured basemap and attribution", () => {
    render(<MapView preview={null} showSimulatedPaths={false} />);
    expect(screen.getByRole("region", { name: "Interactive GIS map" })).toBeInTheDocument();
    expect(mapConstructor).toHaveBeenCalledWith(
      expect.objectContaining({
        style: expect.stringContaining("style.json"),
        center: [121.5654, 25.033],
        attributionControl: {},
      }),
    );
  });
});
