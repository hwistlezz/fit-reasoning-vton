import type { DemoMetric } from "@/lib/types";

type RiskGaugeCardProps = {
  metric: DemoMetric;
};

function formatPercent(value: number) {
  return `${Number.isInteger(value) ? value.toFixed(0) : value.toFixed(1)}%`;
}

export default function RiskGaugeCard({ metric }: RiskGaugeCardProps) {
  const baselineRisk = metric.unit === "%" ? metric.baseline_value : metric.baseline_value * 100;
  const methodRisk = metric.unit === "%" ? metric.method_value : metric.method_value * 100;
  const stability = Math.max(0, Math.min(100, 100 - methodRisk));

  return (
    <article className="rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/80 p-4 shadow-[0_0_30px_rgba(30,80,160,0.12)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold leading-6 text-[#E5EDF8]">
            {metric.title}
          </h3>
          <p className="mt-2 text-sm leading-5 text-[#9AA8BA]">
            {metric.description}
          </p>
        </div>
        <div
          className="grid h-20 w-20 shrink-0 place-items-center rounded-full"
          style={{
            background: `conic-gradient(#74C365 ${stability}%, rgba(116,195,101,0.12) ${stability}% 100%)`,
          }}
        >
          <div className="grid h-14 w-14 place-items-center rounded-full bg-[#061426] text-sm font-semibold text-[#E5EDF8]">
            {formatPercent(methodRisk)}
          </div>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-[#F97316]/25 bg-[#F97316]/10 p-3">
          <p className="text-xs text-[#FDBA74]">{metric.baseline_label}</p>
          <p className="mt-1 text-xl font-semibold text-[#E5EDF8]">
            {formatPercent(baselineRisk)}
          </p>
        </div>
        <div className="rounded-lg border border-[#74C365]/25 bg-[#74C365]/10 p-3">
          <p className="text-xs text-[#A7E39C]">{metric.method_label}</p>
          <p className="mt-1 text-xl font-semibold text-[#E5EDF8]">
            {formatPercent(methodRisk)}
          </p>
        </div>
      </div>
      <p className="mt-3 text-sm font-semibold text-[#74C365]">
        {metric.improvement_text}
      </p>
    </article>
  );
}
