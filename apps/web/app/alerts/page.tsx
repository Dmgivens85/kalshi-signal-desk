import Link from "next/link";
import { getSignalFeed } from "@kalshi/shared-ts";

export default async function AlertsPage() {
  const alerts = await getSignalFeed();

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Alerts</p>
        <h1 className="headline">
          Deep-linkable <em>alerts</em> for mobile review.
        </h1>
        <p className="lede">
          Open any signal as a shareable detail page with feature payloads, provider evidence,
          pricing gaps, and the current recommended action.
        </p>
      </section>

      <div className="feed">
        {alerts.map((alert) => (
          <Link href={`/alerts/${alert.id}`} className="signal-card" key={alert.id}>
            <div className="signal-topline">
              <div>
                <h2 className="signal-market">{alert.market_title ?? alert.market_ticker}</h2>
                <p className="signal-ticker">{alert.market_ticker}</p>
              </div>
              <div className="confidence-pill">{Math.round(alert.confidence * 100)}%</div>
            </div>
            <p className="signal-summary">{alert.thesis}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
