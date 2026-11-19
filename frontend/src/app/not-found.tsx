import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#FAF8F7] flex flex-col items-center justify-center p-6 text-center">
      <h2 className="text-xl font-bold text-[#7C0E44]">Page Not Found</h2>
      <p className="text-xs text-slate-500 mt-2 mb-4">
        The requested page or resource could not be found.
      </p>
      <Link
        href="/"
        className="text-xs font-semibold px-4 py-2 rounded-lg bg-[#7C0E44] hover:bg-[#600B35] text-white transition-colors"
      >
        Return to Dashboard
      </Link>
    </div>
  );
}

