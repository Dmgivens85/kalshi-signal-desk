import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Kalshi Intelligence",
    short_name: "Kalshi IQ",
    description: "Mobile-first market intelligence PWA for explainable Kalshi alerts.",
    start_url: "/",
    display: "standalone",
    background_color: "#eef1f5",
    theme_color: "#f3f4f6",
    icons: []
  };
}
