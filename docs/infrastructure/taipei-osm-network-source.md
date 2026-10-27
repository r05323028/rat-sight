# Bounded Taipei OSM network source

## Pinned source

The network MVP uses one bounded OpenStreetMap surface extract, kept outside Git:

- Resource: an Overpass API query against `https://overpass-api.de/api/interpreter`. It requests `way["highway"](s,w,n,e)` for 30 clustered study-area bboxes around the 91 published Rat Radar aggregate cells, each expanded by 500 m, followed by `(._;>;);out body;`.
- Coverage: the union of those neighborhoods, EPSG:4326 bbox `121.2786025,24.9821164,121.6725037,25.1249122`. Coverage is bounded and clustered, not a continuous city-wide inventory.
- Retrieval: fetched 2026-10-27; OSM base timestamp `2026-10-27T13:20:28Z`.
- Local path: `$RATSIGHT_OSM_SOURCE` (default `$HOME/.local/share/ratsight/network/taipei-expanded-ratdar-20261027.osm`)
- SHA-256: `9db94dd723445fb45e73a77dca4ee4a74783af26e04794fc3fc9d5f63aa0f868`
- Format: OSM XML; 139,865 nodes and 43,031 ways in the downloaded extract; after highway filtering the routable graph has 71,281 nodes, 185,503 edges, and 387 weakly connected components (largest 54,828 nodes).
- Published-cell coverage: all 91 cells in the current aggregate dataset contain at least one eligible graph node (minimum 3, median 60, maximum 286).
- Native CRS/axis order: WGS84 / EPSG:4326, normalized as `[longitude, latitude]` for GeoJSON and MapLibre.

The resource is OpenStreetMap data from a mutable API endpoint; this exact byte snapshot is pinned locally, but later retrievals may fail closed until a new reviewed contract is recorded. © OpenStreetMap contributors, licensed under ODbL 1.0. Any distribution must retain attribution and comply with ODbL database/Produced Work obligations. This source does not establish that rodents use streets and is not biological evidence.

## Graph rules

Only ways tagged with a supported `highway` value are loaded. Graph nodes are OSM node IDs. Directed edges are split at consecutive OSM nodes and retain every original way coordinate, source way ID, tags, and LineString coordinates. The extract-level timestamp and checksum are pinned; per-way version attributes are not exposed by this adapter. Connectivity comes only from shared OSM node references. Geometric crossings, proximity, and clipped-boundary endpoints never create connections. `oneway=yes`, `oneway=-1`, and roundabouts are handled explicitly; missing access/direction tags remain unknown and do not become biological or traversability claims. Bridges and tunnels retain separate layer metadata.

The graph is a spatial reference for a synthetic, uncalibrated random walk. Outputs remain `SIMULATED`; they are not observed movement, prevalence, risk, or validation.

The parser caches the immutable graph in process, keyed by path, pinned SHA-256, and file modification time. Callers MUST treat the returned graph as read-only; revisiting the 26 MB snapshot does not repeat XML parsing.

For an explicitly selected aggregate cell, every graph node strictly inside the cell polygon is eligible. One candidate uses `strict-in-cell-v1`; more than one candidate uses `uniform-in-cell-v1`, and each walker starts uniformly from that set with the seeded RNG. Zero candidates fail closed. The cell still does not identify one observed animal location, and the uniform-start rule has not been scientifically approved.

## Map visualization subset

Simulation and reachability always run on the full model graph. To keep interactive map payloads usable, the preview API may return a `local_reference` subset: all origin nodes, all nodes touched by returned trajectories, nodes within 750 m of the representative origin, and edges among those nodes. The response's `visualization` object records the mode, radius, returned node/edge counts, and full graph totals. The subset is a drawing aid, not reduced model coverage; the dashboard shows full-graph reachability totals and labels the local subset.

## Reproduction

```sh
# Place the pinned byte snapshot at this path through the project artifact channel.
mkdir -p "$HOME/.local/share/ratsight/network"
cp /path/to/pinned/taipei-expanded-ratdar-20261027.osm \
  "$HOME/.local/share/ratsight/network/taipei-expanded-ratdar-20261027.osm"
./scripts/fetch_taipei_osm_source.sh
```

The importer fails closed when the file is missing or its SHA-256 differs from the pinned value. No stormwater geometry is used as topology, and no underground traversal is implemented.
