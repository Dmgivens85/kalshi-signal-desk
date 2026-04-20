export type ServiceHealth = {
  service: string;
  status: "healthy" | "degraded" | "unhealthy";
  detail?: string;
};

export type SignalUrgency = "info" | "watch" | "critical_opportunity" | "critical_risk";
export type RecommendedAction = "buy_yes" | "buy_no" | "monitor";

export type AlertSummary = {
  id: string;
  marketTicker: string;
  title: string;
  confidence: number;
  urgency: SignalUrgency;
  summary: string;
};

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

export type ExecutionOrder = {
  id: string;
  market_ticker: string;
  signal_id?: string | null;
  side: string;
  action: string;
  order_type: string;
  status: string;
  approval_status: string;
  count: number;
  price?: number | null;
  yes_price?: number | null;
  no_price?: number | null;
  size_bucket?: string | null;
  preview_payload?: {
    risk_evaluation_summary?: string;
    risk_evaluation?: {
      passed?: boolean;
      blocking_reasons?: string[];
      warnings?: string[];
    };
    supporting_signal_summary?: string | null;
  };
  risk_check_payload?: Record<string, unknown>;
  created_at?: string;
};

export type PositionSummary = {
  id: string;
  market_ticker: string;
  category?: string | null;
  side?: string | null;
  contracts_count: number;
  average_entry_price: number;
  exposure_cents: number;
  realized_pnl_cents: number;
  unrealized_pnl_cents: number;
  is_open: boolean;
};

export type RiskDashboard = {
  limits: Record<string, unknown>;
  status: {
    kill_switch_enabled: boolean;
    current_open_positions: number;
    current_market_exposure_cents: number;
    current_category_exposure_cents: Record<string, number>;
    latest_risk_events: Array<{
      id: string;
      rule_name: string;
      severity: string;
      detail: string;
      created_at: string;
    }>;
  };
};

export type AutomationPolicy = {
  id: string;
  name: string;
  strategy_id?: string | null;
  strategy_slug?: string | null;
  is_enabled: boolean;
  dry_run: boolean;
  user_opt_in_enabled: boolean;
  allowed_market_tickers: string[];
  allowed_categories: string[];
  min_confidence_score: number;
  overnight_min_confidence_score: number;
  max_size_bucket: string;
  max_open_automated_positions: number;
  notes?: string | null;
};

export type AutomationStatus = {
  global_enabled: boolean;
  global_paused: boolean;
  global_dry_run: boolean;
  blocked_reason?: string | null;
  active_policy_count: number;
  recent_events: Array<{
    id: string;
    event_type: string;
    status: string;
    severity: string;
    detail: string;
    created_at: string;
  }>;
  recent_failures: Array<{
    id: string;
    failure_type: string;
    detail: string;
    created_at: string;
  }>;
};

export type PaperOrder = {
  id: string;
  source_order_id?: string | null;
  signal_id?: string | null;
  market_ticker: string;
  side: string;
  action: string;
  order_type: string;
  status: string;
  requested_count: number;
  filled_count: number;
  remaining_count: number;
  reference_price?: number | null;
  simulated_average_fill_price?: number | null;
  fill_mode: string;
  is_automation: boolean;
  created_at: string;
};

export type PaperPosition = {
  id: string;
  signal_id?: string | null;
  market_ticker: string;
  category?: string | null;
  side?: string | null;
  contracts_count: number;
  average_entry_price: number;
  exposure_cents: number;
  realized_pnl_cents: number;
  unrealized_pnl_cents: number;
  entry_confidence_score?: number | null;
  is_open: boolean;
  created_at: string;
};

export type PaperPerformance = {
  open_positions: number;
  closed_positions: number;
  realized_pnl_cents: number;
  unrealized_pnl_cents: number;
  exposure_by_market: Record<string, number>;
  exposure_by_category: Record<string, number>;
  win_rate: number;
  average_confidence: number;
};

export type PaperStatus = {
  mode: string;
  enabled: boolean;
  paper_only: boolean;
  performance: PaperPerformance;
  latest_portfolio_snapshot?: {
    id: string;
    equity_cents: number;
    realized_pnl_cents: number;
    unrealized_pnl_cents: number;
    created_at: string;
  } | null;
};

export type SimulationRun = {
  id: string;
  name: string;
  mode: string;
  status: string;
  market_ticker?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  summary_json: Record<string, unknown>;
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

const fallbackOrders: ExecutionOrder[] = [
  {
    id: "preview-fed-cut",
    market_ticker: "FED-2026-CUTS",
    signal_id: "fed-cut-demo",
    side: "yes",
    action: "buy",
    order_type: "limit",
    status: "pending_approval",
    approval_status: "pending_approval",
    count: 12,
    price: 58,
    yes_price: 58,
    size_bucket: "small",
    preview_payload: {
      risk_evaluation_summary: "Deterministic checks passed and the order may proceed to manual approval.",
      risk_evaluation: {
        passed: true,
        blocking_reasons: [],
        warnings: ["Category concentration is elevated but still within tolerance."]
      },
      supporting_signal_summary: "External consensus is 71% versus Kalshi pricing near 58%."
    },
    created_at: new Date().toISOString()
  }
];

const fallbackPositions: PositionSummary[] = [
  {
    id: "pos-fed-cut",
    market_ticker: "FED-2026-CUTS",
    category: "fed",
    side: "yes",
    contracts_count: 7,
    average_entry_price: 54,
    exposure_cents: 378,
    realized_pnl_cents: 0,
    unrealized_pnl_cents: 28,
    is_open: true
  }
];

const fallbackRisk: RiskDashboard = {
  limits: {
    max_exposure_per_market_cents: 25000,
    max_exposure_per_category_cents: 75000,
    max_simultaneous_positions: 8,
    max_spread_cents: 12,
    min_liquidity: 100
  },
  status: {
    kill_switch_enabled: true,
    current_open_positions: 1,
    current_market_exposure_cents: 378,
    current_category_exposure_cents: { fed: 378 },
    latest_risk_events: []
  }
};

const fallbackAutomationStatus: AutomationStatus = {
  global_enabled: false,
  global_paused: false,
  global_dry_run: true,
  blocked_reason: "Selective automation is disabled by default.",
  active_policy_count: 0,
  recent_events: [],
  recent_failures: []
};

const fallbackAutomationPolicies: AutomationPolicy[] = [
  {
    id: "macro-overnight-dry-run",
    name: "macro-overnight-dry-run",
    strategy_slug: "macro-consensus",
    is_enabled: false,
    dry_run: true,
    user_opt_in_enabled: false,
    allowed_market_tickers: ["FED-2026-CUTS"],
    allowed_categories: ["macro-consensus"],
    min_confidence_score: 0.92,
    overnight_min_confidence_score: 0.97,
    max_size_bucket: "small",
    max_open_automated_positions: 1,
    notes: "Disabled by default until paper-mode review is stable."
  }
];

const fallbackPaperStatus: PaperStatus = {
  mode: "paper",
  enabled: true,
  paper_only: true,
  performance: {
    open_positions: 1,
    closed_positions: 2,
    realized_pnl_cents: 145,
    unrealized_pnl_cents: 28,
    exposure_by_market: { "FED-2026-CUTS": 378 },
    exposure_by_category: { fed: 378 },
    win_rate: 0.5,
    average_confidence: 0.84
  },
  latest_portfolio_snapshot: {
    id: "paper-snap-demo",
    equity_cents: 1000173,
    realized_pnl_cents: 145,
    unrealized_pnl_cents: 28,
    created_at: new Date().toISOString()
  }
};

const fallbackPaperOrders: PaperOrder[] = [
  {
    id: "paper-order-demo",
    source_order_id: "preview-fed-cut",
    signal_id: "fed-cut-demo",
    market_ticker: "FED-2026-CUTS",
    side: "yes",
    action: "buy",
    order_type: "limit",
    status: "filled",
    requested_count: 12,
    filled_count: 12,
    remaining_count: 0,
    reference_price: 58,
    simulated_average_fill_price: 58,
    fill_mode: "midpoint",
    is_automation: false,
    created_at: new Date().toISOString()
  }
];

const fallbackPaperPositions: PaperPosition[] = [
  {
    id: "paper-position-demo",
    signal_id: "fed-cut-demo",
    market_ticker: "FED-2026-CUTS",
    category: "fed",
    side: "yes",
    contracts_count: 12,
    average_entry_price: 58,
    exposure_cents: 696,
    realized_pnl_cents: 0,
    unrealized_pnl_cents: 24,
    entry_confidence_score: 0.84,
    is_open: true,
    created_at: new Date().toISOString()
  }
];

const fallbackSimulationRuns: SimulationRun[] = [
  {
    id: "replay-demo",
    name: "Overnight macro replay",
    mode: "replay",
    status: "completed",
    market_ticker: "FED-2026-CUTS",
    started_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    completed_at: new Date().toISOString(),
    summary_json: {
      processed_events: 120,
      processed_signals: 4,
      price_change_cents: 6
    }
  }
];

function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.API_BASE_URL;
  if (!configured) {
    return "http://localhost:8000";
  }
  if (/^https?:\/\//.test(configured)) {
    return configured;
  }
  return `http://${configured}`;
}

async function safeFetch<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, { cache: "no-store" });
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
      label: "Kalshi Signal Desk",
      headline: "Explainable external consensus for event-driven Kalshi operators.",
      summary:
        "Fuse Kalshi pricing with cross-platform enrichers, AI-assisted ranking, and cautious approval-first execution in a mobile-native desk."
    },
    metrics: [
      { label: "Active alerts", value: `${alerts.length}` },
      { label: "Avg confidence", value: `${Math.round(avgConfidence * 100)}%` },
      {
        label: "Critical-ready",
        value: `${alerts.filter((alert) => alert.recommended_action === "buy_yes").length}`
      }
    ],
    alerts
  };
}

export async function getPendingApprovals(): Promise<ExecutionOrder[]> {
  const response = await safeFetch<{ items: ExecutionOrder[] }>("/api/approvals/pending");
  return response?.items?.length ? response.items : fallbackOrders;
}

export async function getExecutionOrders(): Promise<ExecutionOrder[]> {
  const response = await safeFetch<{ items: ExecutionOrder[] }>("/api/orders");
  return response?.items?.length ? response.items : fallbackOrders;
}

export async function getExecutionOrder(id: string): Promise<ExecutionOrder | null> {
  const response = await safeFetch<ExecutionOrder>(`/api/orders/${id}`);
  return response ?? fallbackOrders.find((order) => order.id === id) ?? null;
}

export async function getPositions(): Promise<PositionSummary[]> {
  const response = await safeFetch<{ items: PositionSummary[] }>("/api/positions");
  return response?.items?.length ? response.items : fallbackPositions;
}

export async function getRiskDashboard(): Promise<RiskDashboard> {
  const response = await safeFetch<RiskDashboard>("/api/risk");
  return response ?? fallbackRisk;
}

export async function getAutomationStatus(): Promise<AutomationStatus> {
  const response = await safeFetch<AutomationStatus>("/api/automation/status");
  return response ?? fallbackAutomationStatus;
}

export async function getAutomationPolicies(): Promise<AutomationPolicy[]> {
  const response = await safeFetch<{ items: AutomationPolicy[] }>("/api/automation/policies");
  return response?.items?.length ? response.items : fallbackAutomationPolicies;
}

export async function getPaperStatus(): Promise<PaperStatus> {
  const response = await safeFetch<PaperStatus>("/api/paper/status");
  return response ?? fallbackPaperStatus;
}

export async function getPaperOrders(): Promise<PaperOrder[]> {
  const response = await safeFetch<{ items: PaperOrder[] }>("/api/paper/orders");
  return response?.items?.length ? response.items : fallbackPaperOrders;
}

export async function getPaperPositions(): Promise<PaperPosition[]> {
  const response = await safeFetch<{ items: PaperPosition[] }>("/api/paper/positions");
  return response?.items?.length ? response.items : fallbackPaperPositions;
}

export async function getPaperPerformance(): Promise<PaperPerformance> {
  const response = await safeFetch<PaperPerformance>("/api/paper/performance");
  return response ?? fallbackPaperStatus.performance;
}

export async function getSimulationRuns(): Promise<SimulationRun[]> {
  const response = await safeFetch<{ items: SimulationRun[] }>("/api/paper/simulation-runs");
  return response?.items?.length ? response.items : fallbackSimulationRuns;
}
