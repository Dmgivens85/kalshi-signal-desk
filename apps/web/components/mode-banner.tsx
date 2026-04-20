import { getPaperStatus } from "@kalshi/shared-ts";

export async function ModeBanner() {
  const status = await getPaperStatus();
  const isPaper = status.mode === "paper";
  const isDisabled = status.mode === "disabled";

  return (
    <div className={`mode-banner ${isPaper ? "mode-paper" : isDisabled ? "mode-disabled" : "mode-live"}`}>
      <strong>{isPaper ? "Paper mode" : isDisabled ? "Execution disabled" : "Live mode"}</strong>
      <span>
        {isPaper
          ? " Simulated orders and fills only. No live Kalshi orders are sent."
          : isDisabled
            ? " Submission is blocked until execution is explicitly enabled."
            : " Server-side live execution is enabled."}
      </span>
    </div>
  );
}
