import { formatCurrency, formatNumber } from "../lib/formatters";
import type { MetricCard } from "../types/report";

const toneStyles: Record<MetricCard["tone"], string> = {
  blue: "from-sky-500/18 to-cyan-400/8 text-sky-600",
  teal: "from-teal-500/18 to-emerald-400/8 text-teal-600",
  gold: "from-amber-400/20 to-yellow-300/8 text-amber-600",
  slate: "from-slate-300/50 to-slate-100 text-slate-700"
};

type KpiCardProps = {
  item: MetricCard;
};

export default function KpiCard({ item }: KpiCardProps) {
  return (
    <article className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_18px_36px_rgba(15,23,42,0.05)]">
      <div
        className={`inline-flex rounded-2xl bg-gradient-to-br px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] ${toneStyles[item.tone]}`}
      >
        {item.label}
      </div>
      <div className="mt-5 font-display text-3xl font-extrabold tracking-tight text-slate-950">
        {item.format === "currency" ? formatCurrency(item.value) : formatNumber(item.value)}
      </div>
    </article>
  );
}
