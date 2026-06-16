"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export function Navbar() {
  return (
    <nav className="border-b border-slate-200 bg-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">L</span>
            </div>
            <span className="font-bold text-lg text-primary">LegalMY</span>
          </Link>

          {/* Links */}
          <div className="hidden md:flex items-center gap-8">
            <Link href="/search" className="text-slate-700 hover:text-primary transition">
              Search
            </Link>
            <Link href="/judges" className="text-slate-700 hover:text-primary transition">
              Judges
            </Link>
            <Link href="/dashboard" className="text-slate-700 hover:text-primary transition">
              Dashboard
            </Link>
          </div>

          {/* Auth Buttons */}
          <div className="flex items-center gap-3">
            <Button variant="ghost" className="text-slate-700">
              Login
            </Button>
            <Button className="bg-primary hover:bg-primary-dark">
              Register
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}
