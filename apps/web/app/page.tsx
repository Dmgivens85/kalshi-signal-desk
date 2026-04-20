import Link from "next/link";
import { getPlatformOverview } from "@kalshi/shared-ts";

export default async function HomePage() {
  const overview = await getPlatformOverview();

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">{overview.hero.label}</p>
        <h1 className="headline">
          Explainable <em>cross-market</em> alerts.
        </h1>
        <p className="lede">{overview.hero.summary}</p>

        <div className="hero-ribbon">
          <div className="metrics">
            {overview.metrics.map((metric) => (
              <div className="metric" key={metric.label}>
                <span className="metric-label">{metric.label}</span>
                <strong className="metric-value">{metric.value}</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <h2 className="section-title">Live signal feed</h2>
        <p className="section-copy">
          Each alert blends Kalshi pricing with external odds, forecast venues, and narrative
          catalysts, then keeps the recommendation readable enough for a fast human check.
        </p>

        <div className="feed">
          {overview.alerts.map((alert) => (
            <Link href={`/alerts/${alert.id}`} className="signal-card" key={alert.id}>
              <div className="signal-topline">
                <div>
                  <h3 className="signal-market">{alert.market_title ?? alert.market_ticker}</h3>
                  <p className="signal-ticker">{alert.market_ticker}</p>
                </div>
                <div className="confidence-pill">{Math.round(alert.confidence * 100)}%</div>
              </div>
              <p className="signal-summary">{alert.reason_summary ?? alert.thesis}</p>
              <div className="signal-meta">
                <span className={`meta-chip action-${alert.recommended_action ?? "monitor"}`}>
                  {(alert.recommended_action ?? "monitor").replace("_", " ")}
                </span>
                <span className="meta-chip">{alert.source_count} sources</span>
                <span className="meta-chip">{alert.horizon}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
