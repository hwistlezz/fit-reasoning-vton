"use client";

import { usePathname, useRouter } from "next/navigation";
import type { DemoSample } from "@/lib/types";

type PairSelectorProps = {
  samples: DemoSample[];
  selectedPairId: string;
  compact?: boolean;
};

export default function PairSelector({
  samples,
  selectedPairId,
  compact = false,
}: PairSelectorProps) {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <label className="flex w-full flex-col gap-2">
      <span className="text-xs font-medium uppercase tracking-[0.18em] text-[#38BDF8]">
        Sample Selector
      </span>
      <select
        className={[
          "w-full rounded-lg border border-[#6EA5FF]/24 bg-[#081426]/90 text-[#E5EDF8] outline-none transition focus:border-[#5B8CFF] focus:ring-2 focus:ring-[#5B8CFF]/20",
          compact ? "px-3 py-2 text-sm" : "px-4 py-3 text-base",
        ].join(" ")}
        onChange={(event) => {
          router.push(`${pathname}?pairId=${encodeURIComponent(event.target.value)}`);
        }}
        value={selectedPairId}
      >
        {samples.map((sample) => (
          <option key={sample.pair_id} value={sample.pair_id}>
            {sample.pair_id} · {sample.category}
          </option>
        ))}
      </select>
    </label>
  );
}
