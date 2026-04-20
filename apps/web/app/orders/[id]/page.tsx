import Link from "next/link";
import { notFound } from "next/navigation";
import { getExecutionOrder } from "@kalshi/shared-ts";

export default async function OrderDetailPage({
  params
}: {
  params: { id: string };
}) {
  const order = await getExecutionOrder(params.id);
  if (!order) {
    notFound();
  }
  const risk = order.preview_payload?.risk_evaluation;

  return (
    <main className="page">
      <section className="hero">
        <Link href="/approvals" className="back-link">
          Back to approvals
        </Link>
        <p className="eyebrow">{order.market_ticker}</p>
        <h1 className="headline">
          Order <em>preview sheet</em>
        </h1>
        <p className="lede">
          {order.preview_payload?.risk_evaluation_summary ??
            "Server-side preview with deterministic risk evaluation and manual approval gating."}
        </p>
      </section>

      <section className="detail-sheet">
        <div className="sheet-handle" />
        <div className="sheet-grid">
          <div className="sheet-panel">
            <p className="sheet-label">Trade</p>
            <p className="sheet-value">
              {order.action} {order.side} {order.count} contracts at {order.price ?? order.yes_price ?? order.no_price ?? "n/a"}c.
            </p>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Approval state</p>
            <p className="sheet-value">{order.approval_status.replaceAll("_", " ")}</p>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Blocking reasons</p>
            <div className="stack-list">
              {(risk?.blocking_reasons?.length ? risk.blocking_reasons : ["No blocking reasons."]).map((item) => (
                <p className="sheet-value compact" key={item}>
                  {item}
                </p>
              ))}
            </div>
          </div>
          <div className="sheet-panel">
            <p className="sheet-label">Warnings</p>
            <div className="stack-list">
              {(risk?.warnings?.length ? risk.warnings : ["No material warnings."]).map((item) => (
                <p className="sheet-value compact" key={item}>
                  {item}
                </p>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
