import type {
  DemoAnalysis,
  DemoCase,
  DemoCompareResponse,
  DemoImageSet,
  DemoMetric,
  DemoSample,
} from "./types";

export const localDemoArtifacts = {
  stableviton: "/local-demo-vton/demo_stableviton.png",
  enhanced_result: "/local-demo-vton/demo_lora.png",
  hotspot: "/local-demo-vton/analysis/hotspot.png",
  skeleton: "/local-demo-vton/analysis/skeleton.png",
  densepose: "/local-demo-vton/analysis/densepose.png",
  skeleton_preview: "/local-demo-vton/analysis/skeleton-preview.png",
  agnostic: "/local-demo-vton/analysis/agnostic.png",
  upper_body_mask: "/local-demo-vton/analysis/upper-body-mask.png",
  agnostic_mask: "/local-demo-vton/analysis/upper-body-mask.png",
  human_parsing_map: "/local-demo-vton/analysis/human-parsing-map.png",
  cloth_mask: "/local-demo-vton/analysis/cloth-mask.png",
  densepose_overlay: "/local-demo-vton/analysis/densepose-overlay.png",
  agnostic_overlay: "/local-demo-vton/analysis/agnostic-overlay.png",
} as const satisfies Partial<DemoImageSet>;

const demoCases: DemoCase[] = [
  {
    pair_id: "LOCAL-DEMO",
    category: "Upper-body oversized tee",
    pose_type: "Non-frontal pose with object occlusion",
    difficulty: "High",
    gt_fit_label: "stable oversized fit",
    input_confidence: 0.86,
  },
  {
    pair_id: "EP00004567",
    category: "Long sleeve shirt",
    pose_type: "Side-lean pose",
    difficulty: "High",
    gt_fit_label: "slightly loose",
    input_confidence: 0.84,
  },
  {
    pair_id: "EP00007890",
    category: "Casual jacket",
    pose_type: "Front pose with occlusion",
    difficulty: "Medium",
    gt_fit_label: "regular fit",
    input_confidence: 0.89,
  },
];

export const mockSamples: DemoSample[] = demoCases;

function imageSet(pairId: string): DemoImageSet {
  const baseImages: DemoImageSet = {
    person: `/demo-assets/image/${pairId}.jpg`,
    cloth: `/demo-assets/cloth/${pairId}.jpg`,
    target_worn: `/demo-assets/worn/${pairId}.jpg`,
    stableviton: `/demo-assets/stableviton/${pairId}.png`,
    enhanced_result: `/demo-assets/enhanced_result/${pairId}.png`,
  };

  if (pairId !== "LOCAL-DEMO") {
    return baseImages;
  }

  return {
    ...baseImages,
    ...localDemoArtifacts,
  };
}

const keypoints = [
  { name: "left_shoulder", x: 36, y: 24, confidence: 0.93 },
  { name: "right_shoulder", x: 61, y: 24, confidence: 0.92 },
  { name: "left_elbow", x: 27, y: 33, confidence: 0.84 },
  { name: "right_elbow", x: 70, y: 33, confidence: 0.86 },
  { name: "left_wrist", x: 24, y: 48, confidence: 0.76 },
  { name: "right_wrist", x: 74, y: 48, confidence: 0.78 },
  { name: "left_hip", x: 38, y: 59, confidence: 0.89 },
  { name: "right_hip", x: 60, y: 59, confidence: 0.88 },
];

function analysisFor(index: number): DemoAnalysis {
  const adjustment = index * 0.02;

  return {
    fit: {
      fit_label: "stable oversized fit",
      confidence: 0.86 - adjustment,
      shoulder_ratio: 0.98 - adjustment,
      torso_width_ratio: 1.04 + adjustment,
      sleeve_length_ratio: 0.96 + adjustment,
      garment_length_ratio: 0.99 - adjustment,
      pose_quality: 0.84 - adjustment,
      parsing_quality: 0.88 - adjustment,
      body_visibility: 0.81 - adjustment,
    },
    pose: {
      label: demoCases[index]?.pose_type ?? demoCases[0].pose_type,
      summary:
        "비정면 포즈와 양손 오브젝트 가림 조건에서도 상체 회전, 어깨선, 그래픽 중심 정렬이 안정적으로 유지되는지 확인합니다.",
    },
    hotspots: [
      {
        key: "shoulder",
        label: "어깨선 정렬",
        text: "어깨선과 소매 시작 위치가 신체 구조에 맞게 정렬되는 정도입니다.",
        x: 36,
        y: 24,
        value: "88",
      },
      {
        key: "graphic",
        label: "그래픽 보존",
        text: "전면 그래픽의 선명도, 크기, 중심 위치가 유지되는 정도입니다.",
        x: 50,
        y: 38,
        value: "87",
      },
      {
        key: "sleeve",
        label: "소매 경계",
        text: "팔과 소매 사이의 경계가 자연스럽게 분리되는 정도입니다.",
        x: 70,
        y: 33,
        value: "84",
      },
      {
        key: "hem",
        label: "밑단 안정성",
        text: "상의 밑단과 하의 경계가 무너지지 않고 안정적으로 유지되는 정도입니다.",
        x: 50,
        y: 59,
        value: "85",
      },
    ],
    keypoints,
    reliability: {
      result_reliability: 0.86 - adjustment,
      pose_reliability: 0.78 - adjustment,
      boundary_stability: 0.84 - adjustment,
      occlusion_risk: 0.24 + adjustment,
      artifact_risk: 0.18 + adjustment,
    },
    densepose_note:
      "DensePose 조건은 신체 표면 구조를 제공해 비정면 자세와 손 오브젝트 가림 상황에서도 의류 경계와 그래픽 위치를 안정적으로 정렬하도록 돕습니다.",
    agnostic_note:
      "Agnostic mask는 기존 의류 영역을 제거하고 새 의류가 합성될 위치를 명확하게 지정합니다. 이를 통해 상의 경계, 밑단, 소매 영역을 안정적으로 비교할 수 있습니다.",
  };
}

const modelMetrics: DemoMetric[] = [
  {
    key: "shoulder_alignment",
    title: "Shoulder Alignment",
    description: "어깨선과 소매 시작 위치 정렬",
    baseline_label: "StableVITON",
    method_label: "StableVITON + LoRA",
    baseline_value: 74,
    method_value: 88,
    direction: "higher_is_better",
    improvement_text: "+14",
    unit: "score",
  },
  {
    key: "graphic_preservation",
    title: "Graphic Preservation",
    description: "전면 그래픽 선명도와 중심 위치",
    baseline_label: "StableVITON",
    method_label: "StableVITON + LoRA",
    baseline_value: 69,
    method_value: 87,
    direction: "higher_is_better",
    improvement_text: "+18",
    unit: "score",
  },
  {
    key: "sleeve_boundary",
    title: "Sleeve Boundary",
    description: "팔과 소매 경계 분리",
    baseline_label: "StableVITON",
    method_label: "StableVITON + LoRA",
    baseline_value: 68,
    method_value: 84,
    direction: "higher_is_better",
    improvement_text: "+16",
    unit: "score",
  },
  {
    key: "hem_stability",
    title: "Hem Stability",
    description: "상의 밑단과 하의 경계 안정성",
    baseline_label: "StableVITON",
    method_label: "StableVITON + LoRA",
    baseline_value: 71,
    method_value: 85,
    direction: "higher_is_better",
    improvement_text: "+14",
    unit: "score",
  },
  {
    key: "color_consistency",
    title: "Color Consistency",
    description: "입력 의류 색감 유지",
    baseline_label: "StableVITON",
    method_label: "StableVITON + LoRA",
    baseline_value: 76,
    method_value: 88,
    direction: "higher_is_better",
    improvement_text: "+12",
    unit: "score",
  },
  {
    key: "pose_robustness",
    title: "Pose Robustness",
    description: "비정면 자세와 가림 조건 대응",
    baseline_label: "StableVITON",
    method_label: "StableVITON + LoRA",
    baseline_value: 70,
    method_value: 84,
    direction: "higher_is_better",
    improvement_text: "+14",
    unit: "score",
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
