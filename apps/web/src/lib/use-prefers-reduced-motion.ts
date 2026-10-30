"use client";

import { useSyncExternalStore } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";

function subscribe(callback: () => void): () => void {
  if (typeof window.matchMedia !== "function") return () => {};
  const query = window.matchMedia(QUERY);
  query.addEventListener("change", callback);
  return () => query.removeEventListener("change", callback);
}

function getSnapshot(): boolean {
  if (typeof window.matchMedia !== "function") return false;
  return window.matchMedia(QUERY).matches;
}

// The server cannot observe a user motion preference; the first client snapshot
// is the one that matters, and no animation is committed to the static SSR HTML.
function getServerSnapshot(): boolean {
  return false;
}

// Presentation-only motion preference. Animation never carries data meaning, so
// this hook is not a scientific or accessibility authority beyond the OS setting.
export function usePrefersReducedMotion(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
