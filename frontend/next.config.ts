import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow the backend URL to be set via environment variable
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
  // For Vercel deployment — no need to export static
  output: undefined,
};

export default nextConfig;
