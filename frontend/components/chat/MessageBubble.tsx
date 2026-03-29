"use client";
import { cn, formatINR } from "@/lib/utils";
import { TrendingUp, Shield, Target, Lightbulb, Zap, ChevronRight, AlertTriangle } from "lucide-react";

interface Props { role: "user" | "assistant"; content: string }

interface AdvisorPlan {
  headline?: string;
  tone_opener?: string;
  tax?: {
    recommended_regime: string;
    annual_saving: number;
    monthly_saving: number;
    their_tax: number;
    effective_rate: number;
    monthly_tds: number;
    regime_reason: string;
  };
  deductions?: { section: string; what: string; gap: number; saving: number; how: string }[];
  fire?: {
    corpus_needed: number;
    retire_at_age: number;
    monthly_sip_needed: number;
    current_monthly_savings: number;
    emergency_fund_gap: number;
    allocation: string;
  };
  actions?: { priority: number; action: string; impact: string; timeline: string }[];
  insight?: string;
  life_event_advice?: string;
}

function safeStr(val: unknown): string {
  if (val == null) return "";
  if (typeof val === "string") return val;
  if (typeof val === "number") return String(val);
  if (typeof val === "object") {
    // advisor returned an object instead of string — extract useful text
    const obj = val as Record<string, unknown>;
    if (obj.advice_points && Array.isArray(obj.advice_points)) return (obj.advice_points as string[]).join(" • ");
    if (obj.regime_reason) return String(obj.regime_reason);
    return JSON.stringify(val);
  }
  return String(val);
}

function tryParseJSON(text: string): AdvisorPlan | null {
  try {
    let clean = text.replace(/^```(?:json)?\s*/m, "").replace(/\s*```$/m, "").trim();
    const start = clean.indexOf("{");
    const end = clean.lastIndexOf("}");
    if (start === -1 || end === -1) return null;
    clean = clean.slice(start, end + 1);
    const parsed = JSON.parse(clean);
    if (parsed.headline || parsed.tax || parsed.fire || parsed.actions) return parsed;
  } catch {}
  return null;
}

function SectionHeader({ icon, label, accent }: { icon: React.ReactNode; label: string; accent?: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 border-b et-sans" style={{ background: accent || "#fafafa", borderColor: "var(--et-border)" }}>
      <span className="opacity-70">{icon}</span>
      <span className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-text-muted)" }}>{label}</span>
    </div>
  );
}

function MiniStat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="rounded-lg px-3 py-2 et-sans" style={{ background: "#f9f9f9", border: "1px solid var(--et-border)" }}>
      <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>{label}</p>
      <p className={cn("text-sm font-bold", highlight ? "et-red-text" : "")} style={highlight ? { color: "var(--et-red)" } : { color: "var(--et-text)" }}>{value}</p>
    </div>
  );
}

function PlanCard({ plan }: { plan: AdvisorPlan }) {
  return (
    <div className="space-y-3 w-full et-sans">

      {/* Opener */}
      {plan.tone_opener && (
        <p className="text-sm leading-relaxed" style={{ color: "var(--et-text-muted)" }}>{safeStr(plan.tone_opener)}</p>
      )}

      {/* Headline */}
      {plan.headline && (
        <div className="flex items-start gap-2.5 rounded-lg px-4 py-3" style={{ background: "var(--et-red)", color: "white" }}>
          <Zap className="w-4 h-4 shrink-0 mt-0.5 opacity-90" />
          <p className="font-bold text-sm leading-snug">{safeStr(plan.headline)}</p>
        </div>
      )}

      {/* Tax card */}
      {plan.tax && (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid var(--et-border)" }}>
          <SectionHeader icon={<Shield className="w-3.5 h-3.5" />} label="Tax Snapshot" />
          <div className="px-4 py-3 space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>Best regime for you</p>
                <p className="font-bold text-base capitalize" style={{ color: "var(--et-text)" }}>
                  {plan.tax.recommended_regime === "new" ? "New Tax Regime" : "Old Tax Regime"}
                </p>
              </div>
      {plan.tax.annual_saving > 0 && (
                <div className="text-right">
                  <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>Annual saving</p>
                  <p className="font-black text-xl" style={{ color: "var(--et-red)" }}>{formatINR(plan.tax.annual_saving)}</p>
                  <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>{formatINR(plan.tax.monthly_saving)}/month</p>
                </div>
              )}
            </div>
            {plan.tax.regime_reason && (
              <p className="text-xs leading-relaxed rounded-lg px-3 py-2" style={{ background: "#fff8f8", color: "var(--et-text-muted)", border: "1px solid #fde8e8" }}>
                {safeStr(plan.tax.regime_reason)}
              </p>
            )}
            <div className="grid grid-cols-3 gap-2">
              <MiniStat label="Your tax" value={formatINR(plan.tax.their_tax ?? 0)} />
              <MiniStat label="Effective rate" value={`${plan.tax.effective_rate ?? 0}%`} />
              <MiniStat label="Monthly TDS" value={formatINR(plan.tax.monthly_tds ?? 0)} />
            </div>
          </div>
        </div>
      )}

      {/* Deductions */}
      {plan.deductions && plan.deductions.length > 0 && (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid #fbbf24" }}>
          <div className="flex items-center justify-between px-4 py-2 border-b et-sans" style={{ background: "#fffbeb", borderColor: "#fbbf24" }}>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              <span className="text-xs font-black uppercase tracking-widest text-amber-700">Unclaimed Deductions</span>
            </div>
            <span className="text-xs font-bold text-amber-700">
              Save {formatINR(plan.deductions.reduce((s, d) => s + (d?.saving ?? 0), 0))} more
            </span>
          </div>
          <div className="divide-y" style={{ borderColor: "var(--et-border)" }}>
            {plan.deductions.map((d, i) => (
              <div key={i} className="px-4 py-3 bg-white">
                <div className="flex items-start justify-between mb-1.5">
                  <div>
                    <span className="text-xs font-bold" style={{ color: "var(--et-text)" }}>Sec {d.section}</span>
                    <span className="text-xs ml-1" style={{ color: "var(--et-text-muted)" }}>— {safeStr(d.what)}</span>
                  </div>
                  <span className="text-xs font-bold text-green-600 shrink-0 ml-2">Save {formatINR(d.saving)}</span>
                </div>
                <p className="text-xs leading-relaxed flex items-start gap-1" style={{ color: "var(--et-text-muted)" }}>
                  <ChevronRight className="w-3 h-3 shrink-0 mt-0.5" style={{ color: "var(--et-red)" }} />
                  {safeStr(d.how)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* FIRE */}
      {plan.fire && (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid #86efac" }}>
          <SectionHeader icon={<TrendingUp className="w-3.5 h-3.5 text-green-600" />} label="Retirement Plan" accent="#f0fdf4" />
          <div className="px-4 py-3 space-y-3 bg-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>You can retire at</p>
                <p className="text-3xl font-black" style={{ color: "var(--et-text)" }}>Age {plan.fire.retire_at_age}</p>
              </div>
              <div className="text-right">
                <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>Corpus needed</p>
                <p className="font-bold text-lg" style={{ color: "var(--et-text)" }}>{formatINR(plan.fire.corpus_needed)}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <MiniStat label="Monthly SIP needed" value={formatINR(plan.fire.monthly_sip_needed ?? 0)} highlight />
              <MiniStat label="Current savings/mo" value={formatINR(plan.fire.current_monthly_savings ?? 0)} />
            </div>
            {plan.fire.allocation && (
              <div className="rounded-lg px-3 py-2" style={{ background: "#f9f9f9", border: "1px solid var(--et-border)" }}>
                <p className="text-xs mb-0.5" style={{ color: "var(--et-text-muted)" }}>Suggested allocation</p>
                <p className="text-xs font-semibold" style={{ color: "var(--et-text)" }}>{plan.fire.allocation}</p>
              </div>
            )}
            {plan.fire.emergency_fund_gap != null && plan.fire.emergency_fund_gap > 0 && (
              <div className="rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: "#fff0f1", border: "1px solid #fecdd3" }}>
                <p className="text-xs" style={{ color: "var(--et-red)" }}>Emergency fund gap</p>
                <p className="text-xs font-bold" style={{ color: "var(--et-red)" }}>{formatINR(plan.fire.emergency_fund_gap)} short</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Life event */}
      {plan.life_event_advice && (
        <div className="rounded-lg px-4 py-3" style={{ background: "#faf5ff", border: "1px solid #d8b4fe" }}>
          <p className="text-xs font-black uppercase tracking-widest text-purple-600 mb-1.5">Life Event Advice</p>
          <p className="text-sm leading-relaxed" style={{ color: "var(--et-text)" }}>{safeStr(plan.life_event_advice)}</p>
        </div>
      )}

      {/* Next actions */}
      {plan.actions && plan.actions.length > 0 && (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid var(--et-border)" }}>
          <SectionHeader icon={<Target className="w-3.5 h-3.5" />} label="Your Next Steps" />
          <div className="divide-y bg-white" style={{ borderColor: "var(--et-border)" }}>
            {plan.actions.map((a, i) => (
              <div key={i} className="px-4 py-3 flex gap-3">
                <div className="w-6 h-6 rounded-full text-white text-xs font-black flex items-center justify-center shrink-0 mt-0.5" style={{ background: "var(--et-red)" }}>
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm leading-snug" style={{ color: "var(--et-text)" }}>{safeStr(a.action)}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs font-bold text-green-600">{safeStr(a.impact)}</span>
                    <span className="text-xs" style={{ color: "var(--et-text-muted)" }}>{safeStr(a.timeline)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insight */}
      {plan.insight && (
        <div className="flex gap-2.5 rounded-lg px-4 py-3" style={{ background: "#eff6ff", border: "1px solid #bfdbfe" }}>
          <Lightbulb className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
          <p className="text-xs leading-relaxed" style={{ color: "#1e40af" }}>{safeStr(plan.insight)}</p>
        </div>
      )}

      {/* SEBI Disclaimer */}
      <div className="rounded-lg px-3 py-2.5 et-sans" style={{ background: "#f9f9f9", border: "1px solid var(--et-border)" }}>
        <p className="text-xs leading-relaxed" style={{ color: "var(--et-text-muted)" }}>
          📋 AI-generated guidance for educational purposes only. Not licensed financial, tax, or investment advice under SEBI (Investment Advisers) Regulations 2013 or the Income Tax Act 1961.
          Consult a SEBI-registered Investment Adviser (RIA) or Chartered Accountant before acting.{" "}
          <a href="https://sebi.gov.in/investors" target="_blank" rel="noopener noreferrer" style={{ color: "var(--et-red)" }}>
            sebi.gov.in/investors
          </a>
        </p>
      </div>
    </div>
  );
}

function PlainMessage({ content }: { content: string }) {
  const clean = content.replace(/\*\*/g, "").replace(/^#{1,3}\s/gm, "").replace(/^─+$/gm, "").trim();
  return <p className="text-sm leading-relaxed whitespace-pre-wrap et-sans" style={{ color: "var(--et-text)" }}>{clean}</p>;
}

export function MessageBubble({ role, content }: Props) {
  const isUser = role === "user";

  if (isUser) {
    return (
      <div className="flex w-full mb-4 justify-end">
        <div className="max-w-[78%] rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap text-white et-sans" style={{ background: "var(--et-red)" }}>
          {content}
        </div>
      </div>
    );
  }

  const plan = tryParseJSON(content);

  // Streaming placeholder
  if (content === "__streaming__") {
    return (
      <div className="flex w-full mb-4 justify-start">
        <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-black mr-2 shrink-0 mt-1" style={{ background: "var(--et-red)", fontFamily: "Georgia, serif" }}>ET</div>
        <div className="bg-white rounded-2xl rounded-tl-sm shadow-sm px-4 py-3" style={{ border: "1px solid var(--et-border)" }}>
          <div className="flex gap-1 items-center">
            {[0,1,2].map(i => <span key={i} className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: "var(--et-red)", animationDelay: `${i * 0.15}s` }} />)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full mb-4 justify-start">
      <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-black mr-2 shrink-0 mt-1" style={{ background: "var(--et-red)", fontFamily: "Georgia, serif" }}>
        ET
      </div>
      <div className="max-w-[86%] bg-white rounded-2xl rounded-tl-sm shadow-sm px-4 py-3" style={{ border: "1px solid var(--et-border)" }}>
        {plan ? <PlanCard plan={plan} /> : <PlainMessage content={content} />}
      </div>
    </div>
  );
}
