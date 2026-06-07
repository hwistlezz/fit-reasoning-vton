import { getMockModelCompare, mockSamples } from "./mockData";
import type {
  DemoCompareResponse,
  DemoSample,
  TryOnJobResponse,
  TryOnUploadFiles,
} from "./types";

const DEFAULT_API_BASE_URL = "http://localhost:8000";
const FETCH_TIMEOUT_MS = 1500;

function shouldUseMockData() {
  return process.env.NEXT_PUBLIC_USE_MOCK !== "false";
}

function apiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

async function safeFetchJson<T>(
  url: string,
  fallback: T,
  init?: RequestInit,
): Promise<T> {
  if (shouldUseMockData()) {
    return fallback;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      cache: "no-store",
      ...init,
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return (await response.json()) as T;
  } catch (error) {
    console.warn("[API fallback to mock]", url, error);
    return fallback;
  } finally {
    clearTimeout(timeout);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isCompareResponse(value: unknown): value is DemoCompareResponse {
  return (
    isRecord(value) &&
    value.page === "model" &&
    isRecord(value.case) &&
    isRecord(value.images) &&
    Array.isArray(value.metrics) &&
    isRecord(value.analysis)
  );
}

function normalizeTryOnResponse(
  payload: unknown,
  fallback: DemoCompareResponse,
): TryOnJobResponse {
  if (isCompareResponse(payload)) {
    return { status: "done", result: payload };
  }

  if (!isRecord(payload)) {
    return { status: "done", result: fallback };
  }

  const status =
    typeof payload.status === "string" ? payload.status : undefined;
  const result = isCompareResponse(payload.result) ? payload.result : undefined;
  const jobId =
    typeof payload.job_id === "string"
      ? payload.job_id
      : typeof payload.jobId === "string"
        ? payload.jobId
        : undefined;
  const error = typeof payload.error === "string" ? payload.error : undefined;

  if (status === "failed") {
    return { job_id: jobId, status: "failed", error, result };
  }

  if (result) {
    return { job_id: jobId, status: "done", result };
  }

  if (
    status === "pending" ||
    status === "running" ||
    status === "uploading" ||
    status === "preprocessing" ||
    status === "stableviton" ||
    status === "enhanced" ||
    status === "done"
  ) {
    return { job_id: jobId, status };
  }

  return { status: "done", result: fallback };
}

export function fetchDemoSamples(): Promise<DemoSample[]> {
  return safeFetchJson(`${apiBaseUrl()}/api/demo/samples`, mockSamples);
}

export function fetchModelCompare(pairId?: string): Promise<DemoCompareResponse> {
  const safePairId = pairId ?? mockSamples[0].pair_id;

  return safeFetchJson(
    `${apiBaseUrl()}/api/demo/model-compare/${encodeURIComponent(safePairId)}`,
    getMockModelCompare(safePairId),
  );
}

export async function startTryOnJob(
  files: TryOnUploadFiles,
  fallback: DemoCompareResponse = getMockModelCompare(),
): Promise<TryOnJobResponse> {
  const formData = new FormData();
  formData.append("person_image", files.person_image);
  formData.append("cloth_image", files.cloth_image);
  formData.append("worn_image", files.worn_image);

  const payload = await safeFetchJson<unknown>(
    `${apiBaseUrl()}/api/tryon/jobs`,
    { status: "done", result: fallback },
    {
      method: "POST",
      body: formData,
    },
  );

  return normalizeTryOnResponse(payload, fallback);
}

export async function getTryOnJob(
  jobId: string,
  fallback: DemoCompareResponse = getMockModelCompare(),
): Promise<TryOnJobResponse> {
  const payload = await safeFetchJson<unknown>(
    `${apiBaseUrl()}/api/tryon/jobs/${encodeURIComponent(jobId)}`,
    { status: "done", result: fallback },
  );

  return normalizeTryOnResponse(payload, fallback);
}
