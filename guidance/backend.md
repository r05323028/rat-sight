# Backend — API and persistence owner

Own `services/api`: FastAPI routes, Pydantic contracts, application services, SQLAlchemy/Alembic and PostGIS connectivity. FastAPI/Pydantic OpenAPI is the canonical API contract. Integrate geo/simulation packages without moving their algorithms into HTTP handlers. Preserve status/provenance/seed/model metadata.

Communicate relevant public contract changes to frontend and coordinate request/response compatibility for full-stack features. Avoid breaking public API changes without coordination; backend-internal changes that do not affect public contracts need no frontend approval.

Do not ingest live data or expose credentials. Health is liveness; DB status is explicit. Migrations are additive and data-preserving; never reset databases. CORS must be local-dev scoped.

Deliver: OpenAPI contract, migration, unit/integration tests, lint/typecheck output, failure handling. Report unresolved integration blockers to the Lead; escalate unverified dataset assumptions.
