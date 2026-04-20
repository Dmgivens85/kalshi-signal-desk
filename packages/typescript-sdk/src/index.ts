export type RecommendedAction = "buy_yes" | "buy_no" | "monitor";

export type SignalAlert = {
  id: string;
  market_ticker: string;
  market_title: string | null;
  signal_type: string;
  thesis: string;
  confidence: number;
  horizon: string;
  status: string;
  recommended_action: RecommendedAction | null;
  reason_summary: string | null;
  source_count: number;
  metadata_json: {
    external_consensus?: number;
    kalshi_market_price?: number;
    dislocation?: number;
  };
  feature_payload: {
    market_snapshot?: {
      market_ticker?: string;
      title?: string;
      status?: string;
      last_price?: number | null;
      volume?: number | null;
      open_interest?: number | null;
    };
    providers?: Array<{
      provider: string;
      title: string;
      implied_probability?: number | null;
      mapping_confidence: number;
      strategy: string;
    }>;
    scores?: {
      external_consensus?: number;
      market_price?: number;
      dislocation?: number;
      mapping_confidence?: number;
      source_confidence?: number;
      alignment?: number;
    };
  };
  created_at: string;
};

export type PlatformOverview = {
  hero: {
    label: string;
    headline: string;
    summary: string;
  };
  metrics: Array<{
    label: string;
    value: string;
  }>;
  alerts: SignalAlert[];
};

const fallbackAlerts: SignalAlert[] = [
  {
    id: "fed-cut-demo",
    market_ticker: "FED-2026-CUTS",
    market_title: "Will the Fed deliver a rate cut by June 2026?",
    signal_type: "fused_external_consensus",
    thesis:
      "External venues and macro headlines are leaning more dovish than current Kalshi pricing, leaving room for a positive repricing in the YES contract.",
    confidence: 0.78,
    horizon: "intraday to 2 weeks",
    status: "active",
    recommended_action: "buy_yes",
    reason_summary: "External consensus is 71% versus Kalshi pricing near 58%.",
    source_count: 4,
    metadata_json: {
      external_consensus: 0.71,
      kalshi_market_price: 0.58,
      dislocation: 0.13
    },
    feature_payload: {
      market_snapshot: {
        market_ticker: "FED-2026-CUTS",
        title: "Will the Fed deliver a rate cut by June 2026?",
        status: "open",
        last_price: 58,
        volume: 18420,
        open_interest: 7220
      },
      providers: [
        {
          provider: "sportsbook",
          title: "Street pricing drifts toward a June rate cut",
          implied_probability: 0.69,
          mapping_confidence: 0.97,
          strategy: "exact_market_ref"
        },
        {
          provider: "manifold",
          title: "Manifold traders repriced soft-landing confidence lower",
          implied_probability: 0.73,
          mapping_confidence: 0.88,
          strategy: "exact_market_ref"
        }
      ],
      scores: {
        external_consensus: 0.71,
        market_price: 0.58,
        dislocation: 0.13,
        mapping_confidence: 0.92,
        source_confidence: 0.69,
        alignment: 0.48
      }
    },
    created_at: new Date().toISOString()
  },
  {
    id: "house-demo",
    market_ticker: "ELECTION-HOUSE-2026",
    market_title: "Will Democrats win the House in 2026?",
    signal_type: "fused_external_consensus",
    thesis:
      "Forecast communities and campaign-fundraising coverage are drifting more constructive than the current market midpoint, but the spread is smaller and still belongs in monitored mode.",
    confidence: 0.62,
    horizon: "1 to 4 weeks",
    status: "active",
    recommended_action: "monitor",
    reason_summary: "External consensus is 60% versus Kalshi pricing near 54%.",
    source_count: 3,
    metadata_json: {
      external_consensus: 0.6,
      kalshi_market_price: 0.54,
      dislocation: 0.06
    },
    feature_payload: {
      market_snapshot: {
        market_ticker: "ELECTION-HOUSE-2026",
        title: "Will Democrats win the House in 2026?",
        status: "open",
        last_price: 54,
        volume: 20310,
        open_interest: 8840
      },
      providers: [
        {
          provider: "metaculus",
          title: "Metaculus community drifts toward tighter House race distribution",
          implied_probability: 0.64,
          mapping_confidence: 0.97,
          strategy: "exact_market_ref"
        },
        {
          provider: "news",
          title: "District fundraising divergence widens ahead of House cycle",
          implied_probability: null,
          mapping_confidence: 0.87,
          strategy: "exact_market_ref"
        }
      ],
      scores: {
        external_consensus: 0.6,
        market_price: 0.54,
        dislocation: 0.06,
        mapping_confidence: 0.9,
        source_confidence: 0.67,
        alignment: 0.76
      }
    },
    created_at: new Date(Date.now() - 1000 * 60 * 18).toISOString()
  }
];

function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    process.env.API_BASE_URL ??
    "http://localhost:8000"
  );
}

async function safeFetch<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      cache: "no-store"
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function getSignalFeed(): Promise<SignalAlert[]> {
  const response = await safeFetch<{ items: SignalAlert[] }>("/api/signals");
  if (!response?.items?.length) {
    return fallbackAlerts;
  }
  return response.items;
}

export async function getSignalAlert(id: string): Promise<SignalAlert | null> {
  const response = await safeFetch<SignalAlert>(`/api/signals/${id}`);
  if (response) {
    return response;
  }
  return fallbackAlerts.find((alert) => alert.id === id) ?? null;
}

export async function getPlatformOverview(): Promise<PlatformOverview> {
  const alerts = await getSignalFeed();
  const avgConfidence =
    alerts.reduce((sum, alert) => sum + alert.confidence, 0) / Math.max(1, alerts.length);

  return {
    hero: {
      label: "Kalshi Market Intelligence",
      headline: "Explainable external consensus for event-driven trading teams.",
      summary:
        "Fuse Kalshi pricing with cross-venue odds, forecast communities, and live narrative catalysts in a mobile-native alert surface."
    },
    metrics: [
      { label: "Active alerts", value: `${alerts.length}` },
      { label: "Avg confidence", value: `${Math.round(avgConfidence * 100)}%` },
      {
        label: "Buy yes setups",
        value: `${alerts.filter((alert) => alert.recommended_action === "buy_yes").length}`
      }
    ],
    alerts
  };
}
