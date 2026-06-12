import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FitVTON Demo Dashboard",
  description: "Presentation dashboard for artifact and model comparison.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-[#020817] text-[#E5EDF8]">
        {children}
      </body>
    </html>
  );
}
