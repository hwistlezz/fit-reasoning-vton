import type { DemoMetric } from "@/lib/types";

type MetricCardProps = {
  metric: DemoMetric;
};

function formatValue(value: number, unit?: string) {
  if (unit === "%") {
    return `${Number.isInteger(value) ? value.toFixed(0) : value.toFixed(1)}%`;
  }

  if (unit === "score" || value > 1) {
    return value.toFixed(0);
  }

  if (value < 0.2) {
    return value.toFixed(3);
  }

  return value.toFixed(2);
}

function progressWidth(value: number, unit?: string) {
  const normalized = unit === "%" || value > 1 ? value / 100 : value;
  return `${Math.min(Math.max(normalized, 0), 1) * 100}%`;
}

export default function MetricCard({ metric }: MetricCardProps) {
  const methodIsBetter =
    metric.direction === "higher_is_better"
      ? metric.method_value >= metric.baseline_value
      : metric.method_value <= metric.baseline_value;

  return (
    <article className="rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/80 p-4 shadow-[0_0_30px_rgba(30,80,160,0.12)]">
      <div className="flex min-h-24 flex-col justify-between">
        <div>
          <h3 className="text-base font-semibold leading-6 text-[#E5EDF8]">
            {metric.title}
          </h3>
          <p className="mt-2 text-sm leading-5 text-[#9AA8BA]">
            {metric.description}
          </p>
        </div>
        <p
          className={[
            "mt-3 text-sm font-semibold",
            methodIsBetter ? "text-[#74C365]" : "text-[#F97316]",
          ].join(" ")}
        >
          {metric.improvement_text}
        </p>
      </div>

      <div className="mt-4 space-y-3">
        <MetricBar
          color="bg-[#F97316]"
          label={metric.baseline_label}
          unit={metric.unit}
          value={metric.baseline_value}
        />
        <MetricBar
          color="bg-[#74C365]"
          label={metric.method_label}
          unit={metric.unit}
          value={metric.method_value}
        />
      </div>
    </article>
  );
}

function MetricBar({
  label,
  value,
  unit,
  color,
}: {
  label: string;
  value: number;
  unit?: string;
  color: string;
}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-3 text-xs">
        <span className="truncate text-[#9AA8BA]">{label}</span>
        <span className="font-semibold text-[#E5EDF8]">
          {formatValue(value, unit)}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-[#061426]">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: progressWidth(value, unit) }}
        />
      </div>
    </div>
  );
}
