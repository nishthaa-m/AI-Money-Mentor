"use client";
import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, ChevronRight, AlertTriangle, CheckCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { TaxSteps } from "@/components/TaxSteps";
import { formatINR } from "@/lib/utils";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SalaryForm {
  annual_income: string;
  basic_salary: string;
  hra_received: string;
  rent_paid: string;
  metro_city: boolean;
  section_80c_invested: string;
  section_80d_self: string;
  section_80d_parents: string;
  section_80ccd1b: string;
  home_loan_interest: string;
  lta: string;
  other_deductions: string;
  age: string;
  tds_deducted: string;
}

const EMPTY_FORM: SalaryForm = {
  annual_income: "", basic_salary: "", hra_received: "", rent_paid: "",
  metro_city: true, section_80c_invested: "", section_80d_self: "",
  section_80d_parents: "", section_80ccd1b: "", home_loan_interest: "",
  lta: "", other_deductions: "", age: "", tds_deducted: "",
};

export default function TaxWizard() {
  const [mode, setMode] = useState<"landing" | "upload" | "manual" | "result">("landing");
  const [form, setForm] = useState<SalaryForm>(EMPTY_FORM);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [uploadedFile, setUploadedFile] = useState<string>("");

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    setLoading(true);
    setError("");
    setUploadedFile(file.name);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API}/tax/upload-form16`, { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      // Pre-fill form with extracted data
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
      setMode("manual"); // show form pre-filled for review
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { "application/pdf": [".pdf"] }, maxFiles: 1,
  });

  async function analyze() {
    setLoading(true);
    setError("");
    try {
      const payload = Object.fromEntries(
        Object.entries(form).map(([k, v]) => [k, k === "metro_city" ? v : (v === "" ? 0 : Number(v))])
      );
      const res = await fetch(`${API}/tax/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed");
      setResult(data);
      setMode("result");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen et-sans" style={{ background: "var(--et-gray-bg)" }}>
      {/* Header */}
      <header className="bg-white shadow-sm" style={{ borderBottom: "2px solid var(--et-red)" }}>
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-3">
          <Link href="/" className="flex items-center gap-1.5 text-xs hover:underline" style={{ color: "var(--et-text-muted)" }}>
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Chat
          </Link>
          <div className="w-px h-4 bg-gray-200" />
          <div className="w-7 h-7 rounded flex items-center justify-center text-white font-black text-sm"
            style={{ background: "var(--et-red)", fontFamily: "Georgia, serif" }}>ET</div>
          <div>
            <p className="text-sm font-black" style={{ color: "var(--et-red)", fontFamily: "Georgia, serif" }}>Tax Wizard</p>
            <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>FY 2025-26 · Old vs New Regime · Step-by-step</p>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* Landing */}
        {mode === "landing" && (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-black mb-2" style={{ color: "var(--et-text)", fontFamily: "Georgia, serif" }}>
                Find every rupee you're overpaying in tax
              </h1>
              <p className="text-sm" style={{ color: "var(--et-text-muted)" }}>
                Upload your Form 16 or enter your salary structure. We'll calculate exact tax under both regimes and find every deduction you're missing.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button onClick={() => setMode("upload")}
                className="bg-white rounded-xl p-6 text-left hover:shadow-md transition-shadow"
                style={{ border: "2px solid var(--et-red)" }}>
                <Upload className="w-8 h-8 mb-3" style={{ color: "var(--et-red)" }} />
                <p className="font-black text-base mb-1" style={{ color: "var(--et-text)" }}>Upload Form 16</p>
                <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>
                  PDF from your employer. We extract salary, TDS, and deductions automatically.
                </p>
                <span className="inline-block mt-3 text-xs font-bold px-2 py-1 rounded-full" style={{ background: "#fff0f1", color: "var(--et-red)" }}>
                  Fastest
                </span>
              </button>

              <button onClick={() => setMode("manual")}
                className="bg-white rounded-xl p-6 text-left hover:shadow-md transition-shadow"
                style={{ border: "1px solid var(--et-border)" }}>
                <FileText className="w-8 h-8 mb-3" style={{ color: "var(--et-text-muted)" }} />
                <p className="font-black text-base mb-1" style={{ color: "var(--et-text)" }}>Enter Manually</p>
                <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>
                  Know your salary structure? Enter income, HRA, deductions directly.
                </p>
                <span className="inline-block mt-3 text-xs font-bold px-2 py-1 rounded-full bg-gray-100 text-gray-600">
                  Full control
                </span>
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
              {loading ? (
                <p className="text-sm font-semibold" style={{ color: "var(--et-red)" }}>Extracting data from Form 16...</p>
              ) : uploadedFile ? (
                <div>
                  <p className="text-sm font-semibold text-green-600">✓ {uploadedFile} uploaded</p>
                  <p className="text-xs mt-1" style={{ color: "var(--et-text-muted)" }}>Review the pre-filled form below</p>
                </div>
              ) : (
                <>
                  <p className="text-sm font-semibold" style={{ color: "var(--et-text)" }}>
                    {isDragActive ? "Drop your Form 16 here" : "Drag & drop your Form 16 PDF"}
                  </p>
                  <p className="text-xs mt-1" style={{ color: "var(--et-text-muted)" }}>or click to browse · PDF only · max 10MB</p>
                </>
              )}
            </div>
            {error && <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}
            <p className="text-xs text-center" style={{ color: "var(--et-text-muted)" }}>
              🔒 Your PDF is processed locally and never stored. PAN is masked in all outputs.
            </p>
            <button onClick={() => setMode("manual")} className="w-full text-xs text-center hover:underline" style={{ color: "var(--et-text-muted)" }}>
              Don't have Form 16? Enter manually →
            </button>
          </div>
        )}

        {/* Manual Input Form */}
        {mode === "manual" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <button onClick={() => setMode("landing")} className="text-xs flex items-center gap-1 hover:underline" style={{ color: "var(--et-text-muted)" }}>
                <ArrowLeft className="w-3 h-3" /> Back
              </button>
              {uploadedFile && (
                <span className="text-xs text-green-600 font-semibold">✓ Pre-filled from {uploadedFile}</span>
              )}
            </div>

            <div className="bg-white rounded-xl overflow-hidden" style={{ border: "1px solid var(--et-border)" }}>
              <SectionHeader title="Income Details" />
              <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Gross Annual Income *" name="annual_income" form={form} setForm={setForm} hint="Total CTC / gross salary" />
                <Field label="Age" name="age" form={form} setForm={setForm} hint="For senior citizen limits" />
                <Field label="Basic Salary (annual)" name="basic_salary" form={form} setForm={setForm} hint="~40% of CTC typically" />
                <Field label="TDS Already Deducted" name="tds_deducted" form={form} setForm={setForm} hint="From Form 16 / payslips" />
              </div>

              <SectionHeader title="HRA (House Rent Allowance)" />
              <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="HRA Received (annual)" name="hra_received" form={form} setForm={setForm} hint="From salary slip" />
                <Field label="Rent Paid (annual)" name="rent_paid" form={form} setForm={setForm} hint="Actual rent paid" />
                <div className="flex items-center gap-2 col-span-full">
                  <input type="checkbox" id="metro" checked={form.metro_city}
                    onChange={e => setForm(f => ({ ...f, metro_city: e.target.checked }))}
                    className="w-4 h-4 accent-red-600" />
                  <label htmlFor="metro" className="text-sm" style={{ color: "var(--et-text)" }}>
                    Metro city (Mumbai, Delhi, Kolkata, Chennai) — 50% basic HRA limit
                  </label>
                </div>
              </div>

              <SectionHeader title="Deductions (Old Regime)" />
              <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Sec 80C invested" name="section_80c_invested" form={form} setForm={setForm} hint="ELSS, PPF, LIC, EPF — max ₹1.5L" />
                <Field label="Sec 80CCD(1B) — NPS" name="section_80ccd1b" form={form} setForm={setForm} hint="Extra NPS over 80C — max ₹50K" />
                <Field label="Sec 80D — Health Insurance (self)" name="section_80d_self" form={form} setForm={setForm} hint="Max ₹25K (₹50K if senior)" />
                <Field label="Sec 80D — Health Insurance (parents)" name="section_80d_parents" form={form} setForm={setForm} hint="Max ₹25K (₹50K senior parents)" />
                <Field label="Sec 24(b) — Home Loan Interest" name="home_loan_interest" form={form} setForm={setForm} hint="Max ₹2L (self-occupied)" />
                <Field label="LTA (Leave Travel Allowance)" name="lta" form={form} setForm={setForm} hint="Actual travel bills" />
                <Field label="Other deductions" name="other_deductions" form={form} setForm={setForm} hint="80E, 80G, 80TTA etc." />
              </div>
            </div>

            {error && <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}

            <button onClick={analyze} disabled={loading || !form.annual_income}
              className="w-full py-3 rounded-xl text-white font-black text-sm transition-opacity disabled:opacity-40"
              style={{ background: "var(--et-red)" }}>
              {loading ? "Calculating..." : "Calculate My Tax →"}
            </button>
          </div>
        )}

        {/* Results */}
        {mode === "result" && result && (
          <TaxWizardResult result={result} onBack={() => setMode("manual")} />
        )}
      </div>
    </div>
  );
}

function SectionHeader({ title }: { title: string }) {
  return (
    <div className="px-4 py-2.5 border-b" style={{ background: "#fafafa", borderColor: "var(--et-border)" }}>
      <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-text-muted)" }}>{title}</p>
    </div>
  );
}

function Field({ label, name, form, setForm, hint }: {
  label: string; name: keyof SalaryForm; form: SalaryForm;
  setForm: React.Dispatch<React.SetStateAction<SalaryForm>>; hint?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-semibold mb-1" style={{ color: "var(--et-text)" }}>{label}</label>
      <input
        type="number"
        value={form[name] as string}
        onChange={e => setForm(f => ({ ...f, [name]: e.target.value }))}
        placeholder="0"
        className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none"
        style={{ borderColor: "var(--et-border)" }}
      />
      {hint && <p className="text-xs mt-0.5" style={{ color: "var(--et-text-muted)" }}>{hint}</p>}
    </div>
  );
}

function TaxWizardResult({ result, onBack }: { result: any; onBack: () => void }) {
  const s = result.summary;
  const tax = result.tax_comparison;
  const missed = result.missed_deductions || [];
  const instruments = result.tax_instruments || [];
  const hra = result.hra_calculation;
  const rec = s.recommended_regime;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="text-xs flex items-center gap-1 hover:underline" style={{ color: "var(--et-text-muted)" }}>
          <ArrowLeft className="w-3 h-3" /> Edit inputs
        </button>
        <span className="text-xs" style={{ color: "var(--et-text-muted)" }}>FY 2025-26 · Finance Act 2025</span>
      </div>

      {/* Hero summary */}
      <div className="rounded-xl p-5 text-white" style={{ background: "var(--et-red)" }}>
        <p className="text-xs font-black uppercase tracking-widest opacity-80 mb-1">Your Tax This Year</p>
        <p className="text-4xl font-black mb-1">{formatINR(s.current_tax)}</p>
        <p className="text-sm opacity-90">
          {rec === "new" ? "New Tax Regime" : "Old Tax Regime"} · {s.effective_rate}% effective rate · {formatINR(s.monthly_tds_should_be)}/month TDS
        </p>
        {s.max_additional_saving_possible > 0 && (
          <div className="mt-3 bg-white/20 rounded-lg px-3 py-2">
            <p className="text-sm font-bold">💡 You can save {formatINR(s.max_additional_saving_possible)} more by optimising deductions</p>
          </div>
        )}
      </div>

      {/* Regime comparison cards */}
      <div className="grid grid-cols-2 gap-3">
        {(["new", "old"] as const).map(r => {
          const d = tax[`${r}_regime`];
          const isRec = r === rec;
          return (
            <div key={r} className="rounded-xl p-4 bg-white" style={{ border: `2px solid ${isRec ? "var(--et-red)" : "var(--et-border)"}` }}>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-black uppercase" style={{ color: isRec ? "var(--et-red)" : "var(--et-text-muted)" }}>
                  {r === "new" ? "New Regime" : "Old Regime"}
                </p>
                {isRec && <CheckCircle className="w-4 h-4" style={{ color: "var(--et-red)" }} />}
              </div>
              <p className="text-2xl font-black" style={{ color: "var(--et-text)" }}>{formatINR(d.total_tax)}</p>
              <p className="text-xs mt-1" style={{ color: "var(--et-text-muted)" }}>{d.effective_rate_pct}% effective · {formatINR(d.monthly_tax)}/mo</p>
              <p className="text-xs mt-1" style={{ color: "var(--et-text-muted)" }}>Taxable: {formatINR(d.taxable_income)}</p>
            </div>
          );
        })}
      </div>

      {/* TDS gap */}
      {s.tds_deducted > 0 && (
        <div className={`rounded-xl px-4 py-3 flex items-center justify-between ${s.tds_gap < 0 ? "bg-red-50" : "bg-green-50"}`}
          style={{ border: `1px solid ${s.tds_gap < 0 ? "#fecdd3" : "#86efac"}` }}>
          <div>
            <p className="text-xs font-bold" style={{ color: s.tds_gap < 0 ? "var(--et-red)" : "#16a34a" }}>
              {s.tds_gap < 0 ? "⚠️ TDS Shortfall — you may owe tax" : "✓ TDS is sufficient"}
            </p>
            <p className="text-xs mt-0.5" style={{ color: "var(--et-text-muted)" }}>
              TDS deducted: {formatINR(s.tds_deducted)} · Tax liability: {formatINR(s.current_tax)}
            </p>
          </div>
          <p className="text-sm font-black" style={{ color: s.tds_gap < 0 ? "var(--et-red)" : "#16a34a" }}>
            {s.tds_gap < 0 ? `Pay ₹${formatINR(Math.abs(s.tds_gap))}` : `Refund ~${formatINR(s.tds_gap)}`}
          </p>
        </div>
      )}

      {/* HRA calculation */}
      {hra && (
        <div className="bg-white rounded-xl overflow-hidden" style={{ border: "1px solid var(--et-border)" }}>
          <div className="px-4 py-2.5 border-b" style={{ background: "#fafafa", borderColor: "var(--et-border)" }}>
            <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-text-muted)" }}>HRA Exemption Calculation (Sec 10(13A))</p>
          </div>
          <div className="p-4 space-y-2">
            <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>Exempt = minimum of:</p>
            {[
              { label: "① Actual HRA received", value: hra.limit1_actual_hra },
              { label: "② 50% of basic (metro)", value: hra.limit2_metro_pct },
              { label: "③ Rent paid − 10% of basic", value: hra.limit3_rent_minus_10pct_basic },
            ].map((row, i) => (
              <div key={i} className="flex justify-between text-sm">
                <span style={{ color: "var(--et-text)" }}>{row.label}</span>
                <span className={`font-bold ${row.value === hra.hra_exempt ? "text-green-600" : ""}`}>{formatINR(row.value)}</span>
              </div>
            ))}
            <div className="border-t pt-2 flex justify-between text-sm font-black" style={{ borderColor: "var(--et-border)" }}>
              <span style={{ color: "var(--et-red)" }}>HRA Exempt</span>
              <span style={{ color: "var(--et-red)" }}>{formatINR(hra.hra_exempt)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Missed deductions */}
      {missed.length > 0 && (
        <div className="bg-white rounded-xl overflow-hidden" style={{ border: "1px solid #fbbf24" }}>
          <div className="px-4 py-2.5 border-b flex items-center justify-between" style={{ background: "#fffbeb", borderColor: "#fbbf24" }}>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <p className="text-xs font-black uppercase tracking-widest text-amber-700">Missed Deductions</p>
            </div>
            <p className="text-xs font-bold text-amber-700">
              Save {formatINR(missed.reduce((s: number, d: any) => s + d.tax_saving_estimate, 0))} more
            </p>
          </div>
          <div className="divide-y" style={{ borderColor: "var(--et-border)" }}>
            {missed.map((d: any, i: number) => (
              <div key={i} className="px-4 py-3">
                <div className="flex justify-between items-start mb-1">
                  <div>
                    <span className="text-xs font-bold" style={{ color: "var(--et-text)" }}>Sec {d.section}</span>
                    <span className="text-xs ml-1" style={{ color: "var(--et-text-muted)" }}>— {d.description}</span>
                  </div>
                  <span className="text-xs font-bold text-green-600 shrink-0 ml-2">Save {formatINR(d.tax_saving_estimate)}</span>
                </div>
                <div className="flex gap-4 text-xs" style={{ color: "var(--et-text-muted)" }}>
                  <span>Invested: {formatINR(d.current || 0)}</span>
                  <span>Limit: {formatINR(d.max_allowed)}</span>
                  <span className="font-semibold" style={{ color: "var(--et-red)" }}>Gap: {formatINR(d.gap)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tax-saving instruments */}
      {instruments.length > 0 && instruments[0].instrument !== "No deductions needed" && (
        <div className="bg-white rounded-xl overflow-hidden" style={{ border: "1px solid var(--et-border)" }}>
          <div className="px-4 py-2.5 border-b" style={{ background: "#fafafa", borderColor: "var(--et-border)" }}>
            <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-text-muted)" }}>
              Recommended Tax-Saving Instruments
            </p>
            <p className="text-xs mt-0.5" style={{ color: "var(--et-text-muted)" }}>Ranked by liquidity (high → low)</p>
          </div>
          <div className="divide-y" style={{ borderColor: "var(--et-border)" }}>
            {instruments.map((inst: any, i: number) => (
              <div key={i} className="px-4 py-3">
                <div className="flex items-start justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full text-white text-xs font-black flex items-center justify-center shrink-0"
                      style={{ background: "var(--et-red)" }}>{inst.rank}</span>
                    <p className="text-sm font-semibold" style={{ color: "var(--et-text)" }}>{inst.instrument}</p>
                  </div>
                  <span className="text-xs font-bold text-green-600 shrink-0 ml-2">Save {formatINR(inst.tax_saving)}</span>
                </div>
                <div className="pl-7 space-y-0.5">
                  <p className="text-xs" style={{ color: "var(--et-text-muted)" }}>{inst.why_ranked_here}</p>
                  <div className="flex gap-4 text-xs">
                    <span>Liquidity: <span className="font-semibold" style={{ color: "var(--et-text)" }}>{inst.liquidity?.split("—")[0]}</span></span>
                    <span>Risk: <span className="font-semibold" style={{ color: "var(--et-text)" }}>{inst.risk}</span></span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step-by-step */}
      {result.tax_steps_new && result.tax_steps_old && (
        <TaxSteps
          newData={result.tax_steps_new}
          oldData={result.tax_steps_old}
          recommended={rec}
        />
      )}

      {/* SEBI disclaimer */}
      <div className="rounded-xl px-3 py-2.5" style={{ background: "#f9f9f9", border: "1px solid var(--et-border)" }}>
        <p className="text-xs leading-relaxed" style={{ color: "var(--et-text-muted)" }}>
          📋 Tax calculations are based on Finance Act 2025 (FY 2025-26) and are indicative. Actual liability depends on your complete income details. Consult a Chartered Accountant for tax filing.
          Income Tax Helpline: 1800-103-0025 · <a href="https://incometaxindia.gov.in" target="_blank" rel="noopener noreferrer" style={{ color: "var(--et-red)" }}>incometaxindia.gov.in</a>
        </p>
      </div>
    </div>
  );
}
