"use client";
import { formatINR } from "@/lib/utils";

interface SipCategory {
  category: string;
  monthly_sip: number;
  allocation_pct: number;
  rationale: string;
  risk: string;
  liquidity: string;
}

const RISK_COLOR: Record<string, string> = {
  "Very Low": "text-green-600",
  "Low": "text-green-500",
  "Medium": "text-amber-500",
  "Medium-High": "text-orange-500",
  "High": "text-red-500",
};

export function SipByCategory({ data, totalSip }: { data: SipCategory[]; totalSip: number }) {
  if (!data?.length) return null;

  return (
    <div className="rounded-lg overflow-hidden et-sans" style={{ border: "1px solid var(--et-border)" }}>
      <div className="px-3 py-2 border-b flex items-center justify-between"
        style={{ background: "#eff6ff", borderColor: "#bfdbfe" }}>
        <p className="text-xs font-black uppercase tracking-widest text-blue-700">SIP by Fund Category</p>
        <p className="text-xs font-bold text-blue-600">Total: {formatINR(totalSip)}/mo</p>
      </div>
      <div className="bg-white divide-y" style={{ borderColor: "var(--et-border)" }}>
        {data.map((c, i) => (
          <div key={i} className="px-3 py-2.5">
            <div className="flex items-start justify-between mb-1">
              <p className="text-xs font-semibold flex-1 pr-2" style={{ color: "var(--et-text)" }}>{c.category}</p>
              <p className="text-sm font-black shrink-0" style={{ color: "var(--et-red)" }}>{formatINR(c.monthly_sip)}/mo</p>
            </div>
            <p className="text-xs mb-1" style={{ color: "var(--et-text-muted)" }}>{c.rationale}</p>
            <div className="flex gap-3 text-xs">
              <span>Risk: <span className={`font-semibold ${RISK_COLOR[c.risk] || "text-gray-600"}`}>{c.risk}</span></span>
              <span style={{ color: "var(--et-text-muted)" }}>Liquidity: {c.liquidity}</span>
            </div>
            {/* Mini allocation bar */}
            <div className="mt-1.5 h-1 rounded-full bg-gray-100 overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${c.allocation_pct}%`, background: "var(--et-red)", opacity: 0.6 }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
