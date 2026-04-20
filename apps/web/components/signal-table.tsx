import type { CSSProperties } from "react";

type Signal = {
  market: string;
  thesis: string;
  confidence: number;
  horizon: string;
};

export function SignalTable({ signals }: { signals: Signal[] }) {
  return (
    <div
      style={{
        borderRadius: "28px",
        overflow: "hidden",
        border: "1px solid rgba(148, 163, 184, 0.18)",
        background: "rgba(8, 17, 31, 0.72)"
      }}
    >
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", background: "rgba(15, 23, 42, 0.95)" }}>
            <th style={cellStyle}>Market</th>
            <th style={cellStyle}>Thesis</th>
            <th style={cellStyle}>Confidence</th>
            <th style={cellStyle}>Horizon</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((signal) => (
            <tr key={signal.market}>
              <td style={cellStyle}>{signal.market}</td>
              <td style={cellStyle}>{signal.thesis}</td>
              <td style={cellStyle}>{Math.round(signal.confidence * 100)}%</td>
              <td style={cellStyle}>{signal.horizon}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const cellStyle: CSSProperties = {
  padding: "16px 20px",
  borderBottom: "1px solid rgba(148, 163, 184, 0.08)"
};
