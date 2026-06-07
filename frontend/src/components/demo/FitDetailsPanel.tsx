import type { DemoFitDetails } from "@/lib/types";

type FitDetailsPanelProps = {
  fit: DemoFitDetails;
};

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function ratio(value: number) {
  return value.toFixed(2);
}

export default function FitDetailsPanel({ fit }: FitDetailsPanelProps) {
  const ratios = [
    { label: "Shoulder Ratio", value: ratio(fit.shoulder_ratio) },
    { label: "Torso Width Ratio", value: ratio(fit.torso_width_ratio) },
    { label: "Sleeve Length Ratio", value: ratio(fit.sleeve_length_ratio) },
    { label: "Garment Length Ratio", value: ratio(fit.garment_length_ratio) },
  ];

  const quality = [
    { label: "Pose Quality", value: fit.pose_quality },
    { label: "Parsing Quality", value: fit.parsing_quality },
    { label: "Body Visibility", value: fit.body_visibility },
  ];

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
        <p className="mt-4 text-sm leading-6 text-[#9AA8BA]">
          어깨, 몸통, 소매, 의류 길이 비율을 기준으로 생성 결과의 착용
          일관성을 분석합니다.
        </p>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <div className="grid gap-3 sm:grid-cols-2">
          {ratios.map((item) => (
            <div
              className="rounded-2xl border border-[#6EA5FF]/18 bg-[#0C1C34]/70 p-4"
              key={item.label}
            >
              <p className="text-sm text-[#9AA8BA]">{item.label}</p>
              <p className="mt-2 text-2xl font-semibold text-[#E5EDF8]">
                {item.value}
              </p>
            </div>
          ))}
        </div>
        <div className="space-y-3 rounded-2xl border border-[#6EA5FF]/18 bg-[#0C1C34]/70 p-4">
          {quality.map((item) => (
            <div key={item.label}>
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="text-[#9AA8BA]">{item.label}</span>
                <span className="font-semibold text-[#E5EDF8]">
                  {percent(item.value)}
                </span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-[#061426]">
                <div
                  className="h-full rounded-full bg-[#74C365]"
                  style={{ width: `${item.value * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
