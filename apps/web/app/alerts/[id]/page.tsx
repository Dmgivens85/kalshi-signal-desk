import Link from "next/link";
import { notFound } from "next/navigation";
import { getSignalAlert } from "@kalshi/shared-ts";

export default async function AlertDetailPage({
  params
}: {
  params: { id: string };
}) {
  const { id } = params;
  const alert = await getSignalAlert(id);

  if (!alert) {
    notFound();
  }

  const providers = alert.feature_payload.providers ?? [];
  const scores = alert.feature_payload.scores ?? {};
  const snapshot = alert.feature_payload.market_snapshot;

  return (
    <main className="page">
      <section className="hero">
        <Link href="/alerts" className="back-link">
          Back to alerts
        </Link>
        <p className="eyebrow">{alert.market_ticker}</p>
        <h1 className="headline">
          {(alert.market_title ?? alert.market_ticker).split(" ").slice(0, 4).join(" ")}{" "}
          <em>signal sheet</em>
        </h1>
        <p className="lede">{alert.reason_summary ?? alert.thesis}</p>
      </section>

      <section className="detail-sheet">
        <div className="sheet-handle" />
        <div className="sheet-grid">
          <div className="sheet-panel">
            <p className="sheet-label">Action</p>
            <p className={`sheet-value action-${alert.recommended_action ?? "monitor"}`}>
              {(alert.recommended_action ?? "monitor").replace("_", " ")}
            </p>
            <p className="sheet-value" style={{ color: "var(--muted)", marginTop: 12 }}>
              {alert.thesis}
            </p>
          </div>

          <div className="sheet-panel">
            <p className="sheet-label">Confidence stack</p>
            <p className="sheet-value">{Math.round(alert.confidence * 100)}% overall confidence</p>
            <p className="sheet-value" style={{ color: "var(--muted)", marginTop: 12 }}>
              Market {Math.round((scores.market_price ?? 0) * 100)}%, external{" "}
              {Math.round((scores.external_consensus ?? 0) * 100)}%, gap{" "}
              {Math.round(((scores.dislocation ?? 0) * 10000)) / 100} pts.
            </p>
          </div>

          <div className="sheet-panel">
            <p className="sheet-label">Market snapshot</p>
            <p className="sheet-value">
              {snapshot?.status ?? "open"} market, last price {snapshot?.last_price ?? "n/a"}c,
              volume {snapshot?.volume ?? "n/a"}, open interest {snapshot?.open_interest ?? "n/a"}.
            </p>
          </div>

          <div className="sheet-panel">
            <p className="sheet-label">Provider evidence</p>
            <div className="provider-list">
              {providers.map((provider) => (
                <div className="provider-row" key={`${provider.provider}-${provider.title}`}>
                  <div>
                    <strong>{provider.title}</strong>
                    <div style={{ color: "var(--muted)", marginTop: 4 }}>
                      {provider.provider} via {provider.strategy}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <strong>
                      {provider.implied_probability != null
                        ? `${Math.round(provider.implied_probability * 100)}%`
                        : "Narrative"}
                    </strong>
                    <div style={{ color: "var(--muted)", marginTop: 4 }}>
                      {Math.round(provider.mapping_confidence * 100)}% map
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
