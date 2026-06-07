import type {
  DemoAnalysis,
  DemoCase,
  DemoCompareResponse,
  DemoImageSet,
  DemoMetric,
  DemoSample,
} from "./types";

const demoCases: DemoCase[] = [
  {
    pair_id: "EP00001234",
    category: "Upper-body knit",
    pose_type: "Cross-arm standing",
    difficulty: "Medium",
    gt_fit_label: "Good fit",
    input_confidence: 0.91,
  },
  {
    pair_id: "EP00004567",
    category: "Long sleeve shirt",
    pose_type: "Side-lean pose",
    difficulty: "High",
    gt_fit_label: "Slightly loose",
    input_confidence: 0.86,
  },
  {
    pair_id: "EP00007890",
    category: "Casual jacket",
    pose_type: "Front pose with occlusion",
    difficulty: "Medium",
    gt_fit_label: "Regular fit",
    input_confidence: 0.89,
  },
];

export const mockSamples: DemoSample[] = demoCases;

function imageSet(pairId: string): DemoImageSet {
  return {
    person: `/demo-assets/image/${pairId}.jpg`,
    cloth: `/demo-assets/cloth/${pairId}.jpg`,
    target_worn: `/demo-assets/worn/${pairId}.jpg`,
    stableviton: `/demo-assets/stableviton/${pairId}.png`,
    enhanced_result: `/demo-assets/enhanced_result/${pairId}.png`,
    agnostic: `/demo-assets/agnostic-v3.2/${pairId}.jpg`,
    agnostic_mask: `/demo-assets/agnostic-mask/${pairId}.png`,
    densepose: `/demo-assets/image-densepose/${pairId}.png`,
    skeleton_preview: `/demo-assets/skeleton-preview/${pairId}.png`,
  };
}

const keypoints = [
  { name: "left_shoulder", x: 38, y: 27, confidence: 0.93 },
  { name: "right_shoulder", x: 61, y: 28, confidence: 0.92 },
  { name: "left_elbow", x: 33, y: 45, confidence: 0.84 },
  { name: "right_elbow", x: 67, y: 46, confidence: 0.88 },
  { name: "left_wrist", x: 30, y: 63, confidence: 0.78 },
  { name: "right_wrist", x: 71, y: 62, confidence: 0.8 },
  { name: "left_hip", x: 43, y: 68, confidence: 0.91 },
  { name: "right_hip", x: 58, y: 69, confidence: 0.9 },
];

function analysisFor(index: number): DemoAnalysis {
  const adjustment = index * 0.02;

  return {
    fit: {
      fit_label: demoCases[index].gt_fit_label,
      confidence: 0.9 - adjustment,
      shoulder_ratio: 0.97 - adjustment,
      torso_width_ratio: 1.02 + adjustment,
      sleeve_length_ratio: 0.94 + adjustment,
      garment_length_ratio: 0.98 - adjustment,
      pose_quality: 0.92 - adjustment,
      parsing_quality: 0.89 - adjustment,
      body_visibility: 0.87 - adjustment,
    },
    pose: {
      label: demoCases[index].pose_type,
      summary:
        "OpenPose keypoint와 DensePose 영역을 함께 사용해 자세 정렬, 신체 가시성, 의류 배치 안정성을 분석합니다.",
    },
    hotspots: [
      {
        key: "shoulder",
        label: "Shoulder",
        text: "어깨선과 상의 경계가 사람의 자세에 맞게 안정적으로 정렬되는지 확인합니다.",
        x: 39,
        y: 28,
        value: "0.93",
      },
      {
        key: "torso",
        label: "Torso",
        text: "몸통 영역에서 의류 텍스처와 형태가 자연스럽게 유지되는지 확인합니다.",
        x: 51,
        y: 49,
        value: "0.94",
      },
      {
        key: "sleeve",
        label: "Sleeve",
        text: "팔꿈치와 손목 주변에서 소매 위치가 자세 변화나 가림에도 안정적인지 확인합니다.",
        x: 69,
        y: 58,
        value: "0.91",
      },
      {
        key: "length",
        label: "Length",
        text: "의류 하단 경계가 실제 착용 기준 이미지와 얼마나 일관되게 맞는지 비교합니다.",
        x: 53,
        y: 73,
        value: "0.89",
      },
    ],
    keypoints,
    reliability: {
      result_reliability: 0.88 - adjustment,
      pose_reliability: 0.91 - adjustment,
      boundary_stability: 0.9 - adjustment,
      occlusion_risk: 0.22 + adjustment,
      artifact_risk: 0.18 + adjustment,
    },
    densepose_note:
      "DensePose는 신체 표면 구조를 제공해 생성된 의류가 보이는 자세를 더 일관되게 따르도록 돕습니다.",
    agnostic_note:
      "Agnostic mask는 기존 의류 영역을 제거하고 새 의류가 합성될 위치를 명확하게 지정합니다.",
  };
}

const modelMetrics: DemoMetric[] = [
  {
    key: "pose_robustness",
    title: "Pose Robustness",
    description: "포즈 안정성",
    baseline_label: "StableVITON",
    method_label: "Enhanced",
    baseline_value: 0.782,
    method_value: 0.921,
    direction: "higher_is_better",
    improvement_text: "17.8% 개선",
  },
  {
    key: "occlusion_handling",
    title: "Occlusion Handling",
    description: "가림 영역 처리",
    baseline_label: "StableVITON",
    method_label: "Enhanced",
    baseline_value: 0.641,
    method_value: 0.856,
    direction: "higher_is_better",
    improvement_text: "21.5% 개선",
  },
  {
    key: "garment_preservation",
    title: "Garment Preservation",
    description: "의류 디테일 보존",
    baseline_label: "StableVITON",
    method_label: "Enhanced",
    baseline_value: 0.128,
    method_value: 0.064,
    direction: "lower_is_better",
    improvement_text: "50.0% 감소",
  },
  {
    key: "boundary_quality",
    title: "Boundary Quality",
    description: "경계선 품질",
    baseline_label: "StableVITON",
    method_label: "Enhanced",
    baseline_value: 0.712,
    method_value: 0.904,
    direction: "higher_is_better",
    improvement_text: "19.2% 개선",
  },
  {
    key: "failure_case_reduction",
    title: "Failure Case Reduction",
    description: "실패 케이스 감소",
    baseline_label: "StableVITON",
    method_label: "Enhanced",
    baseline_value: 23.4,
    method_value: 8.7,
    direction: "lower_is_better",
    improvement_text: "62.8% 감소",
    unit: "%",
  },
];

function findCase(pairId?: string): { sample: DemoCase; index: number } {
  const index = demoCases.findIndex((sample) => sample.pair_id === pairId);

  if (index >= 0) {
    return { sample: demoCases[index], index };
  }

  return { sample: demoCases[0], index: 0 };
}

export function getMockModelCompare(pairId?: string): DemoCompareResponse {
  const { sample, index } = findCase(pairId);

  return {
    page: "model",
    pair_id: sample.pair_id,
    case: sample,
    images: imageSet(sample.pair_id),
    metrics: modelMetrics,
    analysis: analysisFor(index),
  };
}
