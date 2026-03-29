"use client";

interface Dimension {
  score: number;
  max: number;
}

interface LiteracyData {
  before: number;
  after: number;
  improvement: number;
  level: string;
  next_milestone: string;
  dimensions: {
    tax_awareness: Dimension;
    investment_basics: Dimension;
    insurance: Dimension;
    emergency_fund: Dimension;
    goal_planning: Dimension;
  };
}

const DIM_LABELS: Record<string, string> = {
  tax_awareness:     "Tax Awareness",
  investment_basics: "Investments",
  insurance:         "Insurance",
  emergency_fund:    "Emergency Fund",
  goal_planning:     "Goal Planning",
};

export function LiteracyScore({ data }: { data: LiteracyData }) {
  if (!data) return null;

  return (
    <div className="rounded-lg overflow-hidden et-sans" style={{ border: "1px solid var(--et-border)" }}>
      <div className="px-3 py-2 border-b flex items-center justify-between"
        style={{ background: "#fff0f1", borderColor: "#fde8e8" }}>
        <p className="text-xs font-black uppercase tracking-widest" style={{ color: "var(--et-red)" }}>
          Financial Literacy Score
        </p>
        {data.improvement > 0 && (
          <span className="text-xs font-bold text-green-600">+{data.improvement} pts today</span>
        )}
      </div>

      <div className="bg-white px-3 py-3 space-y-3">
        {/* Before / After */}
        <div className="space-y-2">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span style={{ color: "var(--et-text-muted)" }}>Before this session</span>
              <span className="font-bold" style={{ color: "var(--et-text-muted)" }}>{data.before}/100</span>
            </div>
            <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
              <div className="h-full rounded-full bg-gray-300 transition-all"
                style={{ width: `${data.before}%` }} />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span style={{ color: "var(--et-text-muted)" }}>After this session</span>
              <span className="font-bold" style={{ color: "var(--et-red)" }}>{data.after}/100</span>
            </div>
            <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
              <div className="h-full rounded-full transition-all"
                style={{ width: `${data.after}%`, background: "var(--et-red)" }} />
            </div>
          </div>
          {data.improvement > 0 && (
            <p className="text-xs font-semibold text-green-600">
              ↑ +{data.improvement} points gained this session
            </p>
          )}
        </div>

        {/* Level badge */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold px-2 py-1 rounded-full"
            style={{ background: "#fff0f1", color: "var(--et-red)" }}>
            {data.level}
          </span>
        </div>

        {/* Dimensions */}
        <div className="space-y-1.5">
          {Object.entries(data.dimensions).map(([key, dim]) => (
            <div key={key}>
              <div className="flex justify-between text-xs mb-0.5">
                <span style={{ color: "var(--et-text-muted)" }}>{DIM_LABELS[key]}</span>
                <span className="font-semibold" style={{ color: "var(--et-text)" }}>{dim.score}/{dim.max}</span>
              </div>
              <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
                <div className="h-full rounded-full transition-all"
                  style={{ width: `${(dim.score / dim.max) * 100}%`, background: "var(--et-red)", opacity: 0.7 }} />
              </div>
            </div>
          ))}
        </div>

        {/* Next milestone */}
        <p className="text-xs leading-relaxed rounded-lg px-2 py-2"
          style={{ background: "#f9f9f9", color: "var(--et-text-muted)", border: "1px solid var(--et-border)" }}>
          🎯 {data.next_milestone}
        </p>
      </div>
    </div>
  );
}
