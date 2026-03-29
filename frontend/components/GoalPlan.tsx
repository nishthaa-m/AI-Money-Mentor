"use client";
import { formatINR } from "@/lib/utils";
import { Target } from "lucide-react";

interface GoalItem {
  name: string;
  target_amount: number;
  target_years: number;
  monthly_sip: number;
  instrument: string;
  return_assumed: number;
  feasible: boolean;
}

interface GoalPlanData {
  goals: GoalItem[];
  total_sip_needed: number;
  monthly_investable: number;
  surplus_after_sips: number;
  all_goals_feasible: boolean;
}

export function GoalPlan({ data }: { data: GoalPlanData }) {
  if (!data?.goals?.length) return null;

  return (
    <div className="rounded-lg overflow-hidden et-sans" style={{ border: "1px solid var(--et-border)" }}>
      <div className="px-3 py-2 border-b flex items-center justify-between"
        style={{ background: "#eff6ff", borderColor: "#bfdbfe" }}>
        <div className="flex items-center gap-2">
          <Target className="w-3.5 h-3.5 text-blue-600" />
          <p className="text-xs font-black uppercase tracking-widest text-blue-700">Goal-Based SIP Plan</p>
        </div>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${data.all_goals_feasible ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"}`}>
          {data.all_goals_feasible ? "All goals feasible" : "Needs adjustment"}
        </span>
      </div>

      <div className="bg-white divide-y" style={{ borderColor: "var(--et-border)" }}>
        {data.goals.map((g, i) => (
          <div key={i} className="px-3 py-2.5">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold" style={{ color: "var(--et-text)" }}>{g.name}</p>
                <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>
                  {formatINR(g.target_amount)} in {g.target_years} yrs · {g.instrument}
                </p>
              </div>
              <div className="text-right shrink-0 ml-3">
                <p className="text-sm font-black" style={{ color: "var(--et-red)" }}>
                  {formatINR(g.monthly_sip)}/mo
                </p>
                <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>
                  @{g.return_assumed}% p.a.
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="px-3 py-2.5 border-t" style={{ background: "#f9f9f9", borderColor: "var(--et-border)" }}>
        <div className="flex justify-between text-xs">
          <span style={{ color: "var(--et-text-muted)" }}>Total SIP needed</span>
          <span className="font-bold" style={{ color: "var(--et-text)" }}>{formatINR(data.total_sip_needed)}/mo</span>
        </div>
        <div className="flex justify-between text-xs mt-1">
          <span style={{ color: "var(--et-text-muted)" }}>Monthly investable</span>
          <span className="font-bold" style={{ color: "var(--et-text)" }}>{formatINR(data.monthly_investable)}/mo</span>
        </div>
        <div className="flex justify-between text-xs mt-1">
          <span style={{ color: "var(--et-text-muted)" }}>Surplus after SIPs</span>
          <span className={`font-bold ${data.surplus_after_sips >= 0 ? "text-green-600" : "text-red-600"}`}>
            {formatINR(Math.abs(data.surplus_after_sips))}{data.surplus_after_sips < 0 ? " shortfall" : " remaining"}
          </span>
        </div>
      </div>
    </div>
  );
}
