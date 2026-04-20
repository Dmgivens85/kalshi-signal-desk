import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({
    service: "web",
    status: "healthy",
    mode: process.env.NEXT_PUBLIC_EXECUTION_MODE ?? "paper"
  });
}
