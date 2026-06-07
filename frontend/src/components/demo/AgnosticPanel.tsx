import ImageWithFallback from "./ImageWithFallback";
import type { DemoAnalysis, DemoImageSet } from "@/lib/types";

type AgnosticPanelProps = {
  images: DemoImageSet;
  analysis: DemoAnalysis;
};

export default function AgnosticPanel({ images, analysis }: AgnosticPanelProps) {
  const cards = [
    {
      label: "Agnostic Person",
      alt: "Agnostic person representation",
      src: images.agnostic,
    },
    {
      label: "Agnostic Mask",
      alt: "Agnostic mask representation",
      src: images.agnostic_mask,
    },
    {
      label: "Image Parse",
      alt: "Image parse placeholder",
      src: undefined,
    },
    {
      label: "Cloth Mask",
      alt: "Cloth mask placeholder",
      src: undefined,
    },
  ];

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_300px]">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <div
            className="rounded-2xl border border-[#6EA5FF]/18 bg-[#0C1C34]/70 p-3"
            key={card.label}
          >
            <ImageWithFallback
              alt={card.alt}
              aspectClass="h-[200px]"
              label={card.label}
              src={card.src}
            />
            <p className="mt-3 text-sm font-semibold text-[#E5EDF8]">
              {card.label}
            </p>
          </div>
        ))}
      </div>
      <div className="rounded-2xl border border-[#6EA5FF]/18 bg-[#0C1C34]/70 p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-[#38BDF8]">
          Agnostic Mask
        </p>
        <h3 className="mt-3 text-xl font-semibold text-[#E5EDF8]">
          Mask Conditioning
        </h3>
        <p className="mt-3 text-sm leading-6 text-[#9AA8BA]">
          {analysis.agnostic_note}
        </p>
      </div>
    </div>
  );
}
