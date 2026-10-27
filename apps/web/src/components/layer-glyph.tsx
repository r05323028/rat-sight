import type { ReactNode } from "react";

// Layer rows carry authored marks instead of Unicode characters: a glyph font
// would substitute shapes across platforms and read as an emoji stand-in.
const GLYPH_PATHS: Record<string, ReactNode> = {
  administrative_boundaries: (
    <>
      <path d="M1.5 1.5h9v9h-9z" />
      <path d="M4.5 1.5v9M1.5 4.5h9" strokeDasharray="1.6 1.6" />
    </>
  ),
  stormwater: (
    <>
      <path d="M1 4.5h10M1 8h10" />
      <path d="M4.5 4.5V8M7.5 4.5V8" />
    </>
  ),
  "network-reference": (
    <>
      <path d="M2 9.5 6 2.5l4 7z" />
      <circle cx="6" cy="2.5" r="1.1" />
    </>
  ),
  sewer_networks: (
    <>
      <path d="M1.5 9.5h9" />
      <path d="M4 9.5V4h4v5.5" />
    </>
  ),
  surface_corridors: <path d="M1.5 8.5 8.5 1.5M3.5 10.5 10.5 3.5" />,
  human_activity: <path d="M2 10V6.5M6 10V2.5M10 10V7.5" />,
  environmental_conditions: (
    <>
      <circle cx="6" cy="6" r="3.4" />
      <path d="M6 2.6a3.4 3.4 0 0 1 0 6.8z" fill="currentColor" stroke="none" />
    </>
  ),
  "citizen-aggregates": (
    <>
      <path d="M1.5 1.5h3.4v3.4H1.5zM7.1 1.5h3.4v3.4H7.1zM1.5 7.1h3.4v3.4H1.5z" />
      <path d="M8.8 8.8h1.9M9.75 7.85v1.9" />
    </>
  ),
  simulated_paths: <path d="M1.5 9.5 4.5 5.5 7.5 8 10.5 2.5" strokeDasharray="2 1.4" />,
};

const DEFAULT_GLYPH = <path d="M2 2h8v8H2z" strokeDasharray="1.6 1.6" />;

export function LayerGlyph({ layerId }: { layerId: string }) {
  return (
    <span className={`layer-glyph glyph-${layerId}`} aria-hidden="true">
      <svg
        viewBox="0 0 12 12"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="square"
        focusable="false"
      >
        {GLYPH_PATHS[layerId] ?? DEFAULT_GLYPH}
      </svg>
    </span>
  );
}
