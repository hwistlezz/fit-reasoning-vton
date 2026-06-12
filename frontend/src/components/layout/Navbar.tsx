import Link from "next/link";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-[#6EA5FF]/20 bg-[#020817]/85 backdrop-blur-xl">
      <div className="mx-auto flex min-h-14 w-full max-w-[1480px] items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <Link
          className="text-base font-semibold leading-5 text-[#E5EDF8]"
          href="/demo-vton"
        >
          FitVITON
        </Link>
        <nav aria-label="Primary navigation">
          <Link
            className="rounded-full border border-[#5B8CFF]/45 bg-[#5B8CFF]/14 px-3 py-1.5 mx-1 text-xs font-medium text-[#D8E4FF]"
            href="/demo-vton"
          >
            Stable VITON
          </Link>
          <Link
            className="rounded-full border border-[#5B8CFF]/45 bg-[#5B8CFF]/14 px-3 py-1.5 mx-1 text-xs font-medium text-[#D8E4FF]"
            href="/demo-vton"
          >
            IDM VITON
          </Link>
          <Link
            className="rounded-full border border-[#5B8CFF]/45 bg-[#5B8CFF]/14 px-3 py-1.5 mx-1 text-xs font-medium text-[#D8E4FF]"
            href="/demo-vton"
          >
            CAT VITON
          </Link>
        </nav>
      </div>
    </header>
  );
}
