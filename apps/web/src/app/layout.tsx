import type { Metadata } from "next";

import { AppProviders } from "@/components/app-providers";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "見光鼠 RatSight · 都市鼠類移動分析",
  description: "具證據意識的都市鼠類移動模擬與市政決策支援。",
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
