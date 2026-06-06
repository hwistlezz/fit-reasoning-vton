"use client";

import Image from "next/image";
import { useState } from "react";

type ImageWithFallbackProps = {
  src?: string;
  alt: string;
  label: string;
  aspectClass?: string;
  className?: string;
  imageClassName?: string;
  priority?: boolean;
};

export default function ImageWithFallback({
  src,
  alt,
  label,
  aspectClass = "aspect-[3/4]",
  className = "",
  imageClassName = "object-cover",
  priority = false,
}: ImageWithFallbackProps) {
  const [failedSrc, setFailedSrc] = useState<string | undefined>();

  const showFallback = !src || failedSrc === src;

  return (
    <div
      className={[
        "relative flex w-full overflow-hidden rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/80",
        aspectClass,
        className,
      ].join(" ")}
    >
      {showFallback ? (
        <div className="flex h-full w-full flex-col items-center justify-center gap-3 bg-[linear-gradient(145deg,rgba(8,20,38,0.95),rgba(12,28,52,0.82))] p-5 text-center">
          <div className="h-12 w-12 rounded-full border border-[#6EA5FF]/30 bg-[#5B8CFF]/10 shadow-[0_0_28px_rgba(91,140,255,0.18)]" />
          <div>
            <p className="text-sm font-semibold text-[#E5EDF8]">{label}</p>
            <p className="mt-1 text-xs leading-5 text-[#9AA8BA]">{alt}</p>
          </div>
        </div>
      ) : (
        <Image
          alt={alt}
          className={imageClassName}
          fill
          onError={() => setFailedSrc(src)}
          priority={priority}
          sizes="(max-width: 768px) 100vw, (max-width: 1280px) 40vw, 24vw"
          src={src}
        />
      )}
    </div>
  );
}
