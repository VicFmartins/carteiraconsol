import type { PortfolioSnapshotApi } from "./api";
import { joinSnapshot } from "./reportBuilder";
import type { BreakdownItem, DashboardData, DashboardFilters, MetricCard, PortfolioRecord, TimelinePoint } from "../types/report";

function uniqueSorted(values: string[]) {
  return [...new Set(values.filter(Boolean))].sort((left, right) => left.localeCompare(right, "pt-BR"));
}

function buildBreakdown(records: PortfolioRecord[], getKey: (record: PortfolioRecord) => string): BreakdownItem[] {
  const total = records.reduce((sum, record) => sum + record.totalValue, 0) || 1;
  const grouped = new Map<string, number>();

  records.forEach((record) => {
    const key = getKey(record);
    grouped.set(key, (grouped.get(key) ?? 0) + record.totalValue);
  });

  return [...grouped.entries()]
    .map(([label, value]) => ({ label, value, share: value / total }))
    .sort((left, right) => right.value - left.value);
}

function buildTimeline(records: PortfolioRecord[]): TimelinePoint[] {
  const grouped = new Map<string, number>();
  records.forEach((record) => {
    grouped.set(record.referenceDate, (grouped.get(record.referenceDate) ?? 0) + record.totalValue);
  });

  return [...grouped.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([date, value]) => ({ date, value }));
}

function buildTopAssets(records: PortfolioRecord[]): BreakdownItem[] {
  return buildBreakdown(records, (record) => record.ticker || record.assetName).slice(0, 8);
}

function buildMetrics(records: PortfolioRecord[]): MetricCard[] {
  return [
    {
      label: "Portfolio Value",
      value: records.reduce((sum, record) => sum + record.totalValue, 0),
      tone: "blue",
      format: "currency"
    },
    {
      label: "Active Clients",
      value: new Set(records.map((record) => record.clientName)).size,
      tone: "teal",
      format: "number"
    },
    {
      label: "Tracked Assets",
      value: new Set(records.map((record) => record.ticker || record.assetName)).size,
      tone: "gold",
      format: "number"
    },
    {
      label: "Active Accounts",
      value: new Set(records.map((record) => `${record.clientName}|${record.broker}`)).size,
      tone: "slate",
      format: "number"
    }
  ];
}

export function buildDashboardData(snapshot: PortfolioSnapshotApi, filters: DashboardFilters): DashboardData {
  const records = joinSnapshot(snapshot.clients, snapshot.accounts, snapshot.assets, snapshot.positions);
  const availableClients = uniqueSorted(records.map((record) => record.clientName));
  const availableAssetClasses = uniqueSorted(records.map((record) => record.assetClass));

  const scopedRecords = records.filter((record) => {
    if (filters.clientName && record.clientName !== filters.clientName) return false;
    if (filters.assetClass && record.assetClass !== filters.assetClass) return false;
    return true;
  });

  const availableReferenceDates = uniqueSorted(scopedRecords.map((record) => record.referenceDate)).sort((left, right) =>
    right.localeCompare(left)
  );
  const effectiveReferenceDate = filters.referenceDate || availableReferenceDates[0] || "";
  const currentRecords = scopedRecords
    .filter((record) => (!effectiveReferenceDate ? true : record.referenceDate === effectiveReferenceDate))
    .sort((left, right) => right.totalValue - left.totalValue);

  return {
    asOfDate: effectiveReferenceDate || null,
    metrics: buildMetrics(currentRecords),
    assetAllocation: buildBreakdown(currentRecords, (record) => record.assetClass).slice(0, 8),
    clientAllocation: buildBreakdown(currentRecords, (record) => record.clientName).slice(0, 8),
    topAssets: buildTopAssets(currentRecords),
    timeline: buildTimeline(scopedRecords),
    positions: currentRecords.slice(0, 15),
    availableClients,
    availableAssetClasses,
    availableReferenceDates
  };
}
