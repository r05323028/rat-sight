import type { Metadata } from "next";

import { AppProviders } from "@/components/app-providers";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "見光鼠 RatSight · Urban movement analysis",
  description: "Evidence-aware urban rodent movement simulation and municipal decision support.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-Hant">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
