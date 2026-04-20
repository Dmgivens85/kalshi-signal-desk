import Link from "next/link";
import { getPendingApprovals } from "@kalshi/shared-ts";

export default async function ApprovalsPage() {
  const approvals = await getPendingApprovals();

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Approvals</p>
        <h1 className="headline">
          Manual <em>approval queue</em>
        </h1>
        <p className="lede">
          Every proposed trade stays human-approved in v1. Review the risk summary, scan the signal
          reason, and decide from a clean mobile queue.
        </p>
      </section>

      <div className="feed">
        {approvals.map((order) => (
          <Link href={`/orders/${order.id}`} className="signal-card" key={order.id}>
            <div className="signal-topline">
              <div>
                <h2 className="signal-market">{order.market_ticker}</h2>
                <p className="signal-ticker">{order.approval_status.replaceAll("_", " ")}</p>
              </div>
              <div className="confidence-pill">{order.size_bucket ?? "small"}</div>
            </div>
            <p className="signal-summary">
              {order.preview_payload?.supporting_signal_summary ??
                order.preview_payload?.risk_evaluation_summary ??
                "Deterministic preview ready for mobile review."}
            </p>
            <div className="signal-meta">
              <span className="meta-chip">{order.action} {order.side}</span>
              <span className="meta-chip">{order.count} contracts</span>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
