"use client";
import { cn } from "@/lib/utils";

const LABELS: Record<string, { label: string; color: string }> = {
  tax: { label: "Tax Wizard", color: "bg-blue-100 text-blue-700" },
  fire: { label: "FIRE Planner", color: "bg-green-100 text-green-700" },
  life_event: { label: "Life Event Advisor", color: "bg-purple-100 text-purple-700" },
};

export function ScenarioBadge({ scenario }: { scenario: string | null }) {
  if (!scenario || !LABELS[scenario]) return null;
  const { label, color } = LABELS[scenario];
  return (
    <span className={cn("text-xs font-medium px-2 py-1 rounded-full", color)}>
      {label}
    </span>
  );
}
