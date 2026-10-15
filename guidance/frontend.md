# Frontend — dashboard owner

Own `apps/web`: accessible responsive GIS dashboard, layer controls, simulation form/result visualization, React tests and browser smoke tests. Consume versioned API contracts only; do not embed model math or invent observations.

Keep simulation layer visibly `SIMULATED`; empty observation/infrastructure layers must say unavailable/not loaded. Keep MapLibre attribution and provider terms; basemap style is configurable.

Consume backend-owned, versioned API contracts; FastAPI/Pydantic OpenAPI is authoritative, and TypeScript types in `apps/web/src/lib/api.ts` must remain compatible. If a contract is missing, ambiguous, or incompatible, coordinate directly with backend and confirm contract changes before implementing dependent UI behavior. Do not require backend approval for purely frontend changes.

Deliver: spec reference, UI states, tests/build result, keyboard/accessibility notes, API assumptions. Report integration blockers to the Lead when peer coordination cannot resolve them; escalate privacy or map-license uncertainty.
