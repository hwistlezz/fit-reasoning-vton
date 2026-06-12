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
  fallbackText?: string;
  priority?: boolean;
};

export default function ImageWithFallback({
  src,
  alt,
  label,
  aspectClass = "aspect-[3/4]",
  className = "",
  imageClassName = "object-cover",
  fallbackText = "이미지를 불러올 수 없습니다.",
  priority = false,
}: ImageWithFallbackProps) {
  const [failedSrc, setFailedSrc] = useState<string | undefined>();

  const showFallback = !src || failedSrc === src;
  const isLocalPreview =
    typeof src === "string" &&
    (src.startsWith("blob:") || src.startsWith("data:"));

  return (
    <div
      className={[
        "relative flex w-full overflow-hidden rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/80",
        aspectClass,
        className,
      ].join(" ")}
    >
      {showFallback ? (
        <div className="relative flex h-full w-full items-stretch justify-stretch bg-[linear-gradient(145deg,rgba(8,20,38,0.98),rgba(12,28,52,0.9))] p-3 text-center">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(91,140,255,0.18),transparent_42%)]" />
          <div className="relative grid h-full w-full place-items-center rounded-xl border border-dashed border-[#6EA5FF]/30 bg-[#061426]/45 px-4 py-6">
            <div>
              <div className="mx-auto mb-3 h-1.5 w-16 rounded-full bg-[#5B8CFF]/35" />
              <p className="text-sm font-semibold text-[#E5EDF8]">{label}</p>
              <p className="mt-1 text-xs leading-5 text-[#9AA8BA]">
                {fallbackText}
              </p>
            </div>
          </div>
        </div>
      ) : isLocalPreview ? (
        // next/image does not optimize local object URLs created by file inputs.
        // eslint-disable-next-line @next/next/no-img-element
        <img alt={alt} className={`h-full w-full ${imageClassName}`} src={src} />
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
