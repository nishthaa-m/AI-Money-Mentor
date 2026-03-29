"use client";
import { useState } from "react";
import { ArrowLeft, ChevronRight } from "lucide-react";
import { formatINR } from "@/lib/utils";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const EVENTS = [
  { id: "bonus",       emoji: "🎁", label: "Salary Bonus",   desc: "Allocate optimally across tax saving, investments, and goals." },
  { id: "inheritance", emoji: "🏛️", label: "Inheritance",    desc: "Understand tax implications and invest wisely." },
  { id: "marriage",    emoji: "💍", label: "Getting Married", desc: "Joint finances, insurance, goals — plan together." },
  { id: "baby",        emoji: "👶", label: "New Baby",        desc: "Education corpus, SSY, insurance — start from day one." },
  { id: "job_change",  emoji: "💼", label: "Job Change",      desc: "PF transfer, salary restructuring, joining bonus." },
];

type EventId = "bonus" | "inheritance" | "marriage" | "baby" | "job_change";
const EVENT_COLORS: Record<string, string> = { bonus: "#f97316", inheritance: "#8b5cf6", marriage: "#ec4899", baby: "#06b6d4", job_change: "#10b981" };

export function LifeEventsTab() {
  const [selected, setSelected] = useState<EventId | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function back() { if (result) { setResult(null); return; } setSelected(null); }

  async function submit(payload: Record<string, any>) {
    setLoading(true); setError("");
    try {
      const r = await fetch(`${API}/life-events/analyze`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ event: selected, ...payload }) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Analysis failed");
      setResult(d);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 et-sans">
      {/* Tab header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-black mb-1" style={{ color: "var(--et-text)", fontFamily: "Georgia, serif" }}>Life Event Advisor</h2>
          <p className="text-sm" style={{ color: "var(--et-text-muted)" }}>Personalised financial decisions for life's big moments</p>
        </div>
        {selected && (
          <button onClick={back} className="text-xs flex items-center gap-1 hover:underline" style={{ color: "var(--et-text-muted)" }}>
            <ArrowLeft className="w-3 h-3" /> Back
          </button>
        )}
      </div>

      {/* Event picker */}
      {!selected && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {EVENTS.map(ev => (
            <button key={ev.id} onClick={() => setSelected(ev.id as EventId)}
              className="bg-white rounded-xl p-5 text-left hover:shadow-md transition-all group"
              style={{ border: "1px solid var(--et-border)" }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = EVENT_COLORS[ev.id])}
              onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--et-border)")}>
              <div className="flex items-start justify-between">
                <span className="text-3xl mb-2 block">{ev.emoji}</span>
                <ChevronRight className="w-4 h-4 mt-1 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: EVENT_COLORS[ev.id] }} />
              </div>
              <p className="font-black text-sm mb-1" style={{ color: "var(--et-text)" }}>{ev.label}</p>
              <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>{ev.desc}</p>
            </button>
          ))}
        </div>
      )}

      {/* Forms */}
      {selected && !result && (
        <div>
          {selected === "bonus"       && <BonusForm      onSubmit={submit} loading={loading} error={error} />}
          {selected === "inheritance" && <InheritanceForm onSubmit={submit} loading={loading} error={error} />}
          {selected === "marriage"    && <MarriageForm   onSubmit={submit} loading={loading} error={error} />}
          {selected === "baby"        && <BabyForm       onSubmit={submit} loading={loading} error={error} />}
          {selected === "job_change"  && <JobChangeForm  onSubmit={submit} loading={loading} error={error} />}
        </div>
      )}

      {/* Results */}
      {result && <EventResult result={result} event={selected!} onBack={back} />}
    </div>
  );
}

// ── Shared helpers ────────────────────────────────────────────────────────────

function FormWrap({ title, children, onSubmit, loading, error }: any) {
  return (
    <div className="space-y-5">
      <h3 className="text-lg font-black" style={{ color: "var(--et-text)" }}>{title}</h3>
      <div className="bg-white rounded-xl overflow-hidden" style={{ border: "1px solid var(--et-border)" }}>
        <div className="p-5 space-y-4">{children}</div>
      </div>
      {error && <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}
      <button onClick={onSubmit} disabled={loading} className="w-full py-3 rounded-xl text-white font-black text-sm disabled:opacity-40" style={{ background: "var(--et-red)" }}>
        {loading ? "Calculating your plan..." : "Get My Financial Plan →"}
      </button>
    </div>
  );
}

function F({ label, hint, value, onChange, type = "number" }: any) {
  if (type === "checkbox") return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input type="checkbox" checked={value} onChange={e => onChange(e.target.checked)} className="w-4 h-4 accent-red-600" />
      <span className="text-sm" style={{ color: "var(--et-text)" }}>{label}</span>
      {hint && <span className="text-xs" style={{ color: "var(--et-text-muted)" }}>({hint})</span>}
    </label>
  );
  return (
    <div>
      <label className="block text-xs font-semibold mb-1" style={{ color: "var(--et-text)" }}>{label}</label>
      <input type="number" value={value} onChange={e => onChange(e.target.value)} placeholder="0"
        className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--et-border)" }} />
      {hint && <p className="text-xs mt-0.5" style={{ color: "var(--et-text-muted)" }}>{hint}</p>}
    </div>
  );
}

function Risk({ value, onChange }: any) {
  return (
    <div>
      <label className="block text-xs font-semibold mb-1" style={{ color: "var(--et-text)" }}>Risk Profile</label>
      <select value={value} onChange={e => onChange(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--et-border)" }}>
        <option value="conservative">Conservative — capital preservation</option>
        <option value="moderate">Moderate — balanced growth</option>
        <option value="aggressive">Aggressive — maximum growth</option>
      </select>
    </div>
  );
}

function num(v: string) { return Number(v) || 0; }

function BonusForm({ onSubmit, loading, error }: any) {
  const [f, setF] = useState({ amount: "", annual_income: "", monthly_expenses: "", existing_corpus: "", age: "", section_80c_invested: "", section_80ccd1b: "", risk_profile: "moderate" });
  const s = (k: string) => (v: any) => setF(p => ({ ...p, [k]: v }));
  return <FormWrap title="Salary Bonus Plan" onSubmit={() => onSubmit({ amount: num(f.amount), annual_income: num(f.annual_income), monthly_expenses: num(f.monthly_expenses), existing_corpus: num(f.existing_corpus), age: num(f.age), section_80c_invested: num(f.section_80c_invested), section_80ccd1b: num(f.section_80ccd1b), risk_profile: f.risk_profile })} loading={loading} error={error}>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <F label="Bonus Amount *" value={f.amount} onChange={s("amount")} hint="Pre-tax" />
      <F label="Annual Income *" value={f.annual_income} onChange={s("annual_income")} />
      <F label="Monthly Expenses" value={f.monthly_expenses} onChange={s("monthly_expenses")} />
      <F label="Existing Investments" value={f.existing_corpus} onChange={s("existing_corpus")} />
      <F label="Age" value={f.age} onChange={s("age")} />
      <F label="80C Invested This Year" value={f.section_80c_invested} onChange={s("section_80c_invested")} hint="ELSS, PPF, LIC" />
      <F label="NPS (80CCD)" value={f.section_80ccd1b} onChange={s("section_80ccd1b")} />
      <Risk value={f.risk_profile} onChange={s("risk_profile")} />
    </div>
  </FormWrap>;
}

function InheritanceForm({ onSubmit, loading, error }: any) {
  const [f, setF] = useState({ amount: "", annual_income: "", monthly_expenses: "", existing_corpus: "", age: "", has_home_loan: false, home_loan_outstanding: "", risk_profile: "moderate" });
  const s = (k: string) => (v: any) => setF(p => ({ ...p, [k]: v }));
  return <FormWrap title="Inheritance Plan" onSubmit={() => onSubmit({ amount: num(f.amount), annual_income: num(f.annual_income), monthly_expenses: num(f.monthly_expenses), existing_corpus: num(f.existing_corpus), age: num(f.age), has_home_loan: f.has_home_loan, home_loan_outstanding: num(f.home_loan_outstanding), risk_profile: f.risk_profile })} loading={loading} error={error}>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <F label="Inheritance Amount *" value={f.amount} onChange={s("amount")} />
      <F label="Annual Income" value={f.annual_income} onChange={s("annual_income")} />
      <F label="Monthly Expenses" value={f.monthly_expenses} onChange={s("monthly_expenses")} />
      <F label="Existing Investments" value={f.existing_corpus} onChange={s("existing_corpus")} />
      <F label="Age" value={f.age} onChange={s("age")} />
      <Risk value={f.risk_profile} onChange={s("risk_profile")} />
      <F label="Has Home Loan?" value={f.has_home_loan} onChange={s("has_home_loan")} type="checkbox" />
      {f.has_home_loan && <F label="Outstanding Loan" value={f.home_loan_outstanding} onChange={s("home_loan_outstanding")} />}
    </div>
  </FormWrap>;
}

function MarriageForm({ onSubmit, loading, error }: any) {
  const [f, setF] = useState({ annual_income: "", partner_income: "", existing_corpus: "", partner_corpus: "", monthly_expenses: "", age: "", planning_home: false, planning_child: false, risk_profile: "moderate" });
  const s = (k: string) => (v: any) => setF(p => ({ ...p, [k]: v }));
  return <FormWrap title="Marriage Financial Plan" onSubmit={() => onSubmit({ annual_income: num(f.annual_income), partner_income: num(f.partner_income), existing_corpus: num(f.existing_corpus), partner_corpus: num(f.partner_corpus), monthly_expenses: num(f.monthly_expenses), age: num(f.age), planning_home: f.planning_home, planning_child: f.planning_child, risk_profile: f.risk_profile })} loading={loading} error={error}>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <F label="Your Annual Income *" value={f.annual_income} onChange={s("annual_income")} />
      <F label="Partner's Annual Income" value={f.partner_income} onChange={s("partner_income")} />
      <F label="Your Investments" value={f.existing_corpus} onChange={s("existing_corpus")} />
      <F label="Partner's Investments" value={f.partner_corpus} onChange={s("partner_corpus")} />
      <F label="Combined Monthly Expenses" value={f.monthly_expenses} onChange={s("monthly_expenses")} />
      <F label="Your Age" value={f.age} onChange={s("age")} />
      <Risk value={f.risk_profile} onChange={s("risk_profile")} />
      <div className="col-span-full space-y-2">
        <F label="Planning to buy a home in 3 years?" value={f.planning_home} onChange={s("planning_home")} type="checkbox" />
        <F label="Planning to have children?" value={f.planning_child} onChange={s("planning_child")} type="checkbox" />
      </div>
    </div>
  </FormWrap>;
}

function BabyForm({ onSubmit, loading, error }: any) {
  const [f, setF] = useState({ annual_income: "", monthly_expenses: "", existing_corpus: "", age: "", is_girl: false, risk_profile: "moderate" });
  const s = (k: string) => (v: any) => setF(p => ({ ...p, [k]: v }));
  return <FormWrap title="New Baby Financial Plan" onSubmit={() => onSubmit({ annual_income: num(f.annual_income), monthly_expenses: num(f.monthly_expenses), existing_corpus: num(f.existing_corpus), age: num(f.age), is_girl: f.is_girl, risk_profile: f.risk_profile })} loading={loading} error={error}>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <F label="Annual Income *" value={f.annual_income} onChange={s("annual_income")} />
      <F label="Monthly Expenses" value={f.monthly_expenses} onChange={s("monthly_expenses")} hint="Current, pre-baby" />
      <F label="Existing Investments" value={f.existing_corpus} onChange={s("existing_corpus")} />
      <F label="Your Age" value={f.age} onChange={s("age")} />
      <Risk value={f.risk_profile} onChange={s("risk_profile")} />
      <F label="Baby is a girl?" value={f.is_girl} onChange={s("is_girl")} type="checkbox" hint="Unlocks SSY" />
    </div>
  </FormWrap>;
}

function JobChangeForm({ onSubmit, loading, error }: any) {
  const [f, setF] = useState({ old_income: "", annual_income: "", joining_bonus: "", pf_corpus: "", monthly_expenses: "", age: "", risk_profile: "moderate" });
  const s = (k: string) => (v: any) => setF(p => ({ ...p, [k]: v }));
  return <FormWrap title="Job Change Financial Plan" onSubmit={() => onSubmit({ old_income: num(f.old_income), annual_income: num(f.annual_income), joining_bonus: num(f.joining_bonus), pf_corpus: num(f.pf_corpus), monthly_expenses: num(f.monthly_expenses), age: num(f.age), risk_profile: f.risk_profile })} loading={loading} error={error}>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <F label="Old Annual Income *" value={f.old_income} onChange={s("old_income")} />
      <F label="New Annual Income *" value={f.annual_income} onChange={s("annual_income")} />
      <F label="Joining Bonus" value={f.joining_bonus} onChange={s("joining_bonus")} hint="0 if none" />
      <F label="PF Corpus" value={f.pf_corpus} onChange={s("pf_corpus")} hint="EPF balance" />
      <F label="Monthly Expenses" value={f.monthly_expenses} onChange={s("monthly_expenses")} />
      <F label="Age" value={f.age} onChange={s("age")} />
      <Risk value={f.risk_profile} onChange={s("risk_profile")} />
    </div>
  </FormWrap>;
}

// ── Results ───────────────────────────────────────────────────────────────────

function EventResult({ result, event, onBack }: { result: any; event: string; onBack: () => void }) {
  const color = EVENT_COLORS[event] || "var(--et-red)";
  const ev = EVENTS.find(e => e.id === event)!;
  return (
    <div className="space-y-5">
      <button onClick={onBack} className="text-xs flex items-center gap-1 hover:underline" style={{ color: "var(--et-text-muted)" }}><ArrowLeft className="w-3 h-3" /> Edit inputs</button>
      <div className="rounded-xl p-5 text-white" style={{ background: color }}>
        <p className="text-3xl mb-1">{ev.emoji}</p>
        <p className="text-xl font-black mb-1">{ev.label} — Your Financial Plan</p>
        {result.insight && <p className="text-sm opacity-90 leading-relaxed">{result.insight}</p>}
      </div>
      {result.allocation && <AllocCard allocation={result.allocation} pct={result.allocation_pct} color={color} />}
      {event === "bonus" && <div className="grid grid-cols-3 gap-3">
        <Stat label="Gross Bonus" value={formatINR(result.gross_bonus)} />
        <Stat label="Tax on Bonus" value={formatINR(result.tax_on_bonus)} sub={`${result.marginal_rate_pct}% marginal`} />
        <Stat label="Post-tax" value={formatINR(result.post_tax_bonus)} />
      </div>}
      {event === "inheritance" && <div className="rounded-xl px-4 py-3 bg-purple-50" style={{ border: "1px solid #d8b4fe" }}>
        <p className="text-xs font-bold text-purple-700 mb-1">⚖️ Tax Note</p>
        <p className="text-sm" style={{ color: "var(--et-text)" }}>{result.tax_note}</p>
        {result.stagger_note && <p className="text-xs mt-2 font-semibold text-amber-600">⚠️ {result.stagger_note}</p>}
      </div>}
      {event === "marriage" && <div className="grid grid-cols-2 gap-3">
        <Stat label="Combined Income" value={formatINR(result.combined_income)} sub="Annual" />
        <Stat label="Monthly Surplus" value={formatINR(result.monthly_surplus)} sub="To invest" />
        <Stat label="Emergency Fund" value={formatINR(result.emergency_fund_target)} sub="6 months" />
        <Stat label="Term Cover (each)" value={formatINR(result.recommended_term_cover_each)} />
        {result.goal_sips?.home_down_payment && <Stat label="Home SIP" value={`${formatINR(result.goal_sips.home_down_payment)}/mo`} />}
        {result.goal_sips?.child_education && <Stat label="Child Education SIP" value={`${formatINR(result.goal_sips.child_education)}/mo`} />}
      </div>}
      {event === "baby" && <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          {result.education_goals?.graduation && <Stat label="Graduation SIP" value={`${formatINR(result.education_goals.graduation.monthly_sip)}/mo`} sub="18 years" />}
          {result.education_goals?.pg_mba && <Stat label="PG/MBA SIP" value={`${formatINR(result.education_goals.pg_mba.monthly_sip)}/mo`} sub="22 years" />}
          <Stat label="Budget Increase" value={formatINR(result.monthly_budget_increase)} sub="/month" />
          <Stat label="Term Cover" value={formatINR(result.insurance_update?.term_cover_recommended)} sub="15x income" />
        </div>
        {result.ssy?.applicable && <div className="rounded-xl px-4 py-3 bg-cyan-50" style={{ border: "1px solid #a5f3fc" }}>
          <p className="text-xs font-bold text-cyan-700 mb-1">🌸 Sukanya Samriddhi Yojana (SSY)</p>
          <p className="text-sm" style={{ color: "var(--et-text)" }}>{result.ssy.note}</p>
        </div>}
      </div>}
      {event === "job_change" && <div className="grid grid-cols-2 gap-3">
        <Stat label="Income Increase" value={formatINR(result.income_increase)} sub={`+${result.income_increase_pct}%`} />
        <Stat label="Invest from Raise" value={`${formatINR(result.monthly_invest_from_raise)}/mo`} sub="70% of raise" />
        <Stat label="PF Corpus" value={formatINR(result.pf_corpus)} sub="Transfer — don't withdraw" />
        {result.pf_tax_if_withdrawn > 0 && <Stat label="TDS if Withdrawn" value={formatINR(result.pf_tax_if_withdrawn)} sub="Avoidable!" />}
      </div>}
      {result.checklist && <div className="bg-white rounded-xl overflow-hidden" style={{ border: "1px solid var(--et-border)" }}>
        <div className="px-4 py-2.5 border-b" style={{ background: "#fafafa", borderColor: "var(--et-border)" }}>
          <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-text-muted)" }}>Your Action Checklist</p>
        </div>
        <div className="p-4 space-y-3">
          {result.checklist.map((item: string, i: number) => (
            <div key={i} className="flex items-start gap-2.5">
              <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-white text-xs font-black" style={{ background: color }}>{i + 1}</div>
              <p className="text-sm leading-relaxed" style={{ color: "var(--et-text)" }}>{item}</p>
            </div>
          ))}
        </div>
      </div>}
      <div className="rounded-xl px-3 py-2.5" style={{ background: "#f9f9f9", border: "1px solid var(--et-border)" }}>
        <p className="text-xs leading-relaxed" style={{ color: "var(--et-text-muted)" }}>📋 AI-generated guidance for educational purposes only. Not licensed financial advice under SEBI (Investment Advisers) Regulations 2013. SEBI Helpline: 1800-266-7575</p>
      </div>
    </div>
  );
}

function AllocCard({ allocation, pct, color }: any) {
  const items = Object.entries(allocation).filter(([, v]) => (v as number) > 0);
  if (!items.length) return null;
  return <div className="bg-white rounded-xl overflow-hidden" style={{ border: "1px solid var(--et-border)" }}>
    <div className="px-4 py-2.5 border-b" style={{ background: "#fafafa", borderColor: "var(--et-border)" }}>
      <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-text-muted)" }}>Recommended Allocation</p>
    </div>
    <div className="p-4 space-y-3">
      {items.map(([key, val]) => { const p = pct?.[key] || 0; return (
        <div key={key}>
          <div className="flex justify-between text-sm mb-1">
            <span style={{ color: "var(--et-text)" }}>{key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</span>
            <span className="font-bold" style={{ color }}>{formatINR(val as number)} {p ? `(${p}%)` : ""}</span>
          </div>
          <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
            <div className="h-full rounded-full" style={{ width: `${p}%`, background: color, opacity: 0.7 }} />
          </div>
        </div>
      );})}
    </div>
  </div>;
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return <div className="bg-gray-50 rounded-lg px-3 py-2.5" style={{ border: "1px solid var(--et-border)" }}>
    <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>{label}</p>
    <p className="text-sm font-bold" style={{ color: "var(--et-text)" }}>{value}</p>
    {sub && <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>{sub}</p>}
  </div>;
}
