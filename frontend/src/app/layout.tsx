import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HireWise — Resume Analyzer & Career Coach",
  description:
    "Intelligent resume analyzer and career coach. Identify skill gaps, align with target job descriptions, and enhance your resume.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased selection:bg-teal-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
