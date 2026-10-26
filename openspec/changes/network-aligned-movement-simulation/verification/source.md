# Source validation

Status: PASS for bounded surface-network MVP.

- Resource: OpenStreetMap API map extract, `bbox=121.528,25.028,121.532,25.032`
- Retrieved: 2026-10-23T10:08Z; the mutable API response was re-pinned and revalidated after the earlier snapshot changed.
- External artifact: `$HOME/.local/share/ratsight/network/taipei-songshan-20261023.osm`
- SHA-256: `faae4ffd1bd42e57871bdedbfdcc6e82b3324a458db95034d4ec40f0a019e67e`
- Format: OSM XML; 9,323 nodes and 1,018 ways
- Supported highway ways: 68; unique source way IDs: 68
- Ways with intermediate vertices: 49
- Missing referenced nodes: 0
- Direction tags: `oneway=yes` 38, `oneway=no` 6, absent 24
- Bridge/tunnel tags among supported ways: none in this bounded extract; absence is reported, not inferred.
- CRS: WGS84 / EPSG:4326, explicit `[longitude, latitude]` order.

Validation checks used source node references for topology. No geometric crossing, endpoint proximity, stormwater geometry, or surface/underground connection was used. The importer verifies the exact SHA-256 before parsing and fails closed on missing or mismatched bytes.

OSM data is © OpenStreetMap contributors and licensed under ODbL 1.0. Attribution and applicable database/Produced Work obligations remain required. Street geometry is a spatial modeling assumption only; it is not evidence of rodent movement.
