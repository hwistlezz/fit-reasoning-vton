export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-[#6EA5FF]/20 bg-[#020817]/85 backdrop-blur-xl">
      <div className="mx-auto flex min-h-14 w-full max-w-[1480px] items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <div>
          <p className="text-base font-semibold leading-5 text-[#E5EDF8]">
            FitVTON
          </p>
          <p className="mt-1 text-xs font-medium uppercase tracking-[0.18em] text-[#9AA8BA]">
            CV Capstone Project
          </p>
        </div>
        <div className="rounded-lg border border-[#6EA5FF]/20 bg-[#081426]/70 px-3 py-1.5 text-xs font-medium text-[#BFD0FF]">
          StableVITON Comparison Demo
        </div>
      </div>
    </header>
  );
}
