import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Resume Screening Agent",
  description: "AI recruiting assistant for resume screening",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="mx-auto min-h-screen max-w-6xl px-6 py-8">
          <header className="mb-8 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-500">AI Recruiting Assistant</p>
              <h1 className="text-3xl font-semibold">Resume Screening Agent</h1>
            </div>
            <nav className="flex gap-4 text-sm">
              <Link href="/">Home</Link>
              <Link href="/positions">Positions</Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
