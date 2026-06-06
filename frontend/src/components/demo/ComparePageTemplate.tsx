"use client";

import CaseInputPanel from "./CaseInputPanel";
import DetailedAnalysisTabs from "./DetailedAnalysisTabs";
import MetricCard from "./MetricCard";
import PairSelector from "./PairSelector";
import ResultCard from "./ResultCard";
import RiskGaugeCard from "./RiskGaugeCard";
import PageShell from "@/components/layout/PageShell";
import type { DemoCompareResponse, DemoMetric, DemoSample } from "@/lib/types";

type ComparePageTemplateProps = {
  data: DemoCompareResponse;
  samples: DemoSample[];
};

const pageConfig = {
  eyebrow: "Model Compare",
  title: "StableVITON Result Comparison",
  subtitle:
    "동일한 입력에서 실제 착용 이미지, 기본 StableVITON 결과, 10k Agnostic + DensePose 개선 결과를 비교합니다.",
  defaultTab: "densepose" as const,
  results: [
    {
      title: "Target Worn",
      helper: "실제 착용 참고 이미지",
      caption: "실제 사람이 해당 의류를 착용한 기준 이미지입니다.",
      imageKey: "target_worn" as const,
      variant: "blue" as const,
      badgeLabel: "Reference",
    },
    {
      title: "StableVITON",
      helper: "기본 모델 결과",
      caption: "기본 StableVITON 추론 결과입니다.",
      imageKey: "stableviton" as const,
      variant: "orange" as const,
      badgeLabel: "Base",
    },
    {
      title: "Enhanced Result",
      helper: "Agnostic + DensePose",
      caption: "Agnostic mask와 DensePose 조건을 활용한 개선 결과입니다.",
      imageKey: "enhanced_result" as const,
      variant: "green" as const,
      badgeLabel: "Enhanced",
    },
  ],
};

function isRiskMetric(metric: DemoMetric) {
  const title = metric.title.toLowerCase();
  return title.includes("risk") || title.includes("reduction");
}

export default function ComparePageTemplate({
  data,
  samples,
}: ComparePageTemplateProps) {
  return (
    <PageShell>
      <section className="grid gap-5 rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/70 p-5 shadow-[0_0_30px_rgba(30,80,160,0.12)] backdrop-blur lg:grid-cols-[1fr_340px] lg:items-end">
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
        <PairSelector samples={samples} selectedPairId={data.pair_id} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
        <CaseInputPanel
          demoCase={data.case}
          images={data.images}
        />
        <div className="grid gap-4 lg:grid-cols-3">
          {pageConfig.results.map((result) => (
            <ResultCard
              caption={result.caption}
              helper={result.helper}
              badgeLabel={result.badgeLabel}
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

      <footer className="rounded-2xl border border-[#6EA5FF]/16 bg-[#081426]/60 px-5 py-4 text-sm leading-6 text-[#9AA8BA]">
        Metrics are computed on curated demo samples. Confidence is an
        analytical estimate, not a guarantee.
        <br />
        Metrics are computed on curated demo samples and used for qualitative
        presentation.
      </footer>
    </PageShell>
  );
}
