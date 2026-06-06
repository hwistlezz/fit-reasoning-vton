import ImageWithFallback from "./ImageWithFallback";
import type { DemoCase, DemoImageSet } from "@/lib/types";

type CaseInputPanelProps = {
  demoCase: DemoCase;
  images: DemoImageSet;
};

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function badgeClass(kind: "green" | "orange" | "blue") {
  const styles = {
    blue: "border-[#5B8CFF]/30 bg-[#5B8CFF]/12 text-[#9DB8FF]",
    green: "border-[#74C365]/30 bg-[#74C365]/12 text-[#A7E39C]",
    orange: "border-[#F97316]/30 bg-[#F97316]/12 text-[#FDBA74]",
  };

  return `rounded-lg border px-2 py-1 text-xs font-medium ${styles[kind]}`;
}

function MetadataRow({
  label,
  value,
  badge,
}: {
  label: string;
  value: string;
  badge?: "green" | "orange" | "blue";
}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-[#6EA5FF]/10 py-3 last:border-b-0">
      <span className="text-sm text-[#9AA8BA]">{label}</span>
      {badge ? (
        <span className={badgeClass(badge)}>{value}</span>
      ) : (
        <span className="text-right text-sm font-medium text-[#E5EDF8]">
          {value}
        </span>
      )}
    </div>
  );
}

export default function CaseInputPanel({
  demoCase,
  images,
}: CaseInputPanelProps) {
  const difficultyBadge = demoCase.difficulty === "High" ? "orange" : "blue";
  const confidenceBadge = demoCase.input_confidence >= 0.88 ? "green" : "orange";

  return (
    <aside className="rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/80 p-4 shadow-[0_0_30px_rgba(30,80,160,0.12)] backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[#38BDF8]">
            SELECTED CASE
          </p>
          <h2 className="mt-2 text-lg font-semibold text-[#E5EDF8]">
            {demoCase.pair_id}
          </h2>
        </div>
        <span className={badgeClass(confidenceBadge)}>
          {percent(demoCase.input_confidence)}
        </span>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <ImageWithFallback
          alt="Preview unavailable"
          aspectClass="aspect-[3/4]"
          label="Person Image"
          src={images.person}
        />
        <ImageWithFallback
          alt="Preview unavailable"
          aspectClass="aspect-[3/4]"
          label="Cloth Image"
          src={images.cloth}
        />
      </div>

      <div className="mt-5 rounded-2xl border border-[#6EA5FF]/16 bg-[#0C1C34]/70 px-4">
        <MetadataRow label="Pair ID" value={demoCase.pair_id} />
        <MetadataRow label="Category" value={demoCase.category} />
        <MetadataRow label="Pose Type" value={demoCase.pose_type} />
        <MetadataRow
          badge={difficultyBadge}
          label="Difficulty"
          value={demoCase.difficulty}
        />
        <MetadataRow
          badge="green"
          label="GT Fit Label"
          value={demoCase.gt_fit_label}
        />
        <MetadataRow
          badge={confidenceBadge}
          label="Input Confidence"
          value={percent(demoCase.input_confidence)}
        />
      </div>
    </aside>
  );
}
