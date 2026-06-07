import ImageWithFallback from "./ImageWithFallback";

type Variant = "blue" | "orange" | "green" | "violet";

type ResultCardProps = {
  title: string;
  helper: string;
  caption: string;
  badgeLabel: string;
  imageSrc?: string;
  variant: Variant;
};

const variantStyles: Record<Variant, string> = {
  blue: "border-[#5B8CFF]/45 bg-[#5B8CFF]/12 text-[#BFD0FF]",
  orange: "border-[#F97316]/45 bg-[#F97316]/12 text-[#FDBA74]",
  green: "border-[#74C365]/45 bg-[#74C365]/12 text-[#B9F5AF]",
  violet: "border-[#A78BFA]/45 bg-[#A78BFA]/12 text-[#DDD6FE]",
};

export default function ResultCard({
  title,
  helper,
  caption,
  badgeLabel,
  imageSrc,
  variant,
}: ResultCardProps) {
  return (
    <article className="flex h-full min-h-[410px] min-w-0 flex-col rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/80 p-3 shadow-[0_0_30px_rgba(30,80,160,0.12)] backdrop-blur xl:min-h-[430px]">
      <div className="mb-3 flex h-[88px] shrink-0 items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-[15px] font-semibold leading-5 text-[#E5EDF8]">
            {title}
          </h3>
          <p className="mt-1 text-xs font-medium text-[#9AA8BA]">{helper}</p>
        </div>
        <span
          className={[
            "shrink-0 rounded-lg border px-2 py-1 text-xs font-medium",
            variantStyles[variant],
          ].join(" ")}
        >
          {badgeLabel}
        </span>
      </div>
      <ImageWithFallback
        alt={`${title} preview`}
        aspectClass="min-h-[230px] flex-1"
        imageClassName="object-cover object-top"
        label={title}
        src={imageSrc}
      />
      <div
        className={[
          "mt-3 h-[76px] shrink-0 rounded-lg border px-3 py-2 text-sm leading-5",
          variantStyles[variant],
        ].join(" ")}
      >
        {caption}
      </div>
    </article>
  );
}
