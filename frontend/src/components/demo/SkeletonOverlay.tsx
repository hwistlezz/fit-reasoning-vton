import type { Keypoint } from "@/lib/types";

type SkeletonOverlayProps = {
  keypoints: Keypoint[];
};

const edges = [
  ["left_shoulder", "right_shoulder"],
  ["left_shoulder", "left_elbow"],
  ["left_elbow", "left_wrist"],
  ["right_shoulder", "right_elbow"],
  ["right_elbow", "right_wrist"],
  ["left_shoulder", "left_hip"],
  ["right_shoulder", "right_hip"],
  ["left_hip", "right_hip"],
];

export default function SkeletonOverlay({ keypoints }: SkeletonOverlayProps) {
  const visiblePoints = keypoints.filter((point) => point.confidence >= 0.5);
  const pointMap = new Map(visiblePoints.map((point) => [point.name, point]));

  return (
    <svg
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 h-full w-full"
      preserveAspectRatio="none"
      viewBox="0 0 100 100"
    >
      {edges.map(([from, to]) => {
        const start = pointMap.get(from);
        const end = pointMap.get(to);

        if (!start || !end) {
          return null;
        }

        return (
          <line
            key={`${from}-${to}`}
            stroke="#38BDF8"
            strokeLinecap="round"
            strokeWidth="1.4"
            vectorEffect="non-scaling-stroke"
            x1={start.x}
            x2={end.x}
            y1={start.y}
            y2={end.y}
          />
        );
      })}
      {visiblePoints.map((point) => (
        <circle
          cx={point.x}
          cy={point.y}
          fill="#74C365"
          key={point.name}
          r="1.9"
          stroke="#E5EDF8"
          strokeWidth="0.6"
          vectorEffect="non-scaling-stroke"
        />
      ))}
    </svg>
  );
}
