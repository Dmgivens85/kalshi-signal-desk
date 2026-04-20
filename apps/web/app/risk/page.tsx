import { getRiskDashboard } from "@kalshi/shared-ts";

export default async function RiskPage() {
  const risk = await getRiskDashboard();
  const categories = Object.entries(risk.status.current_category_exposure_cents);

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Risk</p>
        <h1 className="headline">
          Guardrails <em>at a glance</em>
        </h1>
        <p className="lede">
          Deterministic controls stay separate from AI. The kill switch and exposure posture remain
          visible before any order can move beyond approval.
        </p>
      </section>

      <section className="detail-sheet">
        <div className="sheet-handle" />
        <div className="sheet-grid">
          <div className="sheet-panel">
            <p className="sheet-label">Kill switch</p>
            <p className={`sheet-value ${risk.status.kill_switch_enabled ? "status-ok" : "status-alert"}`}>
              {risk.status.kill_switch_enabled ? "Trading enabled" : "Trading disabled"}
            </p>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Open positions</p>
            <p className="sheet-value">{risk.status.current_open_positions}</p>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Exposure by category</p>
            <div className="stack-list">
              {categories.length ? (
                categories.map(([name, value]) => (
                  <p className="sheet-value compact" key={name}>
                    {name}: {value}c
                  </p>
                ))
              ) : (
                <p className="sheet-value compact">No active category exposure.</p>
              )}
            </div>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Recent risk events</p>
            <div className="stack-list">
              {risk.status.latest_risk_events.length ? (
                risk.status.latest_risk_events.map((event) => (
                  <p className="sheet-value compact" key={event.id}>
                    {event.rule_name}: {event.detail}
                  </p>
                ))
              ) : (
                <p className="sheet-value compact">No recent blocking risk events.</p>
              )}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
