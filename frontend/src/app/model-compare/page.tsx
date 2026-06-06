// Suspense 뜻: React의 Suspense는 컴포넌트가 비동기적으로 데이터를 로드하거나 다른 작업을 수행할 때, 로딩 상태를 관리하는 데 사용되는 기능입니다
import { Suspense } from "react";
import ComparePageClient from "@/components/demo/ComparePageClient";

export default function ModelComparePage() {
  return (
    <Suspense fallback={<PageFallback />}>
      <ComparePageClient />
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
