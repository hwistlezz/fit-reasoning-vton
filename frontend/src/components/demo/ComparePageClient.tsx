"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import ComparePageTemplate from "./ComparePageTemplate";
import { fetchModelCompare } from "@/lib/api";
import {
  getMockModelCompare,
  localDemoArtifacts,
  mockSamples,
} from "@/lib/mockData";
import type { DemoCompareResponse, UploadSlotKey } from "@/lib/types";

export type UploadInputState = {
  file?: File;
  previewUrl?: string;
};

export type UploadInputs = Record<UploadSlotKey, UploadInputState>;

type UploadUiStatus =
  | "idle"
  | "ready"
  | "uploading"
  | "preprocessing"
  | "stableviton"
  | "enhanced"
  | "done"
  | "failed";

type ComparePageClientProps = {
  localDemo?: boolean;
};

const emptyUploads: UploadInputs = {
  person: {},
  cloth: {},
  worn: {},
};

const progressSteps: {
  label: string;
  progress: number;
  status: UploadUiStatus;
}[] = [
  {
    label: "입력 이미지를 확인하는 중...",
    progress: 0,
    status: "uploading",
  },
  {
    label: "사람 영역과 의류 영역을 정렬하는 중...",
    progress: 25,
    status: "preprocessing",
  },
  {
    label: "StableVITON 기본 결과를 불러오는 중...",
    progress: 45,
    status: "stableviton",
  },
  {
    label: "LoRA-enhanced 결과를 비교하는 중...",
    progress: 70,
    status: "enhanced",
  },
  {
    label: "fit reasoning과 confidence score를 계산하는 중...",
    progress: 90,
    status: "enhanced",
  },
  {
    label: "결과 비교 화면을 준비하는 중...",
    progress: 100,
    status: "done",
  },
];

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function hasAllUploads(uploads: UploadInputs) {
  return Boolean(
    uploads.person.file && uploads.cloth.file && uploads.worn.file,
  );
}

function mergeUploadPreviews(
  data: DemoCompareResponse,
  uploads: UploadInputs,
): DemoCompareResponse {
  return {
    ...data,
    pair_id: "LOCAL-DEMO",
    case: {
      pair_id: "LOCAL-DEMO",
      category: "Upper-body virtual try-on",
      pose_type: "Non-frontal pose with object occlusion",
      difficulty: "High",
      gt_fit_label: "stable oversized fit",
      input_confidence: 0.86,
    },
    images: {
      ...data.images,
      person: uploads.person.previewUrl ?? data.images.person,
      cloth: uploads.cloth.previewUrl ?? data.images.cloth,
      target_worn: uploads.worn.previewUrl ?? data.images.target_worn,
      stableviton: localDemoArtifacts.stableviton,
      enhanced_result: localDemoArtifacts.enhanced_result,
      hotspot: localDemoArtifacts.hotspot,
      skeleton: localDemoArtifacts.skeleton,
      densepose: localDemoArtifacts.densepose,
      skeleton_preview: localDemoArtifacts.skeleton_preview,
      agnostic: localDemoArtifacts.agnostic,
      agnostic_mask: localDemoArtifacts.agnostic_mask,
      upper_body_mask: localDemoArtifacts.upper_body_mask,
      human_parsing_map: localDemoArtifacts.human_parsing_map,
      cloth_mask: localDemoArtifacts.cloth_mask,
      densepose_overlay: localDemoArtifacts.densepose_overlay,
      agnostic_overlay: localDemoArtifacts.agnostic_overlay,
    },
  };
}

function isRunningStatus(status: UploadUiStatus) {
  return (
    status === "uploading" ||
    status === "preprocessing" ||
    status === "stableviton" ||
    status === "enhanced"
  );
}

export default function ComparePageClient({
  localDemo = false,
}: ComparePageClientProps) {
  const searchParams = useSearchParams();
  const selectedPairId = searchParams.get("pairId") ?? mockSamples[0].pair_id;
  const activeKey = `model:${selectedPairId}`;
  const initialData = useMemo(
    () => getMockModelCompare(selectedPairId),
    [selectedPairId],
  );
  const previewUrls = useRef<Set<string>>(new Set());
  const [uploads, setUploads] = useState<UploadInputs>(emptyUploads);
  const [uploadStatus, setUploadStatus] = useState<UploadUiStatus>("idle");
  const [uploadError, setUploadError] = useState<string | undefined>();
  const [uploadJobId, setUploadJobId] = useState<string | undefined>();
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadProgressLabel, setUploadProgressLabel] = useState<string>();
  const [uploadData, setUploadData] = useState<DemoCompareResponse | undefined>();
  const [loaded, setLoaded] = useState<{
    key: string;
    data: DemoCompareResponse;
  }>({
    key: activeKey,
    data: initialData,
  });

  useEffect(() => {
    if (localDemo) {
      return;
    }

    let ignore = false;

    async function loadData() {
      const nextData = await fetchModelCompare(selectedPairId);

      if (!ignore) {
        setLoaded({
          key: activeKey,
          data: nextData,
        });
      }
    }

    void loadData();

    return () => {
      ignore = true;
    };
  }, [activeKey, localDemo, selectedPairId]);

  useEffect(() => {
    const urls = previewUrls.current;

    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
      urls.clear();
    };
  }, []);

  const demoData =
    localDemo || loaded.key !== activeKey ? initialData : loaded.data;
  const canRunComparison = hasAllUploads(uploads);
  const isRunning = isRunningStatus(uploadStatus);
  const displayedUploadStatus =
    !isRunning && !uploadData
      ? canRunComparison
        ? "ready"
        : "idle"
      : uploadStatus;
  const renderedData = uploadData ?? demoData;

  function handleFileChange(slot: UploadSlotKey, file?: File) {
    setUploadError(undefined);
    setUploadJobId(undefined);
    setUploadData(undefined);
    setUploadStatus("idle");
    setUploadProgress(0);
    setUploadProgressLabel(undefined);

    setUploads((current) => {
      const previousUrl = current[slot].previewUrl;

      if (previousUrl) {
        URL.revokeObjectURL(previousUrl);
        previewUrls.current.delete(previousUrl);
      }

      if (!file) {
        return {
          ...current,
          [slot]: {},
        };
      }

      const previewUrl = URL.createObjectURL(file);
      previewUrls.current.add(previewUrl);

      return {
        ...current,
        [slot]: { file, previewUrl },
      };
    });
  }

  function handleResetInputs() {
    previewUrls.current.forEach((url) => URL.revokeObjectURL(url));
    previewUrls.current.clear();
    setUploads(emptyUploads);
    setUploadStatus("idle");
    setUploadError(undefined);
    setUploadJobId(undefined);
    setUploadProgress(0);
    setUploadProgressLabel(undefined);
    setUploadData(undefined);
  }

  async function handleRunComparison() {
    if (!hasAllUploads(uploads) || isRunning) {
      return;
    }

    const currentUploads = uploads;

    setUploadError(undefined);
    setUploadJobId("DEMO-LOCAL-001");
    setUploadData(undefined);

    for (const step of progressSteps) {
      setUploadStatus(step.status);
      setUploadProgress(step.progress);
      setUploadProgressLabel(step.label);
      await delay(step.progress === 0 ? 350 : 470);
    }

    setUploadData(mergeUploadPreviews(demoData, currentUploads));
    setUploadStatus("done");
    setUploadProgress(100);
    setUploadProgressLabel("결과 비교 화면이 준비되었습니다.");
  }

  return (
    <ComparePageTemplate
      canRunComparison={canRunComparison}
      data={renderedData}
      isRunning={isRunning}
      onFileChange={handleFileChange}
      onResetInputs={handleResetInputs}
      onRunComparison={handleRunComparison}
      uploadError={uploadError}
      uploadJobId={uploadJobId}
      uploadProgress={uploadProgress}
      uploadProgressLabel={uploadProgressLabel}
      uploads={uploads}
      uploadStatus={displayedUploadStatus}
    />
  );
}
