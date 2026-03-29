"use client";
import { formatINR } from "@/lib/utils";
import { useState } from "react";

interface RoadmapMonth {
  month: number;
  month_label: string;
  actions: string[];
  invest_amount: number;
  running_corpus: number;
  focus: string;
}

const FOCUS_COLORS: Record<string, string> = {
  "Emergency Fund": "bg-red-50 text-red-600 border-red-200",
  "Tax Saving":     "bg-amber-50 text-amber-600 border-amber-200",
  "Wealth Building":"bg-green-50 text-green-600 border-green-200",
  "Goal SIPs":      "bg-blue-50 text-blue-600 border-blue-200",
};

export function MonthlyRoadmap({ data }: { data: RoadmapMonth[] }) {
  const [expanded, setExpanded] = useState(false);
  if (!data?.length) return null;

  const visible = expanded ? data : data.slice(0, 3);

  return (
    <div className="rounded-lg overflow-hidden et-sans" style={{ border: "1px solid var(--et-border)" }}>
      <div className="px-3 py-2 border-b flex items-center justify-between"
        style={{ background: "#f0fdf4", borderColor: "#86efac" }}>
        <p className="text-xs font-black uppercase tracking-widest text-green-700">
          12-Month Roadmap
        </p>
        <button onClick={() => setExpanded(e => !e)}
          className="text-xs font-semibold text-green-600 hover:underline">
          {expanded ? "Show less" : "See all 12 months"}
        </button>
      </div>

      <div className="bg-white divide-y" style={{ borderColor: "var(--et-border)" }}>
        {visible.map((m) => (
          <div key={m.month} className="px-3 py-2.5">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full text-white text-xs font-black flex items-center justify-center shrink-0"
                  style={{ background: "var(--et-red)", fontSize: "10px" }}>
                  {m.month}
                </span>
                <span className="text-xs font-bold" style={{ color: "var(--et-text)" }}>{m.month_label}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded-full border ${FOCUS_COLORS[m.focus] || "bg-gray-50 text-gray-500 border-gray-200"}`}>
                  {m.focus}
                </span>
              </div>
              <div className="text-right">
                <p className="text-xs font-bold" style={{ color: "var(--et-red)" }}>
                  Invest {formatINR(m.invest_amount)}
                </p>
                <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>
                  Corpus: {formatINR(m.running_corpus)}
                </p>
              </div>
            </div>
            <div className="space-y-0.5 pl-8">
              {m.actions.map((action, i) => (
                <p key={i} className="text-xs" style={{ color: "var(--et-text-muted)" }}>
                  • {action}
                </p>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
