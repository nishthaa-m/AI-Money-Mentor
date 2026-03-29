"use client";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface GlidepathPoint { age: number; equity_pct: number; debt_pct: number }

export function GlidepathChart({ data }: { data: GlidepathPoint[] }) {
  if (!data?.length) return null;
  // Sample every 2 years to avoid clutter
  const sampled = data.filter((_, i) => i % 2 === 0);

  return (
    <div className="rounded-lg overflow-hidden et-sans mt-3" style={{ border: "1px solid var(--et-border)" }}>
      <div className="px-3 py-2 border-b" style={{ background: "#f0fdf4", borderColor: "#86efac" }}>
        <p className="text-xs font-black uppercase tracking-widest text-green-700">Asset Allocation Glidepath</p>
        <p className="text-xs text-green-600">Equity reduces as you approach retirement</p>
      </div>
      <div className="bg-white px-2 py-3">
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={sampled}>
            <defs>
              <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#e8001c" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#e8001c" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="debtGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#16a34a" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#16a34a" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="age" tick={{ fontSize: 10 }} label={{ value: "Age", position: "insideBottom", offset: -2, fontSize: 10 }} />
            <YAxis domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fontSize: 10 }} width={35} />
            <Tooltip formatter={(v: unknown) => [`${v}%`]} labelFormatter={(label) => `Age ${label}`} />
            <Legend formatter={v => v === "equity_pct" ? "Equity" : "Debt"} />
            <Area type="monotone" dataKey="equity_pct" stroke="#e8001c" fill="url(#equityGrad)" strokeWidth={2} />
            <Area type="monotone" dataKey="debt_pct" stroke="#16a34a" fill="url(#debtGrad)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
