import { getPositions } from "@kalshi/shared-ts";

export default async function PositionsPage() {
  const positions = await getPositions();

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Positions</p>
        <h1 className="headline">
          Open <em>exposure view</em>
        </h1>
        <p className="lede">
          Review current exposure by market and category without clutter. This page is tuned for a
          fast check from an iPhone.
        </p>
      </section>

      <section className="detail-sheet">
        <div className="sheet-handle" />
        <div className="provider-list">
          {positions.map((position) => (
            <div className="provider-row" key={position.id}>
              <div>
                <strong>{position.market_ticker}</strong>
                <div style={{ color: "var(--muted)", marginTop: 4 }}>
                  {position.contracts_count} contracts · {position.side ?? "mixed"}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <strong>{position.exposure_cents}c</strong>
                <div style={{ color: "var(--muted)", marginTop: 4 }}>
                  PnL {position.unrealized_pnl_cents >= 0 ? "+" : ""}
                  {position.unrealized_pnl_cents}c
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
