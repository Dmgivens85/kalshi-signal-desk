import { getAutomationPolicies, getAutomationStatus } from "@kalshi/shared-ts";

export default async function AutomationPage() {
  const [status, policies] = await Promise.all([getAutomationStatus(), getAutomationPolicies()]);

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Automation</p>
        <h1 className="headline">
          Selective <em>automation guardrails</em>
        </h1>
        <p className="lede">
          Automation stays off by default and only runs when a narrow whitelist, stronger
          thresholds, healthy infrastructure, and deterministic risk checks all agree.
        </p>
      </section>

      <section className="detail-sheet">
        <div className="sheet-handle" />
        <div className="sheet-grid">
          <div className="sheet-panel">
            <p className="sheet-label">Global status</p>
            <p className={`sheet-value ${status.global_enabled ? "status-ok" : "status-alert"}`}>
              {status.global_enabled ? "Enabled" : "Disabled"}
            </p>
            <p className="sheet-value compact" style={{ color: "var(--muted)", marginTop: 12 }}>
              {status.blocked_reason ?? "No active block reason."}
            </p>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Mode</p>
            <p className="sheet-value">{status.global_dry_run ? "Paper / dry run" : "Live-capable"}</p>
            <p className="sheet-value compact" style={{ color: "var(--muted)", marginTop: 12 }}>
              {status.global_paused ? "Automation is paused." : "No active pause."}
            </p>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Whitelisted policies</p>
            <div className="stack-list">
              {policies.map((policy) => (
                <p className="sheet-value compact" key={policy.id}>
                  {policy.name}: {policy.is_enabled ? "enabled" : "disabled"} · {policy.max_size_bucket} max size · {Math.round(policy.min_confidence_score * 100)}% threshold
                </p>
              ))}
            </div>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Recent automation events</p>
            <div className="stack-list">
              {status.recent_events.length ? (
                status.recent_events.slice(0, 5).map((event) => (
                  <p className="sheet-value compact" key={event.id}>
                    {event.event_type}: {event.detail}
                  </p>
                ))
              ) : (
                <p className="sheet-value compact">No recent automation events.</p>
              )}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
