import type { DemoFitDetails } from "@/lib/types";

type FitDetailsPanelProps = {
  fit: DemoFitDetails;
};

const fitRows = [
  { label: "Shoulder Alignment", baseline: 74, lora: 88, diff: "+14" },
  { label: "Graphic Preservation", baseline: 69, lora: 87, diff: "+18" },
  { label: "Sleeve Boundary", baseline: 68, lora: 84, diff: "+16" },
  { label: "Hem Stability", baseline: 71, lora: 85, diff: "+14" },
  { label: "Color Consistency", baseline: 76, lora: 88, diff: "+12" },
  { label: "Pose Robustness", baseline: 70, lora: 84, diff: "+14" },
];

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

export default function FitDetailsPanel({ fit }: FitDetailsPanelProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
      <div className="rounded-2xl border border-[#6EA5FF]/20 bg-[#0C1C34]/70 p-5">
        <p className="text-xs uppercase tracking-[0.2em] text-[#38BDF8]">
          Fit Details
        </p>
        <h3 className="mt-3 text-2xl font-semibold text-[#E5EDF8]">
          {fit.fit_label}
        </h3>
        <p className="mt-2 text-sm text-[#9AA8BA]">
          Confidence {percent(fit.confidence)}
        </p>
        <div className="mt-5 space-y-3 text-sm">
          <div className="rounded-xl border border-[#F97316]/25 bg-[#F97316]/10 p-3">
            <p className="font-semibold text-[#FDBA74]">StableVITON</p>
            <p className="mt-1 text-[#9AA8BA]">
              slightly unstable oversized fit
            </p>
          </div>
          <div className="rounded-xl border border-[#74C365]/25 bg-[#74C365]/10 p-3">
            <p className="font-semibold text-[#A7E39C]">StableVITON + LoRA</p>
            <p className="mt-1 text-[#9AA8BA]">stable oversized fit</p>
          </div>
        </div>
      </div>
      <div className="overflow-hidden rounded-2xl border border-[#6EA5FF]/18 bg-[#0C1C34]/70">
        <div className="grid grid-cols-[1.4fr_0.8fr_0.8fr_0.6fr] border-b border-[#6EA5FF]/16 bg-[#061426]/70 px-4 py-3 text-xs font-semibold uppercase tracking-[0.14em] text-[#9AA8BA]">
          <span>Metric</span>
          <span>Baseline</span>
          <span>LoRA</span>
          <span>Diff</span>
        </div>
        {fitRows.map((row) => (
          <div
            className="grid grid-cols-[1.4fr_0.8fr_0.8fr_0.6fr] items-center border-b border-[#6EA5FF]/10 px-4 py-3 text-sm last:border-b-0"
            key={row.label}
          >
            <span className="font-semibold text-[#E5EDF8]">{row.label}</span>
            <span className="text-[#FDBA74]">{row.baseline}</span>
            <span className="text-[#A7E39C]">{row.lora}</span>
            <span className="font-semibold text-[#74C365]">{row.diff}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
