"use client";

import { useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { searchCases, type CaseSearchResult } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

const PRACTICE_AREAS = ["criminal", "civil", "commercial", "family", "land", "employment", "syariah", "other"];
const OUTCOMES = ["plaintiff_wins", "defendant_wins", "settled", "dismissed", "allowed", "unknown"];
const LANGUAGES = ["en", "bm", "ta"];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({
    court_type: "",
    state: "",
    year_from: undefined as number | undefined,
    year_to: undefined as number | undefined,
    practice_area: "",
    outcome: "",
    language: "",
  });
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const { data: results = [], isLoading } = useSWR(
    ["/cases/search", { q: query, ...filters, offset, limit }],
    ([, params]) => searchCases(params),
    { keepPreviousData: true }
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
  };

  const handleFilterChange = (key: string, value: string | number | undefined) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
    setOffset(0);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Search Bar */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search cases by title, parties, case number..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <Button type="submit" className="bg-primary hover:bg-primary-dark">
            Search
          </Button>
        </div>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Sidebar Filters */}
        <div className="space-y-4">
          <h3 className="font-semibold text-slate-900">Filters</h3>

          <div>
            <label className="text-sm font-medium text-slate-600">Practice Area</label>
            <select
              value={filters.practice_area}
              onChange={(e) => handleFilterChange("practice_area", e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg mt-1"
            >
              <option value="">All</option>
              {PRACTICE_AREAS.map((area) => (
                <option key={area} value={area}>
                  {area.charAt(0).toUpperCase() + area.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600">Outcome</label>
            <select
              value={filters.outcome}
              onChange={(e) => handleFilterChange("outcome", e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg mt-1"
            >
              <option value="">All</option>
              {OUTCOMES.map((outcome) => (
                <option key={outcome} value={outcome}>
                  {outcome.replace(/_/g, " ").toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600">Language</label>
            <select
              value={filters.language}
              onChange={(e) => handleFilterChange("language", e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg mt-1"
            >
              <option value="">All</option>
              <option value="en">English</option>
              <option value="bm">Bahasa Malaysia</option>
              <option value="ta">Tamil</option>
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600">Year From</label>
            <input
              type="number"
              value={filters.year_from || ""}
              onChange={(e) => handleFilterChange("year_from", e.target.value ? parseInt(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg mt-1"
              placeholder="YYYY"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600">Year To</label>
            <input
              type="number"
              value={filters.year_to || ""}
              onChange={(e) => handleFilterChange("year_to", e.target.value ? parseInt(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg mt-1"
              placeholder="YYYY"
            />
          </div>
        </div>

        {/* Results */}
        <div className="md:col-span-3 space-y-4">
          {isLoading && <p className="text-slate-600">Loading...</p>}

          {results.length === 0 && !isLoading && (
            <p className="text-slate-600">No results found. Try refining your search.</p>
          )}

          {results.map((result) => (
            <div key={result.id} className="border border-slate-200 rounded-lg p-6 hover:shadow-lg transition">
              <div className="flex items-start justify-between mb-2">
                <div>
                  {result.citation && <p className="text-sm text-slate-500">{result.citation}</p>}
                  <Link href={`/cases/${result.id}`} className="text-lg font-semibold text-primary hover:underline">
                    {result.title}
                  </Link>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 mb-3">
                {result.court_name && (
                  <Badge variant="outline">{result.court_name}</Badge>
                )}
                {result.practice_area && (
                  <Badge variant="secondary">{result.practice_area}</Badge>
                )}
                {result.outcome && (
                  <Badge>{result.outcome}</Badge>
                )}
              </div>

              <p className="text-slate-600 mb-3">{result.snippet}</p>

              <div className="flex gap-4 text-sm text-slate-500">
                {result.judge_name && <p>Judge: {result.judge_name}</p>}
                {result.date_decided && <p>Decided: {result.date_decided}</p>}
              </div>
            </div>
          ))}

          {/* Pagination */}
          {results.length > 0 && (
            <div className="flex gap-2 justify-center pt-4">
              <Button
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={offset === 0}
                variant="outline"
              >
                Previous
              </Button>
              <Button
                onClick={() => setOffset(offset + limit)}
                disabled={results.length < limit}
                variant="outline"
              >
                Next
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
