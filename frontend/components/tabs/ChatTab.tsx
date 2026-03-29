"use client";
import { useState, useEffect, useRef } from "react";
import { Send, Loader2, BarChart2, X } from "lucide-react";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ImpactPanel } from "@/components/ImpactPanel";
import { CorpusChart } from "@/components/charts/CorpusChart";
import { TaxCompareChart } from "@/components/charts/TaxCompareChart";
import { GlidepathChart } from "@/components/charts/GlidepathChart";
import { LiteracyScore } from "@/components/LiteracyScore";
import { MonthlyRoadmap } from "@/components/MonthlyRoadmap";
import { GoalPlan } from "@/components/GoalPlan";
import { TaxSteps } from "@/components/TaxSteps";
import { SipByCategory } from "@/components/SipByCategory";
import { createSession, sendMessageStream } from "@/lib/api";

interface Message { role: "user" | "assistant"; content: string }

const SCENARIO_LABELS: Record<string, { label: string; color: string }> = {
  tax:        { label: "Tax Planning",        color: "bg-blue-50 text-blue-700 border-blue-200" },
  fire:       { label: "Retirement Planning", color: "bg-green-50 text-green-700 border-green-200" },
  life_event: { label: "Life Event Advisor",  color: "bg-purple-50 text-purple-700 border-purple-200" },
};

const STARTERS = [
  { icon: "💰", text: "I earn ₹15L/year. Help me save tax" },
  { icon: "🏖️", text: "Plan my retirement — I'm 30, earn ₹20L" },
  { icon: "🎁", text: "I got a ₹5L bonus. What should I do?" },
  { icon: "💍", text: "Getting married next year. Financial plan?" },
];

export function ChatTab() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [scenario, setScenario] = useState<string | null>(null);
  const [calculations, setCalculations] = useState<Record<string, any> | null>(null);
  const [showPanel, setShowPanel] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    createSession().then(setSessionId);
    setMessages([{
      role: "assistant",
      content: JSON.stringify({
        headline: "Your personal CA is here — free, instant, always available.",
        tone_opener: "I'm your AI Money Mentor on Economic Times. Ask me anything about tax planning, retirement, or what to do when life throws a financial curveball.",
        actions: [
          { priority: 1, action: "Tell me your income and I'll find your tax savings", impact: "Most users save ₹15,000–₹65,000/year", timeline: "Takes 2 minutes" },
          { priority: 2, action: "Share your age and goals for a retirement roadmap", impact: "Know exactly when you can retire", timeline: "Takes 3 minutes" },
          { priority: 3, action: "Mention a life event — bonus, marriage, baby", impact: "Get a personalised allocation plan", timeline: "Instant" },
        ],
      }),
    }]);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(text?: string) {
    const msg = text || input.trim();
    if (!msg || !sessionId || loading) return;
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "42px";
    setMessages(prev => [...prev, { role: "user", content: msg }]);
    setLoading(true);
    setStatusText("Thinking...");
    setMessages(prev => [...prev, { role: "assistant", content: "__streaming__" }]);
    let accumulated = "";

    try {
      await sendMessageStream(sessionId, msg, {
        onStatus: (s) => setStatusText(s),
        onToken: (token) => {
          accumulated += token;
          setMessages(prev => {
            const u = [...prev];
            const last = u[u.length - 1];
            if (last?.role === "assistant") u[u.length - 1] = { ...last, content: accumulated };
            return u;
          });
        },
        onPlan: (json) => {
          setMessages(prev => {
            const u = [...prev];
            const last = u[u.length - 1];
            if (last?.role === "assistant") u[u.length - 1] = { ...last, content: json };
            return u;
          });
        },
        onCalculations: (data) => { setCalculations(data); setShowPanel(true); },
        onDone: (sc) => { if (sc) setScenario(sc); setLoading(false); setStatusText(""); },
        onError: () => {
          setMessages(prev => {
            const u = [...prev];
            const last = u[u.length - 1];
            if (last?.role === "assistant") u[u.length - 1] = { ...last, content: "Something went wrong. Please try again." };
            return u;
          });
          setLoading(false); setStatusText("");
        },
      });
    } catch {
      setMessages(prev => {
        const u = [...prev];
        const last = u[u.length - 1];
        if (last?.role === "assistant") u[u.length - 1] = { ...last, content: "Something went wrong. Please try again." };
        return u;
      });
      setLoading(false); setStatusText("");
    }
  }

  const corpusData = calculations?.fire?.corpus_projection;
  const taxData = calculations?.tax_comparison;
  const scenarioMeta = scenario ? SCENARIO_LABELS[scenario] : null;

  const SideContent = () => (
    <div className="p-4 space-y-3">
      <ImpactPanel calculations={calculations} />
      {taxData && <TaxCompareChart data={taxData} />}
      {calculations?.tax_steps_new && calculations?.tax_steps_old && (
        <TaxSteps newData={calculations.tax_steps_new} oldData={calculations.tax_steps_old} recommended={taxData?.recommended_regime || "new"} />
      )}
      {calculations?.sip_by_category && <SipByCategory data={calculations.sip_by_category} totalSip={calculations?.fire?.monthly_sip_needed || 0} />}
      {calculations?.goal_plan && <GoalPlan data={calculations.goal_plan} />}
      {calculations?.glidepath && <GlidepathChart data={calculations.glidepath} />}
      {calculations?.monthly_roadmap && <MonthlyRoadmap data={calculations.monthly_roadmap} />}
      {corpusData && <CorpusChart data={corpusData} />}
      {calculations?.literacy_score && <LiteracyScore data={calculations.literacy_score} />}
    </div>
  );

  return (
    <div className="h-full flex overflow-hidden">
      {/* Chat */}
      <main className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Scenario badge */}
        {scenarioMeta && (
          <div className="px-4 pt-2 shrink-0">
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border et-sans ${scenarioMeta.color}`}>
              {scenarioMeta.label}
            </span>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-3 sm:px-5 py-4">
          {messages.map((m, i) => <MessageBubble key={i} role={m.role} content={m.content} />)}
          {loading && (
            <div className="flex items-start gap-2 mb-4">
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-black shrink-0"
                style={{ background: "var(--et-red)", fontFamily: "Georgia, serif" }}>ET</div>
              <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm" style={{ border: "1px solid var(--et-border)" }}>
                <div className="flex items-center gap-2 text-sm et-sans" style={{ color: "var(--et-text-muted)" }}>
                  <Loader2 className="w-4 h-4 animate-spin" style={{ color: "var(--et-red)" }} />
                  {statusText || "Crunching your numbers..."}
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Quick starters */}
        {messages.length <= 1 && (
          <div className="px-3 sm:px-5 pb-3 shrink-0">
            <p className="text-xs font-black uppercase tracking-widest mb-2 et-sans" style={{ color: "var(--et-text-muted)" }}>Quick Start</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {STARTERS.map(s => (
                <button key={s.text} type="button" onClick={() => handleSend(s.text)}
                  className="flex items-center gap-2 text-left text-xs bg-white rounded-lg px-3 py-2.5 transition-all et-sans cursor-pointer"
                  style={{ border: "1px solid var(--et-border)" }}
                  onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = "var(--et-red)"; (e.currentTarget as HTMLElement).style.background = "#fff0f1"; }}
                  onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = "var(--et-border)"; (e.currentTarget as HTMLElement).style.background = "white"; }}>
                  <span className="text-base shrink-0">{s.icon}</span>
                  <span style={{ color: "var(--et-text)" }}>{s.text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="shrink-0 bg-white px-3 sm:px-5 py-3" style={{ borderTop: "1px solid var(--et-border)" }}>
          <div className="flex gap-2 items-end">
            <textarea ref={textareaRef} value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              onInput={e => { const el = e.currentTarget; el.style.height = "42px"; el.style.height = Math.min(el.scrollHeight, 120) + "px"; }}
              placeholder="Ask about tax, retirement, investments..."
              rows={1}
              className="flex-1 rounded-lg px-4 py-2.5 text-sm focus:outline-none resize-none et-sans"
              style={{ minHeight: "42px", maxHeight: "120px", border: "1px solid var(--et-border)" }}
            />
            <button type="button" onClick={() => handleSend()} disabled={loading || !input.trim()}
              className="rounded-lg px-4 py-2.5 text-white shrink-0 et-sans"
              style={{ background: "var(--et-red)", opacity: loading || !input.trim() ? 0.4 : 1, cursor: loading || !input.trim() ? "not-allowed" : "pointer" }}>
              <Send className="w-4 h-4" />
            </button>
          </div>
          <div className="flex items-center justify-between mt-1">
            <p className="text-xs et-sans" style={{ color: "var(--et-text-muted)" }}>Enter to send · Shift+Enter for new line</p>
            {calculations && (
              <button onClick={() => setShowPanel(p => !p)} className="lg:hidden flex items-center gap-1 text-xs font-semibold et-sans" style={{ color: "var(--et-red)" }}>
                <BarChart2 className="w-3.5 h-3.5" /> Your Numbers
              </button>
            )}
          </div>
        </div>
      </main>

      {/* Desktop side panel */}
      {calculations && (
        <aside className="hidden lg:flex flex-col w-72 xl:w-80 shrink-0 overflow-y-auto bg-white" style={{ borderLeft: "1px solid var(--et-border)" }}>
          <div className="px-4 py-3 shrink-0 flex items-center justify-between" style={{ borderBottom: "1px solid var(--et-border)" }}>
            <p className="text-xs font-black uppercase tracking-widest et-sans" style={{ color: "var(--et-red)" }}>Your Numbers</p>
          </div>
          <div className="flex-1 overflow-y-auto"><SideContent /></div>
        </aside>
      )}

      {/* Mobile overlay */}
      {showPanel && calculations && (
        <div className="lg:hidden fixed inset-0 z-30 flex">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowPanel(false)} />
          <div className="relative ml-auto w-80 max-w-full h-full bg-white overflow-y-auto flex flex-col" style={{ borderLeft: "1px solid var(--et-border)" }}>
            <div className="flex items-center justify-between px-4 py-3 shrink-0" style={{ borderBottom: "1px solid var(--et-border)" }}>
              <p className="text-xs font-black uppercase tracking-widest et-sans" style={{ color: "var(--et-red)" }}>Your Numbers</p>
              <button onClick={() => setShowPanel(false)}><X className="w-4 h-4" style={{ color: "var(--et-text-muted)" }} /></button>
            </div>
            <div className="flex-1 overflow-y-auto"><SideContent /></div>
          </div>
        </div>
      )}
    </div>
  );
}
