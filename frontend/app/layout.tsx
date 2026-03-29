import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Money Mentor — Economic Times",
  description: "AI-powered personal finance mentor for every Indian. Tax planning, retirement, life events.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
