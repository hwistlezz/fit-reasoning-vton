import type { ReactNode } from "react";
import Navbar from "./Navbar";

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
