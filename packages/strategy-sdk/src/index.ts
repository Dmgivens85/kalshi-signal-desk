export type StrategyDescriptor = {
  id: string;
  name: string;
  description: string;
  enabledByDefault: boolean;
};

export const defaultStrategies: StrategyDescriptor[] = [
  {
    id: "overnight-high-confidence",
    name: "Overnight High Confidence",
    description: "Alert only when Kalshi signal quality and external confirmation align strongly.",
    enabledByDefault: true
  }
];
