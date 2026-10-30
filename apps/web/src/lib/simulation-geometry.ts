// Geometric helpers for simulatcd-route animation.
//
// The simulation returns city-block LineStrings in EPSG:4326. Playback must
// follow those coordinates, never a straight shortcut between endpoints, so
// interpolation happens along the returned polyline by arc length. Distances
// use an equirectangular approximation, which is accurate enough at the
// sub-kilometre scale of one 250 m origin cell; it is a presentation helper,
// not a geodesic measurement.

export type LngLat = [number, number];

const EARTH_RADIUS_METERS = 6_371_008.8;

export function segmentLengthMeters(a: LngLat, b: LngLat): number {
  const meanLatitude = ((a[1] + b[1]) / 2) * (Math.PI / 180);
  const eastWest = (b[0] - a[0]) * (Math.PI / 180) * Math.cos(meanLatitude) * EARTH_RADIUS_METERS;
  const northSouth = (b[1] - a[1]) * (Math.PI / 180) * EARTH_RADIUS_METERS;
  return Math.hypot(eastWest, northSouth);
}

export function pathLengthMeters(coordinates: LngLat[]): number {
  let total = 0;
  for (let index = 1; index < coordinates.length; index += 1) {
    total += segmentLengthMeters(coordinates[index - 1], coordinates[index]);
  }
  return total;
}

export function clampFraction(fraction: number): number {
  if (!Number.isFinite(fraction)) return 0;
  return Math.min(1, Math.max(0, fraction));
}

// Returns the coordinate at a fraction of the path's length. A path with no
// length (missing or duplicated coordinates) falls back to its first point
// instead of inventing a position.
export function pointAtFraction(coordinates: LngLat[], fraction: number): LngLat | null {
  if (coordinates.length === 0) return null;
  if (coordinates.length === 1) return coordinates[0];
  const total = pathLengthMeters(coordinates);
  if (total === 0) return coordinates[0];
  const target = clampFraction(fraction) * total;
  let travelled = 0;
  for (let index = 1; index < coordinates.length; index += 1) {
    const length = segmentLengthMeters(coordinates[index - 1], coordinates[index]);
    if (travelled + length >= target) {
      const within = length === 0 ? 0 : (target - travelled) / length;
      const [startX, startY] = coordinates[index - 1];
      const [endX, endY] = coordinates[index];
      return [startX + (endX - startX) * within, startY + (endY - startY) * within];
    }
    travelled += length;
  }
  return coordinates[coordinates.length - 1];
}

// Prefix of the path up to (and including) the interpolated point. Used to draw
// the already-traversed part of a walker's route.
export function slicePathAtFraction(coordinates: LngLat[], fraction: number): LngLat[] {
  if (coordinates.length === 0) return [];
  const total = pathLengthMeters(coordinates);
  const target = clampFraction(fraction) * total;
  if (total === 0) return [coordinates[0], coordinates[0]];
  if (target <= 0) return [coordinates[0], coordinates[0]];
  const slice: LngLat[] = [coordinates[0]];
  let travelled = 0;
  for (let index = 1; index < coordinates.length; index += 1) {
    const length = segmentLengthMeters(coordinates[index - 1], coordinates[index]);
    if (travelled + length <= target) {
      slice.push(coordinates[index]);
      travelled += length;
      continue;
    }
    const within = length === 0 ? 0 : (target - travelled) / length;
    const [startX, startY] = coordinates[index - 1];
    const [endX, endY] = coordinates[index];
    slice.push([startX + (endX - startX) * within, startY + (endY - startY) * within]);
    break;
  }
  // A LineString needs at least two positions; a zero-length prefix is drawn as
  // a short duplicate pair so the point stays visible without implying travel.
  return slice.length === 1 ? [slice[0], slice[0]] : slice;
}

// Evenly spaced flow markers along a route, offset by a looping phase. The
// markers travel along the directed edge they belong to, so a two-way street is
// animated in both directions rather than falsely presented as one-way.
export function flowPoints(coordinates: LngLat[], count: number, phase: number): LngLat[] {
  if (coordinates.length < 2 || count <= 0) return [];
  const points: LngLat[] = [];
  const total = pathLengthMeters(coordinates);
  if (total === 0) return [];
  const shift = (clampFraction(phase) - 0.5) / count;
  for (let index = 0; index < count; index += 1) {
    const fraction = (((index / count + shift) % 1) + 1) % 1;
    const point = pointAtFraction(coordinates, fraction);
    if (point) points.push(point);
  }
  return points;
}
