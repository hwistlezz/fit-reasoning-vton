import type { DemoReliability } from "@/lib/types";

type ReliabilityPanelProps = {
  reliability: DemoReliability;
};

const reliabilityItems = [
  {
    label: "Input Quality",
    score: 82,
    description:
      "입력 이미지는 전신이 보이지만 비정면 자세와 손에 든 물체로 인해 일부 영역이 가려져 있습니다.",
  },
  {
    label: "Pose Confidence",
    score: 78,
    description:
      "비정면 자세이므로 정면 입력보다 자세 정렬 난이도가 높습니다.",
  },
  {
    label: "Garment Alignment",
    score: 86,
    description:
      "LoRA 결과에서 상의 중심선과 그래픽 위치가 비교적 안정적으로 유지됩니다.",
  },
  {
    label: "Boundary Stability",
    score: 84,
    description:
      "소매와 밑단 경계가 baseline보다 더 명확하게 유지됩니다.",
  },
];

export default function ReliabilityPanel({
  reliability,
}: ReliabilityPanelProps) {
  const overallScore = Math.round(reliability.result_reliability * 100);

  return (
    <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
      <div className="rounded-2xl border border-[#74C365]/25 bg-[#74C365]/10 p-5">
        <p className="text-sm font-medium text-[#A7E39C]">
          Result reliability score
        </p>
        <p className="mt-3 text-5xl font-semibold text-[#E5EDF8]">
          {overallScore}
        </p>
        <p className="mt-4 text-sm leading-6 text-[#9AA8BA]">
          자세 가시성, 의류 정렬, 경계 안정성, 가림 위험을 함께 반영한
          데모용 신뢰도 점수입니다.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {reliabilityItems.map((item) => (
          <div
            className="rounded-2xl border border-[#6EA5FF]/18 bg-[#0C1C34]/70 p-4"
            key={item.label}
          >
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-[#E5EDF8]">
                {item.label}
              </p>
              <span className="rounded-lg border border-[#74C365]/25 bg-[#74C365]/10 px-2 py-1 text-sm font-semibold text-[#A7E39C]">
                {item.score}
              </span>
            </div>
            <p className="mt-3 text-sm leading-6 text-[#9AA8BA]">
              {item.description}
            </p>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#061426]">
              <div
                className="h-full rounded-full bg-[#74C365]"
                style={{ width: `${item.score}%` }}
              />
            </div>
          </div>
        ))}
        <div className="rounded-2xl border border-[#F97316]/25 bg-[#F97316]/10 p-4 text-sm leading-6 text-[#FED7AA] sm:col-span-2">
          비정면 자세와 물체 가림이 있는 입력에서는 실제 모델에서 소매 길이,
          팔 주변 경계, 그래픽 왜곡 분석에 오차가 발생할 수 있습니다.
        </div>
      </div>
    </div>
  );
}
