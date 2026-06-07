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
  onRunComparison: () => void;
  uploadError?: string;
  uploadJobId?: string;
  uploads: UploadInputs;
  uploadStatus: string;
};

const pageConfig = {
  eyebrow: "Live Try-On",
  title: "StableVITON Comparison Results",
  subtitle:
    "입력 이미지를 업로드하면 기본 StableVITON 결과와 StableVITON Lora 결과를 비교합니다.",
  defaultTab: "densepose" as const,
  results: [
    {
      title: "Target Worn",
      helper: "Ground Truth",
      caption: "실제 착용 이미지를 기준으로 결과를 비교합니다.",
      imageKey: "target_worn" as const,
      variant: "blue" as const,
      badgeLabel: "Reference",
    },
    {
      title: "StableVITON",
      helper: "Base Model",
      caption: "기본 StableVITON 추론 결과입니다.",
      imageKey: "stableviton" as const,
      variant: "orange" as const,
      badgeLabel: "Base",
    },
    {
      title: "StableVITON LoRA",
      helper: "Enhanced Model",
      caption: "StableVITON LoRA 모델을 사용한 개선 결과입니다.",
      imageKey: "enhanced_result" as const,
      variant: "green" as const,
      badgeLabel: "LoRA",
    },
  ],
};

function isRiskMetric(metric: DemoMetric) {
  const title = metric.title.toLowerCase();
  return title.includes("risk") || title.includes("reduction");
}

export default function ComparePageTemplate({
  canRunComparison,
  data,
  isRunning,
  onFileChange,
  onRunComparison,
  uploadError,
  uploadJobId,
  uploads,
  uploadStatus,
}: ComparePageTemplateProps) {
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
          Person / Cloth / Worn images
        </div>
      </section>

      <section className="grid items-start gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
        <CaseInputPanel
          canRunComparison={canRunComparison}
          isRunning={isRunning}
          onFileChange={onFileChange}
          onRunComparison={onRunComparison}
          uploadError={uploadError}
          uploadJobId={uploadJobId}
          uploads={uploads}
          uploadStatus={uploadStatus}
        />
        <div className="grid auto-rows-fr items-stretch gap-4 lg:grid-cols-3">
          {pageConfig.results.map((result) => (
            <ResultCard
              badgeLabel={result.badgeLabel}
              caption={result.caption}
              helper={result.helper}
              imageSrc={data.images[result.imageKey]}
              key={result.title}
              title={result.title}
              variant={result.variant}
            />
          ))}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
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
        images={data.images}
      />
    </PageShell>
  );
}
