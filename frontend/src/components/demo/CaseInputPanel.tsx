import ImageWithFallback from "./ImageWithFallback";
import type { UploadInputs } from "./ComparePageClient";
import type { UploadSlotKey } from "@/lib/types";

type CaseInputPanelProps = {
  canRunComparison: boolean;
  isRunning: boolean;
  onFileChange: (slot: UploadSlotKey, file?: File) => void;
  onResetInputs: () => void;
  onRunComparison: () => void;
  uploadError?: string;
  uploadJobId?: string;
  uploadProgress: number;
  uploadProgressLabel?: string;
  uploads: UploadInputs;
  uploadStatus: string;
};

const uploadCards: {
  slot: UploadSlotKey;
  title: string;
  description: string;
}[] = [
  {
    slot: "person",
    title: "사람 이미지",
    description: "가상 착장에 사용할 사람 이미지를 업로드하세요.",
  },
  {
    slot: "cloth",
    title: "의류 이미지",
    description: "착용시킬 상의 이미지를 업로드하세요.",
  },
  {
    slot: "worn",
    title: "정답 착용 이미지",
    description: "결과 비교 기준으로 사용할 ground truth 이미지입니다.",
  },
];

function safeText(value?: string | number) {
  if (value === undefined || value === null || value === "") {
    return "-";
  }

  return String(value);
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    idle: "입력 대기",
    ready: "분석 준비",
    uploading: "입력 확인 중",
    preprocessing: "조건 정렬 중",
    stableviton: "StableVITON 준비",
    enhanced: "LoRA 비교 중",
    done: "완료",
    failed: "Fallback",
  };

  return labels[status] ?? status;
}

function UploadCard({
  description,
  fileName,
  onFileChange,
  previewUrl,
  slot,
  title,
}: {
  description: string;
  fileName?: string;
  onFileChange: (slot: UploadSlotKey, file?: File) => void;
  previewUrl?: string;
  slot: UploadSlotKey;
  title: string;
}) {
  function handleFiles(files?: FileList | null) {
    onFileChange(slot, files?.[0]);
  }

  return (
    <label
      className="group block cursor-pointer rounded-2xl border border-dashed border-[#6EA5FF]/35 bg-[#0C1C34]/60 p-3 transition hover:border-[#5B8CFF]/70 hover:bg-[#0C1C34]/85"
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        handleFiles(event.dataTransfer.files);
      }}
    >
      <input
        accept="image/*"
        className="sr-only"
        onChange={(event) => handleFiles(event.target.files)}
        type="file"
      />
      {previewUrl ? (
        <ImageWithFallback
          alt={`${title} preview`}
          aspectClass="h-28"
          className="rounded-xl"
          imageClassName="object-contain bg-white"
          label={title}
          src={previewUrl}
        />
      ) : (
        <div className="grid h-28 place-items-center rounded-xl border border-[#6EA5FF]/14 bg-[#061426]/70 text-center">
          <div>
            <div className="mx-auto grid h-9 w-9 place-items-center rounded-full border border-[#6EA5FF]/30 bg-[#5B8CFF]/10 text-xl font-light text-[#BFD0FF]">
              +
            </div>
            <p className="mt-2 text-sm font-semibold text-[#E5EDF8]">{title}</p>
            <p className="mt-1 px-2 text-xs leading-5 text-[#9AA8BA]">
              {description}
            </p>
          </div>
        </div>
      )}
      {previewUrl ? (
        <div className="mt-2">
          <p className="text-sm font-semibold text-[#E5EDF8]">{title}</p>
          <p className="truncate text-xs leading-5 text-[#9AA8BA]">
            {fileName ?? "Preview ready"}
          </p>
        </div>
      ) : null}
    </label>
  );
}

export default function CaseInputPanel({
  canRunComparison,
  isRunning,
  onFileChange,
  onResetInputs,
  onRunComparison,
  uploadError,
  uploadJobId,
  uploadProgress,
  uploadProgressLabel,
  uploads,
  uploadStatus,
}: CaseInputPanelProps) {
  const hasAnyUpload = Boolean(
    uploads.person.file || uploads.cloth.file || uploads.worn.file,
  );
  const primaryLabel = isRunning
    ? "분석 중..."
    : uploadStatus === "done"
      ? "다시 분석하기"
      : "Fit-aware Try-On 분석하기";

  return (
    <aside className="rounded-2xl border border-[#6EA5FF]/20 bg-[#081426]/80 p-4 shadow-[0_0_30px_rgba(30,80,160,0.12)] backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[#38BDF8]">
            INPUT IMAGES
          </p>
          <h2 className="mt-2 text-lg font-semibold text-[#E5EDF8]">
            Live Upload
          </h2>
        </div>
        <span className="rounded-lg border border-[#5B8CFF]/30 bg-[#5B8CFF]/12 px-2 py-1 text-xs font-medium text-[#9DB8FF]">
          {statusLabel(uploadStatus)}
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {uploadCards.map((card) => (
          <UploadCard
            description={card.description}
            fileName={uploads[card.slot].file?.name}
            key={card.slot}
            onFileChange={onFileChange}
            previewUrl={uploads[card.slot].previewUrl}
            slot={card.slot}
            title={card.title}
          />
        ))}
        <button
          className={[
            "w-full rounded-xl border px-4 py-3 text-sm font-semibold transition",
            canRunComparison && !isRunning
              ? "border-[#74C365]/40 bg-[#74C365]/14 text-[#D7FFD0] hover:bg-[#74C365]/20"
              : "border-[#6EA5FF]/14 bg-[#061426]/70 text-[#6F7E91]",
          ].join(" ")}
          disabled={!canRunComparison || isRunning}
          onClick={onRunComparison}
          type="button"
        >
          {primaryLabel}
        </button>
        <button
          className={[
            "w-full rounded-xl border px-4 py-2.5 text-sm font-semibold transition",
            hasAnyUpload && !isRunning
              ? "border-[#6EA5FF]/24 bg-[#0C1C34]/70 text-[#D8E4FF] hover:bg-[#0C1C34]"
              : "border-[#6EA5FF]/12 bg-[#061426]/45 text-[#5D6A7A]",
          ].join(" ")}
          disabled={!hasAnyUpload || isRunning}
          onClick={onResetInputs}
          type="button"
        >
          입력 초기화
        </button>
        {uploadProgress > 0 ? (
          <div className="rounded-xl border border-[#6EA5FF]/16 bg-[#061426]/70 p-3">
            <div className="mb-2 flex items-center justify-between gap-3 text-xs">
              <span className="text-[#9AA8BA]">
                {uploadProgressLabel ?? "분석 결과를 준비하는 중..."}
              </span>
              <span className="font-semibold text-[#E5EDF8]">
                {uploadProgress}%
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-[#020817]">
              <div
                className="h-full rounded-full bg-[#74C365] transition-all duration-500"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        ) : null}
        {uploadError ? (
          <div className="rounded-xl border border-[#EF4444]/25 bg-[#EF4444]/10 px-3 py-2 text-xs leading-5 text-[#FCA5A5]">
            {uploadError}
          </div>
        ) : null}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 rounded-2xl border border-[#6EA5FF]/16 bg-[#0C1C34]/70 p-3 text-xs">
        <div>
          <p className="text-[#9AA8BA]">Job ID</p>
          <p className="mt-1 truncate font-semibold text-[#E5EDF8]">
            {uploadJobId ? safeText(uploadJobId) : "업로드 전"}
          </p>
        </div>
        <div>
          <p className="text-[#9AA8BA]">Status</p>
          <p className="mt-1 font-semibold text-[#E5EDF8]">
            {statusLabel(uploadStatus)}
          </p>
        </div>
      </div>
    </aside>
  );
}
