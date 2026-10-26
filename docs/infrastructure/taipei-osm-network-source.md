# Bounded Taipei OSM network source

## Pinned source

The network MVP uses one bounded OpenStreetMap API map extract, kept outside Git:

- Resource: `https://api.openstreetmap.org/api/0.6/map?bbox=121.528,25.028,121.532,25.032`
- Coverage: bounded EPSG:4326 longitude/latitude bbox; coverage is an extract, not a city-wide inventory.
- Retrieval: 2026-10-23T10:08Z (source response was re-pinned after the mutable API resource changed)
- Local path: `$RATSIGHT_OSM_SOURCE` (default `$HOME/.local/share/ratsight/network/taipei-songshan-20261023.osm`)
- SHA-256: `faae4ffd1bd42e57871bdedbfdcc6e82b3324a458db95034d4ec40f0a019e67e`
- Format: OSM XML; 9,323 nodes and 1,018 ways in the downloaded extract.
- Native CRS/axis order: WGS84 / EPSG:4326, normalized as `[longitude, latitude]` for GeoJSON and MapLibre.

The resource is OpenStreetMap data from a mutable API endpoint; this exact byte snapshot is pinned locally, but later retrievals may fail closed until a new reviewed contract is recorded. © OpenStreetMap contributors, licensed under ODbL 1.0. Any distribution must retain attribution and comply with ODbL database/Produced Work obligations. This source does not establish that rodents use streets and is not biological evidence.

## Graph rules

Only ways tagged with a supported `highway` value are loaded. Graph nodes are OSM node IDs. Directed edges are split at consecutive OSM nodes and retain every original way coordinate, source way ID, tags, and LineString coordinates. The extract-level timestamp and checksum are pinned; per-way version attributes are not exposed by this adapter. Connectivity comes only from shared OSM node references. Geometric crossings, proximity, and clipped-boundary endpoints never create connections. `oneway=yes`, `oneway=-1`, and roundabouts are handled explicitly; missing access/direction tags remain unknown and do not become biological or traversability claims. Bridges and tunnels retain separate layer metadata.

The graph is a spatial reference for a synthetic, uncalibrated random walk. Outputs remain `SIMULATED`; they are not observed movement, prevalence, risk, or validation.

## Reproduction

```sh
# Place the approved byte snapshot at this path through the project artifact channel.
mkdir -p "$HOME/.local/share/ratsight/network"
cp /path/to/approved/taipei-songshan-20261023.osm \
  "$HOME/.local/share/ratsight/network/taipei-songshan-20261023.osm"
./scripts/fetch_taipei_osm_source.sh
```

The importer fails closed when the file is missing or its SHA-256 differs from the pinned value. No stormwater geometry is used as topology, and no underground traversal is implemented.
