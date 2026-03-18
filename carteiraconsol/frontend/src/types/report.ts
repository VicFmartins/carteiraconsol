export type PortfolioRecord = {
  clientName: string;
  riskProfile: string;
  broker: string;
  assetClass: string;
  ticker: string;
  assetName: string;
  quantity: number;
  avgPrice: number;
  totalValue: number;
  referenceDate: string;
};

export type MetricCard = {
  label: string;
  value: number;
  tone: "blue" | "teal" | "gold" | "slate";
  format: "currency" | "number";
};

export type BreakdownItem = {
  label: string;
  value: number;
  share: number;
};

export type TimelinePoint = {
  date: string;
  value: number;
};

export type InsightItem = {
  title: string;
  body: string;
};

export type PortfolioReport = {
  clientName: string;
  diagnosis: string;
  sourceLabel: string;
  generatedAt: string;
  latestReferenceDate: string;
  metrics: MetricCard[];
  allocation: BreakdownItem[];
  brokerExposure: BreakdownItem[];
  clientExposure: BreakdownItem[];
  timeline: TimelinePoint[];
  positions: PortfolioRecord[];
  insights: InsightItem[];
};

export type ApiStatus = {
  connected: boolean;
  message: string;
};

export type UploadSummary = {
  filename: string;
  detectedType: string;
  rowsProcessed: number;
  rowsSkipped: number;
  message: string;
  processedAt: string;
  rawFile: string;
  processedFile: string;
};

export type UploadLifecycleState = "idle" | "uploading" | "processing" | "success" | "error";

export type UploadHistoryItem = UploadSummary & {
  id: string;
  status: "success" | "error";
  timestamp: string;
};

export type BuilderState = {
  report: PortfolioReport | null;
  apiStatus: ApiStatus;
  loadingLiveData: boolean;
  uploadName: string | null;
  lastError: string | null;
};
