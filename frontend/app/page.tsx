"use client";
import { useState } from "react";
import { ChatTab } from "@/components/tabs/ChatTab";
import { TaxWizardTab } from "@/components/tabs/TaxWizardTab";
import { LifeEventsTab } from "@/components/tabs/LifeEventsTab";

type Tab = "chat" | "tax" | "life";

const TABS: { id: Tab; label: string; icon: string; desc: string }[] = [
  { id: "chat",  icon: "💬", label: "AI Advisor",    desc: "Ask anything" },
  { id: "tax",   icon: "🧮", label: "Tax Wizard",    desc: "FY 2025-26" },
  { id: "life",  icon: "🎯", label: "Life Events",   desc: "Bonus, marriage…" },
];

export default function Home() {
  const [tab, setTab] = useState<Tab>("chat");

  return (
    <div className="h-screen flex flex-col overflow-hidden et-sans" style={{ background: "var(--et-gray-bg)" }}>

      {/* ── ET Header ─────────────────────────────────────────────────────── */}
      <header className="bg-white shrink-0" style={{ borderBottom: "2px solid var(--et-red)" }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6">

          {/* Brand row */}
          <div className="flex items-center justify-between py-2.5">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded flex items-center justify-center text-white font-black text-base shrink-0"
                style={{ background: "var(--et-red)", fontFamily: "Georgia, serif" }}>
                ET
              </div>
              <div>
                <p className="text-sm font-black leading-tight" style={{ color: "var(--et-red)", fontFamily: "Georgia, serif" }}>
                  Economic Times
                </p>
                <p className="text-xs leading-tight" style={{ color: "var(--et-text-muted)" }}>
                  AI Money Mentor · FY 2025-26
                </p>
              </div>
            </div>

            {/* Desktop tab pills */}
            <nav className="hidden sm:flex items-center gap-1 bg-gray-100 rounded-xl p-1">
              {TABS.map(t => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                  style={{
                    background: tab === t.id ? "var(--et-red)" : "transparent",
                    color: tab === t.id ? "white" : "var(--et-text-muted)",
                  }}
                >
                  <span>{t.icon}</span>
                  <span>{t.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Mobile tab bar */}
          <div className="sm:hidden flex border-t" style={{ borderColor: "var(--et-border)" }}>
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className="flex-1 flex flex-col items-center py-2 text-xs font-semibold transition-colors"
                style={{
                  color: tab === t.id ? "var(--et-red)" : "var(--et-text-muted)",
                  borderBottom: tab === t.id ? "2px solid var(--et-red)" : "2px solid transparent",
                }}
              >
                <span className="text-base">{t.icon}</span>
                <span>{t.label}</span>
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* ── Tab content ───────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-hidden">
        <div className={tab === "chat" ? "h-full" : "hidden"}>
          <ChatTab />
        </div>
        <div className={tab === "tax" ? "h-full overflow-y-auto" : "hidden"}>
          <TaxWizardTab />
        </div>
        <div className={tab === "life" ? "h-full overflow-y-auto" : "hidden"}>
          <LifeEventsTab />
        </div>
      </div>
    </div>
  );
}
