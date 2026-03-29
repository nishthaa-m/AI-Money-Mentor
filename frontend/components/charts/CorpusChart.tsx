"use client";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { formatINR } from "@/lib/utils";

interface DataPoint { year: number; corpus: number }

export function CorpusChart({ data }: { data: DataPoint[] }) {
  if (!data?.length) return null;
  return (
    <div className="mt-3 rounded-lg overflow-hidden et-sans" style={{ border: "1px solid var(--et-border)" }}>
      <div className="px-3 py-2 border-b" style={{ background: "#f0fdf4", borderColor: "#86efac" }}>
        <p className="text-xs font-black uppercase tracking-widest text-green-700">Corpus Growth</p>
      </div>
      <div className="bg-white px-2 py-3">
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="corpusGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#e8001c" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#e8001c" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="year" tick={{ fontSize: 11, fontFamily: "sans-serif" }} label={{ value: "Years", position: "insideBottom", offset: -2, fontSize: 10 }} />
            <YAxis tickFormatter={(v) => formatINR(v)} tick={{ fontSize: 10, fontFamily: "sans-serif" }} width={65} />
            <Tooltip formatter={(v: number) => [formatINR(v), "Corpus"]} />
            <Area type="monotone" dataKey="corpus" stroke="#e8001c" fill="url(#corpusGrad)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
