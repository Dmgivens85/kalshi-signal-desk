import { getPaperOrders, getPaperPerformance, getPaperPositions, getPaperStatus, getSimulationRuns } from "@kalshi/shared-ts";

export default async function PaperPage() {
  const [status, orders, positions, performance, runs] = await Promise.all([
    getPaperStatus(),
    getPaperOrders(),
    getPaperPositions(),
    getPaperPerformance(),
    getSimulationRuns()
  ]);

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Paper Trading</p>
        <h1 className="headline">
          Safe <em>simulation desk</em>
        </h1>
        <p className="lede">
          Real Kalshi market data, real signals, real alerts, simulated orders. This surface is for
          validating behavior before any live deployment.
        </p>
      </section>

      <section className="detail-sheet">
        <div className="sheet-handle" />
        <div className="sheet-grid">
          <div className="sheet-panel">
            <p className="sheet-label">Mode</p>
            <p className={`sheet-value ${status.mode === "paper" ? "status-ok" : "status-alert"}`}>
              {status.mode}
            </p>
            <p className="sheet-value compact" style={{ color: "var(--muted)", marginTop: 12 }}>
              Paper-only labeling is always shown to avoid confusion with live activity.
            </p>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Performance</p>
            <p className="sheet-value">
              Realized {performance.realized_pnl_cents}c · Unrealized {performance.unrealized_pnl_cents}c
            </p>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Paper positions</p>
            <div className="stack-list">
              {positions.slice(0, 4).map((position) => (
                <p className="sheet-value compact" key={position.id}>
                  {position.market_ticker}: {position.contracts_count} contracts at {position.average_entry_price}c
                </p>
              ))}
            </div>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Recent simulation runs</p>
            <div className="stack-list">
              {runs.slice(0, 4).map((run) => (
                <p className="sheet-value compact" key={run.id}>
                  {run.name}: {run.status}
                </p>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section>
        <h2 className="section-title">Recent paper orders</h2>
        <div className="feed">
          {orders.slice(0, 5).map((order) => (
            <div className="signal-card" key={order.id}>
              <div className="signal-topline">
                <div>
                  <h3 className="signal-market">{order.market_ticker}</h3>
                  <p className="signal-ticker">paper only</p>
                </div>
                <div className="confidence-pill">{order.status}</div>
              </div>
              <p className="signal-summary">
                {order.action} {order.side} {order.requested_count} contracts, filled {order.filled_count} at{" "}
                {order.simulated_average_fill_price ?? order.reference_price ?? "n/a"}c.
              </p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
