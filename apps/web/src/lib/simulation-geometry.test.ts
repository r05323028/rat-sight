import { describe, expect, it } from "vitest";

import {
  flowPoints,
  pathLengthMeters,
  pointAtFraction,
  segmentLengthMeters,
  slicePathAtFraction,
} from "@/lib/simulation-geometry";

// A one-degree latitude step is ~111 km; the helper uses an equirectangular
// approximation, which is adequate for sub-kilometre city blocks.
const ROUTE: [number, number][] = [
  [121.55, 25.02],
  [121.55, 25.03],
  [121.56, 25.03],
];

describe("simulation geometry", () => {
  it("measures path length from returned coordinates instead of endpoints", () => {
    const direct = segmentLengthMeters(ROUTE[0], ROUTE[2]);
    const alongPath = pathLengthMeters(ROUTE);
    expect(alongPath).toBeGreaterThan(direct);
    // ~1112 m of latitude plus ~1007 m of longitude at 25.03 degrees.
    expect(alongPath).toBeCloseTo(1112 + 1007, 0);
  });

  it("interpolates along the polyline, not across the corner", () => {
    // The corner sits at ~1112 m of a ~2119 m path (~52%), so 75% is on the
    // east-west leg: a straight corner-to-corner interpolation would drift south.
    const point = pointAtFraction(ROUTE, 0.75)!;
    expect(point[1]).toBeCloseTo(25.03, 6);
    expect(point[0]).toBeGreaterThan(121.55);
  });

  it("returns the last coordinate for fractions beyond the route", () => {
    expect(pointAtFraction(ROUTE, 2)).toEqual(ROUTE[2]);
    expect(pointAtFraction(ROUTE, -1)).toEqual(ROUTE[0]);
  });

  it("slices a prefix that stays on the returned geometry", () => {
    const prefix = slicePathAtFraction(ROUTE, 0.75);
    expect(prefix[0]).toEqual(ROUTE[0]);
    expect(prefix[1]).toEqual(ROUTE[1]);
    expect(prefix.every(([lng]) => lng >= 121.55 && lng <= 121.56)).toBe(true);
    expect(prefix.length).toBeGreaterThanOrEqual(3);
    expect(prefix.at(-1)![1]).toBeCloseTo(25.03, 6);
  });

  it("returns a degenerate but valid line for an empty prefix", () => {
    expect(slicePathAtFraction(ROUTE, 0)).toEqual([ROUTE[0], ROUTE[0]]);
  });

  it("spaces flow points along the route and wraps by phase", () => {
    const points = flowPoints(ROUTE, 4, 0.25);
    expect(points).toHaveLength(4);
    const atStart = flowPoints(ROUTE, 4, 0)[0];
    const atEnd = flowPoints(ROUTE, 4, 1)[0];
    expect(atStart).not.toEqual(atEnd);
  });

  it("handles empty and singleton routes without inventing positions", () => {
    expect(pointAtFraction([], 0.5)).toBeNull();
    expect(slicePathAtFraction([], 0.5)).toEqual([]);
    expect(flowPoints([], 4, 0)).toEqual([]);
    expect(flowPoints([[121.55, 25.02]], 4, 0)).toEqual([]);
  });
});
