"use client";

import { useState } from "react";
import type { Hotspot } from "@/lib/types";

type HotspotOverlayProps = {
  hotspots: Hotspot[];
};

export default function HotspotOverlay({ hotspots }: HotspotOverlayProps) {
  const [activeKey, setActiveKey] = useState<string | null>(null);

  return (
    <div className="pointer-events-none absolute inset-0">
      {hotspots.map((hotspot) => {
        const isActive = activeKey === hotspot.key;

        return (
          <button
            aria-label={hotspot.label}
            className="pointer-events-auto absolute h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/80 bg-[#74C365] shadow-[0_0_20px_rgba(116,195,101,0.65)] outline-none ring-4 ring-[#74C365]/20 transition hover:scale-110 focus:scale-110"
            key={hotspot.key}
            onClick={() => setActiveKey(isActive ? null : hotspot.key)}
            onMouseEnter={() => setActiveKey(hotspot.key)}
            onMouseLeave={() => setActiveKey(null)}
            style={{ left: `${hotspot.x}%`, top: `${hotspot.y}%` }}
            type="button"
          >
            <span className="sr-only">{hotspot.label}</span>
            {isActive ? (
              <span className="absolute left-1/2 top-6 z-20 w-52 -translate-x-1/2 rounded-lg border border-[#6EA5FF]/25 bg-[#020817]/95 p-3 text-left shadow-[0_16px_40px_rgba(0,0,0,0.35)]">
                <span className="block text-xs font-semibold text-[#E5EDF8]">
                  {hotspot.label}
                </span>
                <span className="mt-1 block text-xs leading-5 text-[#9AA8BA]">
                  {hotspot.text}
                </span>
                {hotspot.value ? (
                  <span className="mt-2 block text-xs font-semibold text-[#74C365]">
                    {hotspot.value}
                  </span>
                ) : null}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
