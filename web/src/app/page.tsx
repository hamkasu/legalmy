import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Search, Users, Zap, Bell, FileText, Code } from "lucide-react";

const features = [
  {
    icon: Search,
    title: "Smart Search",
    description: "Full-text search across 2.4M+ Malaysian court cases with advanced filtering",
  },
  {
    icon: Users,
    title: "Judge Analytics",
    description: "Comprehensive judge profiles with success rates and case history",
  },
  {
    icon: Zap,
    title: "AI Summariser",
    description: "Instant judgment summaries with key findings and ratio decidendi",
  },
  {
    icon: Bell,
    title: "Real-time Alerts",
    description: "Get notified about cases matching your practice areas and interests",
  },
  {
    icon: FileText,
    title: "Bilingual Drafting",
    description: "AI-powered legal document drafting in English and Bahasa Malaysia",
  },
  {
    icon: Code,
    title: "API Access",
    description: "Integrate Malaysian legal data into your own applications",
  },
];

const courts = [
  "Federal Court",
  "Court of Appeal",
  "High Court (Malaya)",
  "High Court (Sabah & Sarawak)",
  "Sessions Court",
  "Magistrates Court",
  "Shariah Court",
  "Special Courts",
  "Tribunal",
];

export default function Home() {
  return (
    <div className="w-full">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-light to-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-slate-900 mb-6">
            Malaysia's Court Intelligence Platform
          </h1>
          <p className="text-xl text-slate-600 mb-8 max-w-3xl mx-auto">
            Access millions of court cases, analyze judge profiles, and leverage AI-powered legal insights to win your cases.
          </p>
          <div className="flex gap-4 justify-center">
            <Button className="bg-primary hover:bg-primary-dark text-white px-8 py-6 text-lg">
              Get Started Free
            </Button>
            <Button variant="outline" className="border-primary text-primary hover:bg-primary-light px-8 py-6 text-lg">
              Book Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-slate-100 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="text-center">
              <p className="text-3xl font-bold text-primary">2.4M+</p>
              <p className="text-slate-600">Court Records</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-primary">1,200+</p>
              <p className="text-slate-600">Judges</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-primary">30+</p>
              <p className="text-slate-600">Years of Data</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-primary">95K</p>
              <p className="text-slate-600">Searches/Month</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center mb-12">Powerful Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <div key={idx} className="border border-slate-200 rounded-lg p-6 hover:shadow-lg transition">
                  <Icon className="w-12 h-12 text-primary mb-4" />
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-slate-600">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Coverage Section */}
      <section className="bg-slate-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center mb-12">Court Coverage</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {courts.map((court, idx) => (
              <div key={idx} className="bg-white border border-slate-200 rounded-lg p-4 text-center">
                <p className="text-slate-700 font-medium">{court}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold mb-4">Start your free trial</h2>
          <p className="text-lg mb-8 opacity-90">No credit card required. Get instant access to Malaysia's largest court database.</p>
          <Button className="bg-white text-primary hover:bg-slate-100 px-8 py-6 text-lg font-semibold">
            Sign Up Now
          </Button>
        </div>
      </section>
    </div>
  );
}
