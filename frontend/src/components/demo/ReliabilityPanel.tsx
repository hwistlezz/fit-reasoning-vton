import type { DemoReliability } from "@/lib/types";

type ReliabilityPanelProps = {
  reliability: DemoReliability;
};

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

export default function ReliabilityPanel({ reliability }: ReliabilityPanelProps) {
  const items = [
    {
      label: "Result Reliability",
      value: reliability.result_reliability,
      color: "bg-[#74C365]",
      display: reliability.result_reliability,
    },
    {
      label: "Pose Reliability",
      value: reliability.pose_reliability,
      color: "bg-[#38BDF8]",
      display: reliability.pose_reliability,
    },
    {
      label: "Boundary Stability",
      value: reliability.boundary_stability,
      color: "bg-[#5B8CFF]",
      display: reliability.boundary_stability,
    },
    {
      label: "Occlusion Risk",
      value: 1 - reliability.occlusion_risk,
      color: "bg-[#F97316]",
      display: reliability.occlusion_risk,
    },
    {
      label: "Generation Risk",
      value: 1 - reliability.artifact_risk,
      color: "bg-[#EF4444]",
      display: reliability.artifact_risk,
    },
  ];

  return (
    <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
      <div className="rounded-2xl border border-[#74C365]/25 bg-[#74C365]/10 p-5">
        <p className="text-sm font-medium text-[#A7E39C]">
          Result reliability score
        </p>
        <p className="mt-3 text-5xl font-semibold text-[#E5EDF8]">
          {percent(reliability.result_reliability)}
        </p>
        <p className="mt-4 text-sm leading-6 text-[#9AA8BA]">
          이 신뢰도는 정답 확률이 아니라 pose visibility, boundary
          stability, occlusion risk 등을 기반으로 한 분석용 추정값입니다.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <div
            className="rounded-2xl border border-[#6EA5FF]/18 bg-[#0C1C34]/70 p-4"
            key={item.label}
          >
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-[#E5EDF8]">
                {item.label}
              </p>
              <span className="text-sm font-semibold text-[#9AA8BA]">
                {percent(item.display)}
              </span>
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#061426]">
              <div
                className={`h-full rounded-full ${item.color}`}
                style={{
                  width: `${Math.min(Math.max(item.value, 0), 1) * 100}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
