# Initial architecture decisions

1. **Monorepo, modular boundaries.** One Next.js app, one FastAPI service and two independent Python packages minimize startup cost while allowing separate tests. No microservices, queue, Redis, Kafka or graph database.
2. **PostGIS as spatial store.** PostgreSQL/PostGIS supports relational provenance and geometries in the same local service; migrations own schema evolution. No database reset workflow.
3. **CRS is explicit.** Utilities accept source and target CRS; EPSG:4326 is API/map interchange, EPSG:3826 is a supported projected CRS. Never assume all source data uses one CRS.
4. **Synthetic preview only.** A seeded weighted graph exercises the vertical path without fabricating municipal observations. Result classification and assumptions travel end-to-end.
5. **Evidence-first workflow.** OpenSpec's installed spec-driven schema is forked locally as evidence-driven. Research review, scientific assumption approval, independent review, validation and traceability are coordinated by role guidance because schema stages may not enforce them.
6. **Pi seat isolation.** OpenRig owns seat sessions and writable state. Explicit symlinks share selected read-only/global configuration; no session/history/memory sharing, no settings.json symlink, no copied secrets.
