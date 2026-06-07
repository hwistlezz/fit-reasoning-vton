"use client";

import { useState } from "react";
import AgnosticPanel from "./AgnosticPanel";
import DensePosePanel from "./DensePosePanel";
import FitDetailsPanel from "./FitDetailsPanel";
import HotspotPanel from "./HotspotPanel";
import ImageWithFallback from "./ImageWithFallback";
import ReliabilityPanel from "./ReliabilityPanel";
import SkeletonOverlay from "./SkeletonOverlay";
import type { DemoAnalysis, DemoImageSet } from "@/lib/types";

type TabKey =
  | "hotspot"
  | "skeleton"
  | "densepose"
  | "agnostic"
  | "reliability"
  | "fit";

type DetailedAnalysisTabsProps = {
  analysis: DemoAnalysis;
  defaultTab: TabKey;
  images: DemoImageSet;
};

const tabs: { key: TabKey; label: string }[] = [
  { key: "hotspot", label: "Hotspot" },
  { key: "skeleton", label: "Skeleton" },
  { key: "densepose", label: "DensePose" },
  { key: "agnostic", label: "Agnostic Mask" },
  { key: "reliability", label: "Reliability" },
  { key: "fit", label: "Fit Details" },
];

export default function DetailedAnalysisTabs({
  analysis,
  defaultTab,
  images,
}: DetailedAnalysisTabsProps) {
  const [activeTab, setActiveTab] = useState<TabKey>(defaultTab);

  return (
    <section className="rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/80 p-4 shadow-[0_0_30px_rgba(30,80,160,0.12)] backdrop-blur">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[#38BDF8]">
            Detailed Analysis
          </p>
          <h2 className="mt-2 text-xl font-semibold text-[#E5EDF8]">
            Conditioning & Reliability Analysis
          </h2>
        </div>
        <div className="flex flex-wrap gap-2">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.key;

            return (
              <button
                className={[
                  "rounded-lg border px-3 py-2 text-sm font-medium transition",
                  isActive
                    ? "border-[#5B8CFF]/70 bg-[#5B8CFF]/16 text-[#E5EDF8]"
                    : "border-[#6EA5FF]/16 bg-[#0C1C34]/70 text-[#9AA8BA] hover:text-[#E5EDF8]",
                ].join(" ")}
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                type="button"
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-5">
        {activeTab === "hotspot" ? (
          <HotspotPanel
            hotspots={analysis.hotspots}
            imageSrc={images.enhanced_result}
          />
        ) : null}
        {activeTab === "skeleton" ? (
          <div className="grid items-stretch gap-4 lg:grid-cols-[minmax(0,420px)_1fr]">
            <div className="relative min-h-[360px] overflow-hidden rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/80">
              <ImageWithFallback
                alt="Enhanced StableVITON result with skeleton overlay"
                aspectClass="h-full min-h-[360px]"
                className="border-0"
                imageClassName="object-cover object-top"
                label="Skeleton overlay"
                src={images.enhanced_result}
              />
              <SkeletonOverlay keypoints={analysis.keypoints} />
            </div>
            <div className="rounded-2xl border border-[#6EA5FF]/18 bg-[#0C1C34]/70 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-[#38BDF8]">
                OpenPose
              </p>
              <h3 className="mt-3 text-xl font-semibold text-[#E5EDF8]">
                Percent-coordinate skeleton
              </h3>
              <p className="mt-3 text-sm leading-6 text-[#9AA8BA]">
                OpenPose keypoint를 오버레이해 어깨, 팔꿈치, 손목, 골반의
                정렬 상태를 확인하고 생성 결과의 자세 안정성을 비교합니다.
              </p>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {analysis.keypoints.map((point) => (
                  <div
                    className="flex items-center justify-between rounded-lg border border-[#6EA5FF]/12 bg-[#061426]/70 px-3 py-2 text-sm"
                    key={point.name}
                  >
                    <span className="text-[#9AA8BA]">{point.name}</span>
                    <span className="font-semibold text-[#E5EDF8]">
                      {Math.round(point.confidence * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}
        {activeTab === "densepose" ? (
          <DensePosePanel analysis={analysis} images={images} />
        ) : null}
        {activeTab === "agnostic" ? (
          <AgnosticPanel analysis={analysis} images={images} />
        ) : null}
        {activeTab === "reliability" ? (
          <ReliabilityPanel reliability={analysis.reliability} />
        ) : null}
        {activeTab === "fit" ? <FitDetailsPanel fit={analysis.fit} /> : null}
      </div>
    </section>
  );
}
