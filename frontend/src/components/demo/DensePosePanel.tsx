import ImageWithFallback from "./ImageWithFallback";
import type { DemoAnalysis, DemoImageSet } from "@/lib/types";

type DensePosePanelProps = {
  images: DemoImageSet;
  analysis: DemoAnalysis;
};

export default function DensePosePanel({ images, analysis }: DensePosePanelProps) {
  const cards = [
    {
      label: "DensePose",
      alt: "DensePose input preview",
      src: images.densepose,
    },
    {
      label: "Skeleton Preview",
      alt: "OpenPose skeleton preview",
      src: images.skeleton_preview,
    },
    {
      label: "Enhanced Result",
      alt: "Agnostic + DensePose enhanced result preview",
      src: images.enhanced_result,
    },
  ];

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
      <div className="grid gap-4 md:grid-cols-3">
        {cards.map((card) => (
          <div
            className="rounded-2xl border border-[#6EA5FF]/18 bg-[#0C1C34]/70 p-3"
            key={card.label}
          >
            <ImageWithFallback alt={card.alt} label={card.label} src={card.src} />
            <p className="mt-3 text-sm font-semibold text-[#E5EDF8]">
              {card.label}
            </p>
          </div>
        ))}
      </div>
      <div className="rounded-2xl border border-[#6EA5FF]/18 bg-[#0C1C34]/70 p-5">
        <p className="text-xs uppercase tracking-[0.2em] text-[#38BDF8]">
          DensePose
        </p>
        <h3 className="mt-3 text-xl font-semibold text-[#E5EDF8]">
          {analysis.pose.label}
        </h3>
        <p className="mt-3 text-sm leading-6 text-[#9AA8BA]">
          {analysis.densepose_note}
        </p>
        <p className="mt-4 text-sm leading-6 text-[#9AA8BA]">
          {analysis.pose.summary}
        </p>
      </div>
    </div>
  );
}
