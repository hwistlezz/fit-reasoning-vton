export type ComparePageType = "model";

export type MetricDirection = "higher_is_better" | "lower_is_better";
export type UploadSlotKey = "person" | "cloth" | "worn";
export type TryOnJobStatus =
  | "pending"
  | "running"
  | "uploading"
  | "preprocessing"
  | "stableviton"
  | "enhanced"
  | "done"
  | "failed";

export type DemoCase = {
  pair_id: string;
  category: string;
  pose_type: string;
  difficulty: "Low" | "Medium" | "High";
  gt_fit_label: string;
  input_confidence: number;
};

export type DemoSample = DemoCase;

export type DemoImageSet = {
  person: string;
  cloth: string;
  target_worn: string;
  stableviton: string;
  enhanced_result: string;
  hotspot?: string;
  skeleton?: string;
  agnostic?: string;
  agnostic_mask?: string;
  upper_body_mask?: string;
  densepose?: string;
  skeleton_preview?: string;
  human_parsing_map?: string;
  cloth_mask?: string;
  densepose_overlay?: string;
  agnostic_overlay?: string;
};

export type DemoMetric = {
  key: string;
  title: string;
  description: string;
  baseline_label: string;
  method_label: string;
  baseline_value: number;
  method_value: number;
  direction: MetricDirection;
  improvement_text: string;
  unit?: string;
};

export type Hotspot = {
  key: string;
  label: string;
  text: string;
  x: number;
  y: number;
  value?: string;
};

export type Keypoint = {
  name: string;
  x: number;
  y: number;
  confidence: number;
};

export type DemoFitDetails = {
  fit_label: string;
  confidence: number;
  shoulder_ratio: number;
  torso_width_ratio: number;
  sleeve_length_ratio: number;
  garment_length_ratio: number;
  pose_quality: number;
  parsing_quality: number;
  body_visibility: number;
};

export type DemoReliability = {
  result_reliability: number;
  pose_reliability: number;
  boundary_stability: number;
  occlusion_risk: number;
  artifact_risk: number;
};

export type DemoAnalysis = {
  fit: DemoFitDetails;
  pose: {
    label: string;
    summary: string;
  };
  hotspots: Hotspot[];
  keypoints: Keypoint[];
  reliability: DemoReliability;
  densepose_note: string;
  agnostic_note: string;
};

export type DemoCompareResponse = {
  page: ComparePageType;
  pair_id: string;
  case: DemoCase;
  images: DemoImageSet;
  metrics: DemoMetric[];
  analysis: DemoAnalysis;
};

export type TryOnUploadFiles = {
  person_image: File;
  cloth_image: File;
  worn_image: File;
};

export type TryOnJobResponse = {
  job_id?: string;
  status: TryOnJobStatus;
  result?: DemoCompareResponse;
  error?: string;
};
