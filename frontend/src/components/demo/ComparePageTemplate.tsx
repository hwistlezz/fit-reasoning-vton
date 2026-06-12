"use client";

import CaseInputPanel from "./CaseInputPanel";
import DetailedAnalysisTabs from "./DetailedAnalysisTabs";
import MetricCard from "./MetricCard";
import ResultCard from "./ResultCard";
import RiskGaugeCard from "./RiskGaugeCard";
import PageShell from "@/components/layout/PageShell";
import type { UploadInputs } from "./ComparePageClient";
import type {
  DemoCompareResponse,
  DemoMetric,
  UploadSlotKey,
} from "@/lib/types";

type ComparePageTemplateProps = {
  canRunComparison: boolean;
  data: DemoCompareResponse;
  isRunning: boolean;
  onFileChange: (slot: UploadSlotKey, file?: File) => void;
  onResetInputs: () => void;
  onRunComparison: () => void;
  uploadError?: string;
  uploadJobId?: string;
  uploadProgress: number;
  uploadProgressLabel?: string;
  uploads: UploadInputs;
  uploadStatus: string;
};

const demoFallbackText =
  "데모 결과 이미지를 public/local-demo-vton 폴더에 추가해 주세요.";

const pageConfig = {
  eyebrow: "Live Try-On",
  title: "Virtual Try-On Comparison Result",
  subtitle:
    "입력 이미지, 정답 이미지, StableVITON 기본 결과, StableVITON+LoRA 결과를 비교합니다.",
  defaultTab: "hotspot" as const,
  results: [
    {
      title: "Ground Truth",
      helper: "Uploaded Reference",
      caption:
        "실제 착용 또는 목표 결과로 사용하는 기준 이미지입니다. 사용자가 업로드한 세 번째 이미지를 그대로 표시합니다.",
      imageKey: "target_worn" as const,
      variant: "blue" as const,
      badgeLabel: "Reference",
    },
    {
      title: "StableVITON",
      helper: "Base Model",
      caption:
        "기본 StableVITON 결과입니다. 전체 착장은 가능하지만 비정면 자세에서는 그래픽 정렬, 소매 경계, 밑단 표현이 다소 불안정할 수 있습니다.",
      imageKey: "stableviton" as const,
      variant: "orange" as const,
      badgeLabel: "Baseline",
      confidenceLevel: "Medium",
      confidenceScore: 72,
    },
    {
      title: "StableVITON + LoRA",
      helper: "Enhanced Model",
      caption:
        "LoRA를 적용한 결과입니다. 동일한 입력 조건에서 착장 색감, 그래픽 위치, 소매와 밑단 경계를 더 안정적으로 복원하는 것을 목표로 합니다.",
      imageKey: "enhanced_result" as const,
      variant: "green" as const,
      badgeLabel: "LoRA-enhanced",
      confidenceLevel: "High",
      confidenceScore: 86,
    },
  ],
};

function isRiskMetric(metric: DemoMetric) {
  const title = metric.title.toLowerCase();
  return title.includes("risk") || title.includes("reduction");
}

function hideGeneratedImages(data: DemoCompareResponse) {
  return {
    ...data.images,
    target_worn: "",
    stableviton: "",
    enhanced_result: "",
    hotspot: undefined,
    skeleton: undefined,
    densepose: undefined,
    skeleton_preview: undefined,
    agnostic: undefined,
    agnostic_mask: undefined,
    upper_body_mask: undefined,
    human_parsing_map: undefined,
    cloth_mask: undefined,
    densepose_overlay: undefined,
    agnostic_overlay: undefined,
  };
}

export default function ComparePageTemplate({
  canRunComparison,
  data,
  isRunning,
  onFileChange,
  onResetInputs,
  onRunComparison,
  uploadError,
  uploadJobId,
  uploadProgress,
  uploadProgressLabel,
  uploads,
  uploadStatus,
}: ComparePageTemplateProps) {
  const showResultScores = uploadStatus === "done";
  const visibleImages = showResultScores ? data.images : hideGeneratedImages(data);

  return (
    <PageShell>
      <section className="grid gap-5 rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/70 p-5 shadow-[0_0_30px_rgba(30,80,160,0.12)] backdrop-blur lg:grid-cols-[1fr_320px] lg:items-end">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-[#38BDF8]">
            {pageConfig.eyebrow}
          </p>
          <h1 className="mt-3 max-w-4xl text-3xl font-semibold leading-tight text-[#E5EDF8] sm:text-4xl">
            {pageConfig.title}
          </h1>
          <p className="mt-3 max-w-3xl text-base leading-7 text-[#9AA8BA]">
            {pageConfig.subtitle}
          </p>
        </div>
        <div className="rounded-xl border border-[#6EA5FF]/18 bg-[#061426]/70 px-4 py-3 text-sm leading-6 text-[#9AA8BA]">
          <span className="font-semibold text-[#E5EDF8]">Upload Input</span>
          <br />
          Person / Cloth / Ground Truth images
        </div>
      </section>

      <section className="grid items-start gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
        <CaseInputPanel
          canRunComparison={canRunComparison}
          isRunning={isRunning}
          onFileChange={onFileChange}
          onResetInputs={onResetInputs}
          onRunComparison={onRunComparison}
          uploadError={uploadError}
          uploadJobId={uploadJobId}
          uploadProgress={uploadProgress}
          uploadProgressLabel={uploadProgressLabel}
          uploads={uploads}
          uploadStatus={uploadStatus}
        />
        <div className="grid auto-rows-fr items-stretch gap-4 lg:grid-cols-3">
          {pageConfig.results.map((result) => (
            <ResultCard
              badgeLabel={result.badgeLabel}
              caption={result.caption}
              confidenceLevel={
                showResultScores ? result.confidenceLevel : undefined
              }
              confidenceScore={
                showResultScores ? result.confidenceScore : undefined
              }
              fallbackText={demoFallbackText}
              helper={result.helper}
              imageSrc={visibleImages[result.imageKey] || undefined}
              key={result.title}
              title={result.title}
              variant={result.variant}
            />
          ))}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
        {data.metrics.map((metric) =>
          isRiskMetric(metric) ? (
            <RiskGaugeCard key={metric.key} metric={metric} />
          ) : (
            <MetricCard key={metric.key} metric={metric} />
          ),
        )}
      </section>

      <DetailedAnalysisTabs
        analysis={data.analysis}
        defaultTab={pageConfig.defaultTab}
        images={visibleImages}
      />

      <section className="grid gap-4 rounded-2xl border border-[#F97316]/25 bg-[#F97316]/10 p-4 text-sm leading-6 text-[#FED7AA] md:grid-cols-[260px_1fr]">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[#FDBA74]">
            Low-risk warning
          </p>
          <h2 className="mt-2 text-lg font-semibold text-[#E5EDF8]">
            비정면 자세 안내
          </h2>
        </div>
        <div>
          <p>
            비정면 자세와 손에 든 물체로 인해 소매 길이와 팔 주변 경계
            분석은 실제 환경에서 오차가 발생할 수 있습니다. 정면 전신 사진을
            사용하면 더 안정적인 결과를 얻을 수 있습니다.
          </p>
        </div>
      </section>
    </PageShell>
  );
}
