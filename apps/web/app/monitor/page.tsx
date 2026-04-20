import { getSignalFeed } from "@kalshi/shared-ts";

export default async function MonitorPage() {
  const alerts = await getSignalFeed();
  const actions = {
    buyYes: alerts.filter((item) => item.recommended_action === "buy_yes").length,
    buyNo: alerts.filter((item) => item.recommended_action === "buy_no").length,
    monitor: alerts.filter((item) => item.recommended_action === "monitor").length
  };

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Monitor</p>
        <h1 className="headline">
          Signal <em>operating view</em>
        </h1>
        <p className="lede">
          A restrained mobile control surface for seeing how many alerts are actionable now versus
          still worth human monitoring.
        </p>
      </section>

      <section className="detail-sheet">
        <div className="sheet-handle" />
        <div className="sheet-grid">
          <div className="sheet-panel">
            <p className="sheet-label">Buy yes</p>
            <p className="sheet-value">{actions.buyYes} alerts currently clear the yes-action threshold.</p>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Buy no</p>
            <p className="sheet-value">{actions.buyNo} alerts currently clear the no-action threshold.</p>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Monitor</p>
            <p className="sheet-value">{actions.monitor} alerts still need a tighter spread or fresher evidence.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
