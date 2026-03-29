"use client";
import { formatINR } from "@/lib/utils";

interface Props { calculations: Record<string, any> | null }

export function ImpactPanel({ calculations }: Props) {
  if (!calculations) return null;
  const tax = calculations.tax_comparison;
  const fire = calculations.fire;
  const missed = calculations.missed_deductions;

  return (
    <div className="space-y-3 et-sans">
      {tax && (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid #fde8e8" }}>
          <div className="px-3 py-2 border-b" style={{ background: "#fff0f1", borderColor: "#fde8e8" }}>
            <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-red)" }}>Tax Impact</p>
          </div>
          <div className="px-3 py-3 grid grid-cols-2 gap-3 bg-white">
            <Stat label="Best Regime" value={tax.recommended_regime === "new" ? "New Regime" : "Old Regime"} />
            <Stat label="Tax Saved" value={formatINR(tax.tax_saving_with_recommended)} highlight />
            <Stat label="Effective Rate" value={`${tax[`${tax.recommended_regime}_regime`]?.effective_rate_pct}%`} />
            <Stat label="Monthly Tax" value={formatINR(tax[`${tax.recommended_regime}_regime`]?.monthly_tax)} />
          </div>
        </div>
      )}

      {missed && missed.length > 0 && (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid #fbbf24" }}>
          <div className="px-3 py-2 border-b" style={{ background: "#fffbeb", borderColor: "#fbbf24" }}>
            <p className="text-xs font-black uppercase tracking-widest text-amber-700">
              ⚠ Missed — {formatINR(missed.reduce((s: number, d: any) => s + d.gap, 0))} unclaimed
            </p>
          </div>
          <div className="bg-white divide-y" style={{ borderColor: "var(--et-border)" }}>
            {missed.map((d: any) => (
              <div key={d.section} className="flex justify-between items-center px-3 py-2 text-xs">
                <span style={{ color: "var(--et-text)" }}>{d.section}</span>
                <span className="font-bold text-green-600">Save {formatINR(d.tax_saving_estimate)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {fire && (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid #86efac" }}>
          <div className="px-3 py-2 border-b" style={{ background: "#f0fdf4", borderColor: "#86efac" }}>
            <p className="text-xs font-black uppercase tracking-widest text-green-700">Retirement</p>
          </div>
          <div className="px-3 py-3 grid grid-cols-2 gap-3 bg-white">
            <Stat label="FIRE Number" value={formatINR(fire.fire_number)} highlight />
            <Stat label="Retire at Age" value={`${fire.fire_age} yrs`} />
            <Stat label="Emergency Fund" value={formatINR(fire.emergency_fund_target)} />
            <Stat label="Monthly Savings" value={formatINR(fire.monthly_savings_available)} />
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>{label}</p>
      <p className="text-sm font-bold" style={{ color: highlight ? "var(--et-red)" : "var(--et-text)" }}>{value}</p>
    </div>
  );
}
