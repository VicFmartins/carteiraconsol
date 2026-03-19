import { formatCurrency, formatDate, formatNumber } from "../lib/formatters";
import { assetClassLabel } from "../lib/presentation";
import type { DashboardData, DashboardFilters } from "../types/report";
import KpiCard from "./KpiCard";
import DonutChart from "./charts/DonutChart";
import HorizontalBars from "./charts/HorizontalBars";
import TimelineChart from "./charts/TimelineChart";

type DashboardWorkspaceProps = {
  data: DashboardData | null;
  filters: DashboardFilters;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onFilterChange: (field: keyof DashboardFilters, value: string) => void;
};

function SectionHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <div className="mb-5 flex flex-col gap-2">
      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-400">{eyebrow}</p>
      <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <h2 className="font-display text-2xl font-extrabold tracking-tight text-slate-950">{title}</h2>
        <p className="max-w-2xl text-sm leading-7 text-slate-500">{description}</p>
      </div>
    </div>
  );
}

function DashboardSelect({
  label,
  value,
  options,
  onChange
}: {
  label: string;
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</div>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-sky-200"
      >
        {options.map((option) => (
          <option key={`${label}-${option.value || "all"}`} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function DashboardWorkspace({
  data,
  filters,
  loading,
  error,
  onRefresh,
  onFilterChange
}: DashboardWorkspaceProps) {
  if (loading) {
    return (
      <section className="rounded-[32px] border border-slate-200 bg-[#f8fafc] p-8 shadow-[0_24px_70px_rgba(15,23,42,0.18)]">
        <div className="rounded-[28px] border border-dashed border-slate-200 bg-white px-6 py-16 text-center text-sm text-slate-500">
          Carregando dashboard executivo com dados reais da API...
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-[32px] border border-slate-200 bg-[#f8fafc] p-8 shadow-[0_24px_70px_rgba(15,23,42,0.18)]">
        <div className="rounded-[28px] border border-rose-200 bg-rose-50 px-6 py-16 text-center text-sm text-rose-700">
          {error}
        </div>
      </section>
    );
  }

  if (!data || !data.positions.length) {
    return (
      <section className="rounded-[32px] border border-slate-200 bg-[#f8fafc] p-8 shadow-[0_24px_70px_rgba(15,23,42,0.18)]">
        <div className="rounded-[28px] border border-dashed border-slate-200 bg-white px-6 py-16 text-center text-sm text-slate-500">
          Nenhuma posicao encontrada para os filtros atuais. Ajuste o recorte para visualizar o dashboard.
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-[32px] border border-slate-200 bg-[#f8fafc] p-6 shadow-[0_24px_70px_rgba(15,23,42,0.18)] md:p-8 lg:p-10">
      <header className="rounded-[28px] bg-[radial-gradient(circle_at_top_right,rgba(20,184,166,0.14),transparent_22%),linear-gradient(145deg,#081223_0%,#0e1b31_55%,#14223a_100%)] p-8 text-white">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.34em] text-cyan-100/70">Executive Dashboard</p>
            <h1 className="mt-3 font-display text-4xl font-extrabold tracking-tight">Live portfolio intelligence</h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300">
              Painel operacional com indicadores, alocacao e exposicao construidos diretamente sobre o snapshot atual
              do CarteiraConsol.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-4">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Reference date</p>
              <p className="mt-2 text-sm font-semibold text-white">{data.asOfDate ? formatDate(data.asOfDate) : "-"}</p>
            </div>
            <button
              type="button"
              onClick={onRefresh}
              className="rounded-2xl border border-cyan-300/18 bg-cyan-300/[0.08] px-4 py-4 text-left text-sm font-semibold text-cyan-50 transition hover:bg-cyan-300/[0.12]"
            >
              Refresh live data
            </button>
          </div>
        </div>
      </header>

      <div className="mt-8 rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <SectionHeader
          eyebrow="Filters"
          title="Executive Cut"
          description="Aplique filtros leves para recortar o snapshot atual sem sair do workspace."
        />
        <div className="grid gap-4 md:grid-cols-3">
          <DashboardSelect
            label="Client"
            value={filters.clientName}
            options={[{ value: "", label: "Todos os clientes" }, ...data.availableClients.map((item) => ({ value: item, label: item }))]}
            onChange={(value) => onFilterChange("clientName", value)}
          />
          <DashboardSelect
            label="Asset class"
            value={filters.assetClass}
            options={[
              { value: "", label: "Todas as classes" },
              ...data.availableAssetClasses.map((item) => ({ value: item, label: assetClassLabel(item) }))
            ]}
            onChange={(value) => onFilterChange("assetClass", value)}
          />
          <DashboardSelect
            label="Reference date"
            value={filters.referenceDate}
            options={[
              { value: "", label: "Ultimo snapshot" },
              ...data.availableReferenceDates.map((item) => ({ value: item, label: formatDate(item) }))
            ]}
            onChange={(value) => onFilterChange("referenceDate", value)}
          />
        </div>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {data.metrics.map((item) => (
          <KpiCard key={item.label} item={item} />
        ))}
      </div>

      <div className="mt-10 grid gap-6 xl:grid-cols-[1.02fr_0.98fr]">
        <article className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
          <SectionHeader
            eyebrow="Allocation Overview"
            title="Allocation by Asset Class"
            description="Distribuicao do valor consolidado entre classes no snapshot filtrado."
          />
          <div className="grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)] lg:items-center">
            <DonutChart items={data.assetAllocation.map((item) => ({ ...item, label: assetClassLabel(item.label) }))} />
            <div className="space-y-3">
              {data.assetAllocation.map((item) => (
                <div key={item.label} className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{assetClassLabel(item.label)}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400">
                        {formatNumber(item.share * 100, 1)}%
                      </p>
                    </div>
                    <p className="text-sm font-semibold text-slate-700">{formatCurrency(item.value)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </article>

        <article className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
          <SectionHeader
            eyebrow="Client Exposure"
            title="Allocation by Client"
            description="Participacao relativa dos clientes no recorte corrente do portfolio."
          />
          <HorizontalBars items={data.clientAllocation} tone="teal" />
        </article>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.02fr_0.98fr]">
        <article className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
          <SectionHeader
            eyebrow="Asset Concentration"
            title="Top Assets by Total Value"
            description="Maior exposicao por ativo ou ticker, ordenada do maior para o menor valor."
          />
          <HorizontalBars items={data.topAssets} />
        </article>

        <article className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
          <SectionHeader
            eyebrow="Portfolio Timeline"
            title="Portfolio Evolution"
            description="Evolucao do valor consolidado ao longo dos snapshots disponiveis."
          />
          <TimelineChart items={data.timeline} />
        </article>
      </div>

      <div className="mt-6 rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
        <SectionHeader
          eyebrow="Detailed Positions"
          title="Positions Table"
          description="Tabela operacional das posicoes mais relevantes no snapshot filtrado."
        />

        <div className="overflow-x-auto">
          <table className="min-w-full border-separate border-spacing-y-3 text-left">
            <thead>
              <tr className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                <th className="px-4">Client</th>
                <th className="px-4">Asset</th>
                <th className="px-4">Ticker</th>
                <th className="px-4">Class</th>
                <th className="px-4 text-right">Quantity</th>
                <th className="px-4 text-right">Avg price</th>
                <th className="px-4 text-right">Total value</th>
                <th className="px-4 text-right">Reference date</th>
              </tr>
            </thead>
            <tbody>
              {data.positions.map((position) => (
                <tr key={`${position.referenceDate}-${position.ticker}-${position.broker}-${position.clientName}`} className="text-sm text-slate-700">
                  <td className="rounded-l-2xl bg-slate-50 px-4 py-4 font-semibold text-slate-950">{position.clientName}</td>
                  <td className="bg-slate-50 px-4 py-4">{position.assetName}</td>
                  <td className="bg-slate-50 px-4 py-4 font-semibold text-slate-900">{position.ticker || "-"}</td>
                  <td className="bg-slate-50 px-4 py-4">{assetClassLabel(position.assetClass)}</td>
                  <td className="bg-slate-50 px-4 py-4 text-right">{formatNumber(position.quantity, position.quantity < 1 ? 4 : 2)}</td>
                  <td className="bg-slate-50 px-4 py-4 text-right">{formatCurrency(position.avgPrice)}</td>
                  <td className="bg-slate-50 px-4 py-4 text-right font-semibold text-slate-950">{formatCurrency(position.totalValue)}</td>
                  <td className="rounded-r-2xl bg-slate-50 px-4 py-4 text-right">{formatDate(position.referenceDate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
