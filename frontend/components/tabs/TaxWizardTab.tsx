"use client";
import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, ArrowLeft, AlertTriangle, CheckCircle } from "lucide-react";
import { TaxSteps } from "@/components/TaxSteps";
import { formatINR } from "@/lib/utils";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SalaryForm {
  annual_income: string; basic_salary: string; hra_received: string; rent_paid: string;
  metro_city: boolean; section_80c_invested: string; section_80d_self: string;
  section_80d_parents: string; section_80ccd1b: string; home_loan_interest: string;
  lta: string; other_deductions: string; age: string; tds_deducted: string;
}

const EMPTY: SalaryForm = {
  annual_income: "", basic_salary: "", hra_received: "", rent_paid: "", metro_city: true,
  section_80c_invested: "", section_80d_self: "", section_80d_parents: "", section_80ccd1b: "",
  home_loan_interest: "", lta: "", other_deductions: "", age: "", tds_deducted: "",
};

export function TaxWizardTab() {
  const [mode, setMode] = useState<"landing" | "upload" | "manual" | "result">("landing");
  const [form, setForm] = useState<SalaryForm>(EMPTY);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [uploadedFile, setUploadedFile] = useState("");

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0]; if (!file) return;
    setLoading(true); setError(""); setUploadedFile(file.name);
    try {
      const fd = new FormData(); fd.append("file", file);
      const res = await fetch(`${API}/tax/upload-form16`, { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      const ext = data.extracted;
      setForm(prev => ({
        ...prev,
        annual_income: ext.annual_income ? String(ext.annual_income) : prev.annual_income,
        basic_salary: ext.basic_salary ? String(ext.basic_salary) : prev.basic_salary,
        hra_received: ext.hra_received ? String(ext.hra_received) : prev.hra_received,
        section_80c_invested: ext.section_80c_invested ? String(ext.section_80c_invested) : prev.section_80c_invested,
        section_80d_self: ext.section_80d_self ? String(ext.section_80d_self) : prev.section_80d_self,
        section_80ccd1b: ext.section_80ccd1b ? String(ext.section_80ccd1b) : prev.section_80ccd1b,
        home_loan_interest: ext.home_loan_interest ? String(ext.home_loan_interest) : prev.home_loan_interest,
        tds_deducted: ext.tds_deducted ? String(ext.tds_deducted) : prev.tds_deducted,
      }));
      setMode("manual");
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { "application/pdf": [".pdf"] }, maxFiles: 1 });

  async function analyze() {
    setLoading(true); setError("");
    try {
      const payload = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, k === "metro_city" ? v : (v === "" ? 0 : Number(v))]));
      const res = await fetch(`${API}/tax/analyze`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed");
      setResult(data); setMode("result");
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 et-sans">

      {/* Tab header */}
      <div className="mb-6">
        <h2 className="text-xl font-black mb-1" style={{ color: "var(--et-text)", fontFamily: "Georgia, serif" }}>Tax Wizard</h2>
        <p className="text-sm" style={{ color: "var(--et-text-muted)" }}>FY 2025-26 · Finance Act 2025 · Old vs New Regime · Step-by-step verifiable calculations</p>
      </div>

      {/* Landing */}
      {mode === "landing" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button onClick={() => setMode("upload")} className="bg-white rounded-xl p-6 text-left hover:shadow-md transition-shadow" style={{ border: "2px solid var(--et-red)" }}>
              <Upload className="w-8 h-8 mb-3" style={{ color: "var(--et-red)" }} />
              <p className="font-black text-base mb-1" style={{ color: "var(--et-text)" }}>Upload Form 16</p>
              <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>PDF from your employer. We extract salary, TDS, and deductions automatically.</p>
              <span className="inline-block mt-3 text-xs font-bold px-2 py-1 rounded-full" style={{ background: "#fff0f1", color: "var(--et-red)" }}>Fastest</span>
            </button>
            <button onClick={() => setMode("manual")} className="bg-white rounded-xl p-6 text-left hover:shadow-md transition-shadow" style={{ border: "1px solid var(--et-border)" }}>
              <FileText className="w-8 h-8 mb-3" style={{ color: "var(--et-text-muted)" }} />
              <p className="font-black text-base mb-1" style={{ color: "var(--et-text)" }}>Enter Manually</p>
              <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>Know your salary structure? Enter income, HRA, deductions directly.</p>
              <span className="inline-block mt-3 text-xs font-bold px-2 py-1 rounded-full bg-gray-100 text-gray-600">Full control</span>
            </button>
          </div>
        </div>
      )}

      {/* Upload */}
      {mode === "upload" && (
        <div className="space-y-4">
          <button onClick={() => setMode("landing")} className="text-xs flex items-center gap-1 hover:underline" style={{ color: "var(--et-text-muted)" }}>
            <ArrowLeft className="w-3 h-3" /> Back
          </button>
          <div {...getRootProps()} className="bg-white rounded-xl p-10 text-center cursor-pointer transition-all"
            style={{ border: `2px dashed ${isDragActive ? "var(--et-red)" : "var(--et-border)"}`, background: isDragActive ? "#fff0f1" : "white" }}>
            <input {...getInputProps()} />
            <Upload className="w-10 h-10 mx-auto mb-3" style={{ color: isDragActive ? "var(--et-red)" : "var(--et-text-muted)" }} />
            {loading ? <p className="text-sm font-semibold" style={{ color: "var(--et-red)" }}>Extracting data...</p>
              : uploadedFile ? <p className="text-sm font-semibold text-green-600">✓ {uploadedFile} uploaded</p>
              : <><p className="text-sm font-semibold" style={{ color: "var(--et-text)" }}>{isDragActive ? "Drop here" : "Drag & drop Form 16 PDF"}</p>
                  <p className="text-xs mt-1" style={{ color: "var(--et-text-muted)" }}>or click to browse · PDF only · max 10MB</p></>}
          </div>
          {error && <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}
          <p className="text-xs text-center" style={{ color: "var(--et-text-muted)" }}>🔒 PDF processed locally, never stored. PAN is masked.</p>
        </div>
      )}

      {/* Manual form */}
      {mode === "manual" && (
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <button onClick={() => setMode("landing")} className="text-xs flex items-center gap-1 hover:underline" style={{ color: "var(--et-text-muted)" }}>
              <ArrowLeft className="w-3 h-3" /> Back
            </button>
            {uploadedFile && <span className="text-xs text-green-600 font-semibold">✓ Pre-filled from {uploadedFile}</span>}
          </div>
          <div className="bg-white rounded-xl overflow-hidden" style={{ border: "1px solid var(--et-border)" }}>
            <Sec title="Income Details" />
            <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Fld label="Gross Annual Income *" name="annual_income" form={form} setForm={setForm} hint="Total CTC / gross salary" />
              <Fld label="Age" name="age" form={form} setForm={setForm} />
              <Fld label="Basic Salary (annual)" name="basic_salary" form={form} setForm={setForm} hint="~40% of CTC" />
              <Fld label="TDS Already Deducted" name="tds_deducted" form={form} setForm={setForm} />
            </div>
            <Sec title="HRA" />
            <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Fld label="HRA Received (annual)" name="hra_received" form={form} setForm={setForm} />
              <Fld label="Rent Paid (annual)" name="rent_paid" form={form} setForm={setForm} />
              <label className="flex items-center gap-2 col-span-full cursor-pointer">
                <input type="checkbox" checked={form.metro_city} onChange={e => setForm(f => ({ ...f, metro_city: e.target.checked }))} className="w-4 h-4 accent-red-600" />
                <span className="text-sm" style={{ color: "var(--et-text)" }}>Metro city (Mumbai, Delhi, Kolkata, Chennai)</span>
              </label>
            </div>
            <Sec title="Deductions (Old Regime)" />
            <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Fld label="Sec 80C" name="section_80c_invested" form={form} setForm={setForm} hint="ELSS, PPF, LIC — max ₹1.5L" />
              <Fld label="Sec 80CCD(1B) NPS" name="section_80ccd1b" form={form} setForm={setForm} hint="Extra NPS — max ₹50K" />
              <Fld label="Sec 80D — Self" name="section_80d_self" form={form} setForm={setForm} hint="Health insurance — max ₹25K" />
              <Fld label="Sec 80D — Parents" name="section_80d_parents" form={form} setForm={setForm} hint="Max ₹25K (₹50K senior)" />
              <Fld label="Sec 24(b) Home Loan Interest" name="home_loan_interest" form={form} setForm={setForm} hint="Max ₹2L" />
              <Fld label="LTA" name="lta" form={form} setForm={setForm} />
              <Fld label="Other deductions" name="other_deductions" form={form} setForm={setForm} hint="80E, 80G, 80TTA etc." />
            </div>
          </div>
          {error && <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}
          <button onClick={analyze} disabled={loading || !form.annual_income}
            className="w-full py-3 rounded-xl text-white font-black text-sm disabled:opacity-40"
            style={{ background: "var(--et-red)" }}>
            {loading ? "Calculating..." : "Calculate My Tax →"}
          </button>
        </div>
      )}

      {/* Results */}
      {mode === "result" && result && <TaxResult result={result} onBack={() => setMode("manual")} />}
    </div>
  );
}

function Sec({ title }: { title: string }) {
  return <div className="px-4 py-2.5 border-b border-t" style={{ background: "#fafafa", borderColor: "var(--et-border)" }}>
    <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-text-muted)" }}>{title}</p>
  </div>;
}

function Fld({ label, name, form, setForm, hint }: { label: string; name: keyof SalaryForm; form: SalaryForm; setForm: any; hint?: string }) {
  return <div>
    <label className="block text-xs font-semibold mb-1" style={{ color: "var(--et-text)" }}>{label}</label>
    <input type="number" value={form[name] as string} onChange={e => setForm((f: SalaryForm) => ({ ...f, [name]: e.target.value }))} placeholder="0"
      className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--et-border)" }} />
    {hint && <p className="text-xs mt-0.5" style={{ color: "var(--et-text-muted)" }}>{hint}</p>}
  </div>;
}

function TaxResult({ result, onBack }: { result: any; onBack: () => void }) {
  const s = result.summary; const tax = result.tax_comparison;
  const missed = result.missed_deductions || []; const instruments = result.tax_instruments || [];
  const hra = result.hra_calculation; const rec = s.recommended_regime;
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="text-xs flex items-center gap-1 hover:underline" style={{ color: "var(--et-text-muted)" }}><ArrowLeft className="w-3 h-3" /> Edit</button>
        <span className="text-xs" style={{ color: "var(--et-text-muted)" }}>FY 2025-26 · Finance Act 2025</span>
      </div>
      <div className="rounded-xl p-5 text-white" style={{ background: "var(--et-red)" }}>
        <p className="text-xs font-black uppercase tracking-widest opacity-80 mb-1">Your Tax This Year</p>
        <p className="text-4xl font-black mb-1">{formatINR(s.current_tax)}</p>
        <p className="text-sm opacity-90">{rec === "new" ? "New Regime" : "Old Regime"} · {s.effective_rate}% effective · {formatINR(s.monthly_tds_should_be)}/month TDS</p>
        {s.max_additional_saving_possible > 0 && <div className="mt-3 bg-white/20 rounded-lg px-3 py-2"><p className="text-sm font-bold">💡 Save {formatINR(s.max_additional_saving_possible)} more by optimising deductions</p></div>}
      </div>
      <div className="grid grid-cols-2 gap-3">
        {(["new", "old"] as const).map(r => { const d = tax[`${r}_regime`]; const isRec = r === rec; return (
          <div key={r} className="rounded-xl p-4 bg-white" style={{ border: `2px solid ${isRec ? "var(--et-red)" : "var(--et-border)"}` }}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-black uppercase" style={{ color: isRec ? "var(--et-red)" : "var(--et-text-muted)" }}>{r === "new" ? "New Regime" : "Old Regime"}</p>
              {isRec && <CheckCircle className="w-4 h-4" style={{ color: "var(--et-red)" }} />}
            </div>
            <p className="text-2xl font-black" style={{ color: "var(--et-text)" }}>{formatINR(d.total_tax)}</p>
            <p className="text-xs mt-1" style={{ color: "var(--et-text-muted)" }}>{d.effective_rate_pct}% · {formatINR(d.monthly_tax)}/mo · Taxable: {formatINR(d.taxable_income)}</p>
          </div>
        );})}
      </div>
      {hra && <HRACard hra={hra} />}
      {missed.length > 0 && <MissedCard missed={missed} />}
      {instruments.length > 0 && instruments[0].instrument !== "No deductions needed" && <InstrumentsCard instruments={instruments} />}
      {result.tax_steps_new && result.tax_steps_old && <TaxSteps newData={result.tax_steps_new} oldData={result.tax_steps_old} recommended={rec} />}
      <div className="rounded-xl px-3 py-2.5" style={{ background: "#f9f9f9", border: "1px solid var(--et-border)" }}>
        <p className="text-xs leading-relaxed" style={{ color: "var(--et-text-muted)" }}>📋 Indicative calculations based on Finance Act 2025. Consult a CA for tax filing. IT Helpline: 1800-103-0025</p>
      </div>
    </div>
  );
}

function HRACard({ hra }: any) {
  return <div className="bg-white rounded-xl overflow-hidden" style={{ border: "1px solid var(--et-border)" }}>
    <div className="px-4 py-2.5 border-b" style={{ background: "#fafafa", borderColor: "var(--et-border)" }}>
      <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-text-muted)" }}>HRA Exemption (Sec 10(13A))</p>
    </div>
    <div className="p-4 space-y-2">
      {[["① Actual HRA received", hra.limit1_actual_hra], ["② 50% of basic (metro)", hra.limit2_metro_pct], ["③ Rent paid − 10% basic", hra.limit3_rent_minus_10pct_basic]].map(([l, v]: any, i) => (
        <div key={i} className="flex justify-between text-sm"><span style={{ color: "var(--et-text)" }}>{l}</span><span className={`font-bold ${v === hra.hra_exempt ? "text-green-600" : ""}`}>{formatINR(v)}</span></div>
      ))}
      <div className="border-t pt-2 flex justify-between text-sm font-black" style={{ borderColor: "var(--et-border)" }}>
        <span style={{ color: "var(--et-red)" }}>HRA Exempt</span><span style={{ color: "var(--et-red)" }}>{formatINR(hra.hra_exempt)}</span>
      </div>
    </div>
  </div>;
}

function MissedCard({ missed }: any) {
  return <div className="bg-white rounded-xl overflow-hidden" style={{ border: "1px solid #fbbf24" }}>
    <div className="px-4 py-2.5 border-b flex items-center justify-between" style={{ background: "#fffbeb", borderColor: "#fbbf24" }}>
      <div className="flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-500" /><p className="text-xs font-black uppercase tracking-widest text-amber-700">Missed Deductions</p></div>
      <p className="text-xs font-bold text-amber-700">Save {formatINR(missed.reduce((s: number, d: any) => s + d.tax_saving_estimate, 0))} more</p>
    </div>
    <div className="divide-y" style={{ borderColor: "var(--et-border)" }}>
      {missed.map((d: any, i: number) => (
        <div key={i} className="px-4 py-3">
          <div className="flex justify-between items-start mb-1">
            <span className="text-xs font-bold" style={{ color: "var(--et-text)" }}>Sec {d.section} — {d.description}</span>
            <span className="text-xs font-bold text-green-600 shrink-0 ml-2">Save {formatINR(d.tax_saving_estimate)}</span>
          </div>
          <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>Gap: {formatINR(d.gap)} · Limit: {formatINR(d.max_allowed)}</p>
        </div>
      ))}
    </div>
  </div>;
}

function InstrumentsCard({ instruments }: any) {
  return <div className="bg-white rounded-xl overflow-hidden" style={{ border: "1px solid var(--et-border)" }}>
    <div className="px-4 py-2.5 border-b" style={{ background: "#fafafa", borderColor: "var(--et-border)" }}>
      <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-text-muted)" }}>Tax-Saving Instruments</p>
      <p className="text-xs mt-0.5" style={{ color: "var(--et-text-muted)" }}>Ranked by liquidity (high → low)</p>
    </div>
    <div className="divide-y" style={{ borderColor: "var(--et-border)" }}>
      {instruments.map((inst: any, i: number) => (
        <div key={i} className="px-4 py-3">
          <div className="flex items-start justify-between mb-1">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full text-white text-xs font-black flex items-center justify-center shrink-0" style={{ background: "var(--et-red)" }}>{inst.rank}</span>
              <p className="text-sm font-semibold" style={{ color: "var(--et-text)" }}>{inst.instrument}</p>
            </div>
            <span className="text-xs font-bold text-green-600 shrink-0 ml-2">Save {formatINR(inst.tax_saving)}</span>
          </div>
          <div className="pl-7 text-xs space-y-0.5">
            <p style={{ color: "var(--et-text-muted)" }}>{inst.why_ranked_here}</p>
            <p style={{ color: "var(--et-text-muted)" }}>Liquidity: <b>{inst.liquidity?.split("—")[0]}</b> · Risk: <b>{inst.risk}</b></p>
          </div>
        </div>
      ))}
    </div>
  </div>;
}
