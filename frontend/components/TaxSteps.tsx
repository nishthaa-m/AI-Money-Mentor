"use client";
import { formatINR } from "@/lib/utils";
import { useState } from "react";

interface Step {
  step: number;
  label: string;
  amount: number;
  note: string;
}

interface TaxStepsData {
  regime: string;
  total_tax: number;
  effective_rate_pct: number;
  steps: Step[];
}

export function TaxSteps({ newData, oldData, recommended }: {
  newData: TaxStepsData;
  oldData: TaxStepsData;
  recommended: string;
}) {
  const [active, setActive] = useState<"new" | "old">(recommended as "new" | "old");
  const data = active === "new" ? newData : oldData;
  if (!data?.steps?.length) return null;

  return (
    <div className="rounded-lg overflow-hidden et-sans mt-3" style={{ border: "1px solid var(--et-border)" }}>
      <div className="px-3 py-2 border-b flex items-center justify-between"
        style={{ background: "#fff0f1", borderColor: "#fde8e8" }}>
        <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-red)" }}>
          Step-by-Step Tax Calculation
        </p>
        <div className="flex gap-1">
          {(["new", "old"] as const).map(r => (
            <button key={r} onClick={() => setActive(r)}
              className="text-xs px-2 py-0.5 rounded font-semibold transition-colors"
              style={{
                background: active === r ? "var(--et-red)" : "#f5f5f5",
                color: active === r ? "white" : "var(--et-text-muted)",
              }}>
              {r === "new" ? "New Regime" : "Old Regime"}
              {r === recommended && <span className="ml-1">✓</span>}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white divide-y" style={{ borderColor: "var(--et-border)" }}>
        {data.steps.map((s, i) => {
          const isTotal = s.label.includes("Total Tax");
          return (
            <div key={i} className={`px-3 py-2 flex items-start justify-between gap-2 ${isTotal ? "font-bold" : ""}`}
              style={{ background: isTotal ? "#fff0f1" : "white" }}>
              <div className="flex items-start gap-2 flex-1 min-w-0">
                <span className="w-5 h-5 rounded-full text-xs flex items-center justify-center shrink-0 mt-0.5 font-bold"
                  style={{ background: isTotal ? "var(--et-red)" : "#f5f5f5", color: isTotal ? "white" : "var(--et-text-muted)" }}>
                  {s.step}
                </span>
                <div className="min-w-0">
                  <p className="text-xs" style={{ color: isTotal ? "var(--et-red)" : "var(--et-text)" }}>{s.label}</p>
                  {s.note && <p className="text-xs mt-0.5" style={{ color: "var(--et-text-muted)" }}>{s.note}</p>}
                </div>
              </div>
              <p className="text-xs font-bold shrink-0" style={{ color: s.amount < 0 ? "green" : isTotal ? "var(--et-red)" : "var(--et-text)" }}>
                {s.amount < 0 ? `−${formatINR(Math.abs(s.amount))}` : formatINR(s.amount)}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
