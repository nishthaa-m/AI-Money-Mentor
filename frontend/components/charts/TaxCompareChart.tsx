"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { formatINR } from "@/lib/utils";

interface TaxData {
  new_regime: { total_tax: number; effective_rate_pct: number };
  old_regime: { total_tax: number; effective_rate_pct: number };
  recommended_regime: string;
  tax_saving_with_recommended: number;
  verdict: string;
}

export function TaxCompareChart({ data }: { data: TaxData }) {
  if (!data) return null;
  const chartData = [
    { name: "New Regime", tax: data.new_regime.total_tax },
    { name: "Old Regime", tax: data.old_regime.total_tax },
  ];
  const rec = data.recommended_regime;
  return (
    <div className="mt-3 rounded-lg overflow-hidden et-sans" style={{ border: "1px solid var(--et-border)" }}>
      <div className="px-3 py-2 border-b" style={{ background: "#fff0f1", borderColor: "#fde8e8" }}>
        <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-red)" }}>Tax Comparison</p>
        <p className="text-xs text-green-600 font-semibold mt-0.5">{data.verdict}</p>
      </div>
      <div className="bg-white px-2 py-3">
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={chartData} barSize={36}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fontFamily: "sans-serif" }} />
            <YAxis tickFormatter={(v) => formatINR(v)} tick={{ fontSize: 10, fontFamily: "sans-serif" }} width={65} />
            <Tooltip formatter={(v: number) => [formatINR(v), "Total Tax"]} />
            <Bar dataKey="tax" radius={[3, 3, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.name.toLowerCase().includes(rec) ? "#e8001c" : "#d1d5db"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
