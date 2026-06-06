import type { ReactNode } from "react";
import Navbar from "./Navbar";

// PageShell 컴포넌트는 애플리케이션의 기본 레이아웃을 정의하는 컴포넌트로, 전체 페이지에 공통적으로 적용되는 스타일과 구조를 제공하며, Navbar와 main 콘텐츠 영역을 포함합 
// children prop을 통해 각 페이지의 고유한 콘텐츠를 main 영역에 렌더링할 수 있도록 설계
export default function PageShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#020817] via-[#061426] to-[#01040A] text-[#E5EDF8]">
      <div className="pointer-events-none fixed inset-0 bg-[linear-gradient(120deg,rgba(56,189,248,0.08),transparent_38%,rgba(91,140,255,0.08)_72%,transparent)]" />
      <Navbar />
      <main className="relative z-10 mx-auto flex w-full max-w-[1480px] flex-1 flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}
