import Link from "next/link";

export function Footer() {
  return (
    <footer className="bg-slate-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between">
          <div>
            <p className="text-sm text-slate-400">© 2026 LegalMY. All rights reserved.</p>
          </div>
          <div className="flex items-center gap-6 mt-4 md:mt-0">
            <Link href="/privacy" className="text-sm text-slate-400 hover:text-white transition">
              Privacy
            </Link>
            <Link href="/terms" className="text-sm text-slate-400 hover:text-white transition">
              Terms
            </Link>
            <Link href="/pdpa" className="text-sm text-slate-400 hover:text-white transition">
              PDPA
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
