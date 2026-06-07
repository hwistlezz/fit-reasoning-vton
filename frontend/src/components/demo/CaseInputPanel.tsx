import ImageWithFallback from "./ImageWithFallback";
import type { UploadInputs } from "./ComparePageClient";
import type { UploadSlotKey } from "@/lib/types";

type CaseInputPanelProps = {
  canRunComparison: boolean;
  isRunning: boolean;
  onFileChange: (slot: UploadSlotKey, file?: File) => void;
  onRunComparison: () => void;
  uploadError?: string;
  uploadJobId?: string;
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
    title: "Person Image",
    description: "\ud30c\uc77c\uc744 \uc120\ud0dd\ud558\uac70\ub098 \ub4dc\ub798\uadf8\ud574 \uc8fc\uc138\uc694",
  },
  {
    slot: "cloth",
    title: "Cloth Image",
    description: "\uc758\ub958 \uc774\ubbf8\uc9c0\ub97c \uc120\ud0dd\ud574 \uc8fc\uc138\uc694",
  },
  {
    slot: "worn",
    title: "Worn Image",
    description: "\uc2e4\uc81c \ucc29\uc6a9 \ucc38\uace0 \uc774\ubbf8\uc9c0\ub97c \uc120\ud0dd\ud574 \uc8fc\uc138\uc694",
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
    ready: "실행 준비",
    uploading: "업로드 중",
    preprocessing: "전처리 중",
    stableviton: "StableVITON 추론",
    enhanced: "개선 결과 생성",
    done: "완료",
    failed: "Fallback",
  };

  return labels[status] ?? status;
}

function UploadCard({
  description,
  onFileChange,
  previewUrl,
  slot,
  title,
}: {
  description: string;
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
          imageClassName="object-cover object-top"
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
          <p className="text-xs leading-5 text-[#9AA8BA]">Preview ready</p>
        </div>
      ) : null}
    </label>
  );
}

export default function CaseInputPanel({
  canRunComparison,
  isRunning,
  onFileChange,
  onRunComparison,
  uploadError,
  uploadJobId,
  uploads,
  uploadStatus,
}: CaseInputPanelProps) {
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
          {isRunning ? "Running Comparison..." : "Run Comparison"}
        </button>
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
