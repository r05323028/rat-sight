# Design

The smoke harness will clear only its disposable database using the existing compose project and a privileged fixture reset path that cannot be used by the production importer/API. The rodent-report immutability trigger remains enabled in all application migrations and runtime paths. Cleanup remains project-scoped and must verify no shared developer resources were touched.

The rodent-report table and model will require `classification='SIMULATED'`. The application will validate persisted rows and provenance before serializing; inconsistent classification raises an explicit data-contract error rather than relabeling. A forward migration is used if needed for databases that already applied `0004`.

The dashboard will render at most 100 report inspection buttons, show a limitation notice, and retain the complete GeoJSON source for map rendering. Selection is derived from current features so a map-selected feature outside the auxiliary list remains inspectable. A temporal range validator runs before query construction; invalid `from > to` disables the query and displays a validation message. Existing UTC API semantics remain unchanged.
