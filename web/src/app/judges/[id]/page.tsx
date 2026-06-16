"use client";

import useSWR from "swr";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { getJudge, getJudgeAnalytics, getJudgeCases } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

interface PageParams {
  params: {
    id: string;
  };
}

export default function JudgePage({ params }: PageParams) {
  const { data: judge, isLoading: judgeLoading } = useSWR(
    `/judges/${params.id}`,
    () => getJudge(params.id)
  );

  const { data: analytics, isLoading: analyticsLoading } = useSWR(
    `/judges/${params.id}/analytics`,
    () => getJudgeAnalytics(params.id).catch(() => null),
    { revalidateOnFocus: false }
  );

  const { data: cases = [], isLoading: casesLoading } = useSWR(
    `/judges/${params.id}/cases`,
    () => getJudgeCases(params.id, { limit: 10 })
  );

  if (judgeLoading) return <div className="max-w-7xl mx-auto px-4 py-8">Loading...</div>;
  if (!judge) return <div className="max-w-7xl mx-auto px-4 py-8">Judge not found</div>;

  // Parse practice areas for chart
  const practiceAreaData = analytics?.top_practice_areas
    ? analytics.top_practice_areas.split(",").map((area) => ({
        name: area.trim(),
        value: Math.random() * 100,
      }))
    : [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Judge Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-slate-900">{judge.name}</h1>
        <p className="text-lg text-slate-600 mt-2">
          {judge.court_name ? `${judge.court_name}, ` : ""}
          {judge.state || "Malaysia"}
        </p>
        {judge.court_type && <Badge className="mt-2">{judge.court_type}</Badge>}
      </div>

      {/* Analytics Stats */}
      {analytics && !analyticsLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="border border-slate-200 rounded-lg p-6">
            <p className="text-sm text-slate-600 font-medium">Total Decisions</p>
            <p className="text-3xl font-bold text-primary mt-2">{analytics.total_decisions}</p>
          </div>

          <div className="border border-slate-200 rounded-lg p-6">
            <p className="text-sm text-slate-600 font-medium">Plaintiff Favourable Rate</p>
            <p className="text-3xl font-bold text-primary mt-2">
              {analytics.plaintiff_favourable_rate ? (analytics.plaintiff_favourable_rate * 100).toFixed(1) : "N/A"}%
            </p>
          </div>

          <div className="border border-slate-200 rounded-lg p-6">
            <p className="text-sm text-slate-600 font-medium">Avg Disposal Days</p>
            <p className="text-3xl font-bold text-primary mt-2">
              {analytics.avg_disposal_days ? analytics.avg_disposal_days.toFixed(0) : "N/A"}
            </p>
          </div>

          <div className="border border-slate-200 rounded-lg p-6">
            <p className="text-sm text-slate-600 font-medium">Costs Awarded Rate</p>
            <p className="text-3xl font-bold text-primary mt-2">
              {analytics.costs_awarded_rate ? (analytics.costs_awarded_rate * 100).toFixed(1) : "N/A"}%
            </p>
          </div>
        </div>
      ) : null}

      {/* Practice Area Chart */}
      {practiceAreaData.length > 0 && (
        <div className="border border-slate-200 rounded-lg p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Practice Area Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={practiceAreaData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#0F6E56" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent Cases Table */}
      {!casesLoading && cases.length > 0 && (
        <div className="border border-slate-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Cases (Last 10)</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-3 px-4 font-semibold text-slate-900">Case Number</th>
                  <th className="text-left py-3 px-4 font-semibold text-slate-900">Title</th>
                  <th className="text-left py-3 px-4 font-semibold text-slate-900">Practice Area</th>
                  <th className="text-left py-3 px-4 font-semibold text-slate-900">Outcome</th>
                  <th className="text-left py-3 px-4 font-semibold text-slate-900">Date</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((caseItem: any) => (
                  <tr key={caseItem.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-4">{caseItem.case_number || "-"}</td>
                    <td className="py-3 px-4">
                      <Link href={`/cases/${caseItem.id}`} className="text-primary hover:underline">
                        {caseItem.title.substring(0, 50)}...
                      </Link>
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant="secondary">{caseItem.practice_area}</Badge>
                    </td>
                    <td className="py-3 px-4">{caseItem.outcome}</td>
                    <td className="py-3 px-4">{caseItem.date_decided || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
