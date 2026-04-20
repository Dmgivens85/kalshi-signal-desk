type OverviewItem = {
  label: string;
  value: string;
};

export function OverviewCard({
  eyebrow,
  title,
  items
}: {
  eyebrow: string;
  title: string;
  items: OverviewItem[];
}) {
  return (
    <aside
      style={{
        padding: "24px",
        borderRadius: "28px",
        background: "linear-gradient(180deg, rgba(15, 23, 42, 0.95), rgba(8, 17, 31, 0.92))",
        border: "1px solid rgba(52, 211, 153, 0.16)",
        boxShadow: "0 20px 60px rgba(0, 0, 0, 0.25)"
      }}
    >
      <p style={{ margin: "0 0 10px", color: "#34d399", textTransform: "uppercase", letterSpacing: "0.16em" }}>
        {eyebrow}
      </p>
      <h2 style={{ margin: "0 0 18px" }}>{title}</h2>
      <div style={{ display: "grid", gap: "12px" }}>
        {items.map((item) => (
          <div
            key={item.label}
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: "12px",
              paddingBottom: "12px",
              borderBottom: "1px solid rgba(148, 163, 184, 0.12)"
            }}
          >
            <span style={{ color: "#94a3b8" }}>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
    </aside>
  );
}
