import { getMockModelCompare, mockSamples } from "./mockData";
import type { DemoCompareResponse, DemoSample } from "./types";

// API_BASE_URL은 API 요청을 보낼 때 사용할 기본 URL을 정의하는 상수로
// 백엔드 서버의 주소를 환경 변수 NEXT_PUBLIC_API_BASE_URL에서 가져오며, 해당 환경 변수가 설정되지 않은 경우 DEFAULT_API_BASE_URL을 사용하도록 설정
const DEFAULT_API_BASE_URL = "http://localhost:8000";
const FETCH_TIMEOUT_MS = 1500;
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

// apiBaseUrl 함수는 환경 변수 NEXT_PUBLIC_API_BASE_URL에서 API의 기본 URL을 가져오며, 해당 환경 변수가 설정되지 않은 경우 DEFAULT_API_BASE_URL을 반환하는 유틸리티 함수
// 이를 통해 API 요청 시 일관된 기본 URL을 사용할 수 있도록 합니다.
function apiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

async function safeFetchJson<T>(url: string, fallback: T): Promise<T> {
  if (USE_MOCK) {
    return fallback;
  }

  // AbortController: 지정된 시간(FETCH_TIMEOUT_MS) 내에 응답이 오지 않으면 요청을 중단하고 예외를 발생
  // 이를 통해 네트워크 지연이나 서버 문제로 인한 무한 대기 상태를 방지할 수 있습니다.
  const controller = new AbortController();

  // timeout이 따로 있는 이유: fetch 함수 자체에는 타임아웃 기능이 없기 때문에, setTimeout을 사용하여 일정 시간이 지난 후에 AbortController를 통해 요청을 중단하도록 구현
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    // cache: cache 옵션을 "no-store"로 설정하여 브라우저가 응답을 캐시하지 않도록 하고, 항상 최신 데이터를 가져오도록 합니다.
    // signal: 옵션에 AbortController의 신호를 전달하여 지정된 시간 내에 응답이 오지 않으면 요청을 중단하도록 설정
    const response = await fetch(url, {
      cache: "no-store",
      signal: controller.signal,
      // signal: signal은 fetch 요청에 대한 신호를 전달하는 옵션, fetch 함수에서 사용
      // abort: 요청을 중단하는 역할, 특정 상황에서 요청을 중단할 때 호출됩니다.
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
