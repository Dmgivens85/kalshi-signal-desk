import type { Metadata, Viewport } from "next";
import { Instrument_Serif, Manrope } from "next/font/google";
import type { ReactNode } from "react";
import { BottomNav } from "../components/bottom-nav";
import { ModeBanner } from "../components/mode-banner";
import "./globals.css";

const sans = Manrope({
  subsets: ["latin"],
  variable: "--font-sans"
});

const serif = Instrument_Serif({
  subsets: ["latin"],
  variable: "--font-serif",
  weight: "400"
});

export const metadata: Metadata = {
  title: "Kalshi Intelligence",
  description: "Mobile-first PWA for explainable market alerts and external consensus.",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Kalshi Intelligence"
  }
};

export const viewport: Viewport = {
  themeColor: "#f3f4f6",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1
};

export default function RootLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${sans.variable} ${serif.variable}`}>
        <div className="app-shell">
          <ModeBanner />
          {children}
          <BottomNav />
        </div>
      </body>
    </html>
  );
}
