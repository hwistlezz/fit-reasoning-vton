"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import ComparePageTemplate from "./ComparePageTemplate";
import { fetchModelCompare, getTryOnJob, startTryOnJob } from "@/lib/api";
import { getMockModelCompare, mockSamples } from "@/lib/mockData";
import type {
  DemoCompareResponse,
  TryOnJobResponse,
  TryOnJobStatus,
  UploadSlotKey,
} from "@/lib/types";

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

const emptyUploads: UploadInputs = {
  person: {},
  cloth: {},
  worn: {},
};

function statusFromJob(status: TryOnJobStatus): UploadUiStatus {
  if (status === "pending" || status === "running") {
    return "preprocessing";
  }

  return status;
}

function mergeUploadPreviews(
  data: DemoCompareResponse,
  uploads: UploadInputs,
): DemoCompareResponse {
  return {
    ...data,
    pair_id: data.pair_id || "UPLOAD-LOCAL",
    case: {
      pair_id: data.case?.pair_id || "UPLOAD-LOCAL",
      category: data.case?.category || "Uploaded try-on",
      pose_type: data.case?.pose_type || "Analysis pending",
      difficulty: data.case?.difficulty || "Medium",
      gt_fit_label: data.case?.gt_fit_label || "Analysis pending",
      input_confidence: data.case?.input_confidence ?? 1,
    },
    images: {
      ...data.images,
      person: uploads.person.previewUrl ?? data.images.person,
      cloth: uploads.cloth.previewUrl ?? data.images.cloth,
      target_worn: uploads.worn.previewUrl ?? data.images.target_worn,
    },
  };
}

async function resolveTryOnResult(
  response: TryOnJobResponse,
  fallback: DemoCompareResponse,
): Promise<TryOnJobResponse> {
  if (response.result || !response.job_id || response.status === "failed") {
    return response;
  }

  let latest = response;

  for (let attempt = 0; attempt < 4; attempt += 1) {
    latest = await getTryOnJob(response.job_id, fallback);

    if (latest.result || latest.status === "failed") {
      return latest;
    }

    await new Promise((resolve) => setTimeout(resolve, 700));
  }

  return { status: "done", result: fallback };
}

export default function ComparePageClient() {
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
  const [uploadData, setUploadData] = useState<DemoCompareResponse | undefined>();
  const [loaded, setLoaded] = useState<{
    key: string;
    data: DemoCompareResponse;
  }>({
    key: activeKey,
    data: initialData,
  });

  useEffect(() => {
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
  }, [activeKey, selectedPairId]);

  useEffect(() => {
    const urls = previewUrls.current;

    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
      urls.clear();
    };
  }, []);

  const demoData = loaded.key === activeKey ? loaded.data : initialData;
  const canRunComparison = Boolean(
    uploads.person.file && uploads.cloth.file && uploads.worn.file,
  );
  const isRunning =
    uploadStatus === "uploading" ||
    uploadStatus === "preprocessing" ||
    uploadStatus === "stableviton" ||
    uploadStatus === "enhanced";
  const renderedData = uploadData ?? demoData;

  function handleFileChange(slot: UploadSlotKey, file?: File) {
    setUploadError(undefined);
    setUploadJobId(undefined);
    setUploadData(undefined);

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

    setUploadStatus(file ? "ready" : "idle");
  }

  async function handleRunComparison() {
    if (
      !uploads.person.file ||
      !uploads.cloth.file ||
      !uploads.worn.file ||
      isRunning
    ) {
      return;
    }

    const fallback = mergeUploadPreviews(demoData, uploads);

    setUploadError(undefined);
    setUploadJobId(undefined);
    setUploadStatus("uploading");

    try {
      const started = await startTryOnJob(
        {
          person_image: uploads.person.file,
          cloth_image: uploads.cloth.file,
          worn_image: uploads.worn.file,
        },
        fallback,
      );

      const resolvedJobId = started.job_id ?? "UPLOAD-LOCAL";

      setUploadJobId(resolvedJobId);
      setUploadStatus(statusFromJob(started.status));

      const finished = await resolveTryOnResult(started, fallback);
      setUploadJobId(finished.job_id ?? resolvedJobId);

      if (finished.status === "failed") {
        setUploadError(finished.error ?? "Upload result generation failed.");
        setUploadStatus("failed");
        setUploadData(fallback);
        return;
      }

      setUploadStatus("enhanced");

      const result = mergeUploadPreviews(finished.result ?? fallback, uploads);
      setUploadData(result);
      setUploadStatus("done");
    } catch (error) {
      console.warn("[Try-on upload fallback]", error);
      setUploadError("API response failed. Showing mock fallback result.");
      setUploadData(fallback);
      setUploadStatus("failed");
    }
  }

  return (
    <ComparePageTemplate
      canRunComparison={canRunComparison}
      data={renderedData}
      isRunning={isRunning}
      onFileChange={handleFileChange}
      onRunComparison={handleRunComparison}
      uploadError={uploadError}
      uploadJobId={uploadJobId}
      uploads={uploads}
      uploadStatus={uploadStatus}
    />
  );
}
