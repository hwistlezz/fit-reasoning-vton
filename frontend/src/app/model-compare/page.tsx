import { Suspense } from "react";
import ComparePageClient from "@/components/demo/ComparePageClient";

export default function ModelComparePage() {
  return (
    <Suspense fallback={<PageFallback />}>
      <ComparePageClient localDemo />
    </Suspense>
  );
}

function PageFallback() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#020817] via-[#061426] to-[#01040A] p-6 text-[#E5EDF8]">
      Loading Model Compare...
    </div>
  );
}
