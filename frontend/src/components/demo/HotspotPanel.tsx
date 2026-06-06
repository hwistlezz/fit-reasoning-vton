import HotspotOverlay from "./HotspotOverlay";
import ImageWithFallback from "./ImageWithFallback";
import type { Hotspot } from "@/lib/types";

type HotspotPanelProps = {
  imageSrc?: string;
  hotspots: Hotspot[];
};

export default function HotspotPanel({ imageSrc, hotspots }: HotspotPanelProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1.05fr)_minmax(280px,0.95fr)]">
      <div className="relative overflow-hidden rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/80">
        <ImageWithFallback
          alt="Enhanced StableVITON result with hotspot overlay"
          aspectClass="aspect-[3/4]"
          className="border-0"
          label="Enhanced result"
          src={imageSrc}
        />
        <HotspotOverlay hotspots={hotspots} />
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
        {hotspots.map((hotspot) => (
          <div
            className="rounded-2xl border border-[#6EA5FF]/18 bg-[#0C1C34]/70 p-4"
            key={hotspot.key}
          >
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold text-[#E5EDF8]">
                {hotspot.label}
              </h3>
              {hotspot.value ? (
                <span className="rounded-lg border border-[#74C365]/25 bg-[#74C365]/10 px-2 py-1 text-xs font-semibold text-[#A7E39C]">
                  {hotspot.value}
                </span>
              ) : null}
            </div>
            <p className="mt-2 text-sm leading-6 text-[#9AA8BA]">
              {hotspot.text}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
