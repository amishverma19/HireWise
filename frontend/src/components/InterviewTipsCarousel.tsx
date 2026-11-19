"use client";

import React, { useEffect, useState } from "react";
import { Sparkles, ChevronLeft, ChevronRight } from "lucide-react";
import { useResumeStore } from "@/store/useResumeStore";

const PRO_TIPS = [
  {
    category: "Amazon & Google STAR Strategy",
    headline: "Always Establish a Baseline Metric First",
    content: "Before describing your solution, state the raw initial problem with a metric: 'Our p99 latency was 480ms causing a 4% user drop-off...'. This makes your result 10x more convincing to senior bar raisers."
  },
  {
    category: "System Design Calibration",
    headline: "Articulate Explicit Technical Trade-Offs",
    content: "Senior interviewers look for technical rationale: Why did you pick pgvector HNSW over IVFFlat? (HNSW gives 98% recall at the cost of higher RAM usage). Explaining trade-offs proves architectural maturity."
  },
  {
    category: "Senior Technical Ownership",
    headline: "Distinguish 'I' from 'We' in Key Achievements",
    content: "Never say 'We built a microservice'. Say: 'I architected the asynchronous message routing and decoupled workers, while the team contributed feature modules.' Interviewers hire you, not your team."
  },
  {
    category: "Telemetry & Quantified Impact",
    headline: "Swap Vague Adjectives for Concrete Telemetry",
    content: "Replace 'massively optimized database performance' with 'reduced B-tree index scan latency from 180ms to 24ms'. Exact numbers build instant technical credibility with hiring committees."
  },
  {
    category: "Behavioral Conflict Resolution",
    headline: "Anchor Disagreements in Data & Benchmarks",
    content: "When asked about a technical disagreement with a peer, highlight how you ran load tests or prototype benchmarks to compare data rather than arguing subjective opinions."
  }
];

export function InterviewTipsCarousel() {
  const [currentIdx, setCurrentIdx] = useState(0);
  const isHydrating = useResumeStore((s) => s.isHydrating);
  const currentStepMessage = useResumeStore((s) => s.currentStepMessage);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIdx((prev) => (prev + 1) % PRO_TIPS.length);
    }, 4500);
    return () => clearInterval(timer);
  }, []);

  const tip = PRO_TIPS[currentIdx];

  return (
    <div className="relative rounded-2xl border border-[#D49A9A]/35 bg-white p-5 shadow-xs overflow-hidden transition-all duration-300">
      <style>{`
        @keyframes tipProgress {
          from { width: 0%; }
          to { width: 100%; }
        }
      `}</style>

      {/* Top Header: Live Status & Controls */}
      <div className="flex items-center justify-between gap-4 mb-3 pb-3 border-b border-slate-100">
        {/* Status indicator on the left */}
        <div className="flex items-center gap-2 min-w-0">
          {isHydrating ? (
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2 shrink-0">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#7C0E44] opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#7C0E44]" />
              </span>
              <span className="text-xs font-semibold text-[#7C0E44]">
                Analyzing in Background
              </span>
              <span className="text-slate-300">•</span>
              <span className="text-xs text-slate-500 font-normal truncate max-w-xs sm:max-w-md">
                {currentStepMessage || "Optimizing ATS alignment and STAR bullets..."}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[#7C0E44]">
              <Sparkles className="w-3.5 h-3.5 text-[#AA5E7A]" />
              <span>Senior Interview Strategy</span>
            </div>
          )}
        </div>

        {/* Tip Navigation & Counter */}
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[11px] text-slate-400 font-medium">
            Tip {currentIdx + 1} of {PRO_TIPS.length}
          </span>
          <div className="flex items-center gap-0.5">
            <button
              type="button"
              onClick={() => setCurrentIdx((prev) => (prev - 1 + PRO_TIPS.length) % PRO_TIPS.length)}
              className="w-6 h-6 rounded flex items-center justify-center text-slate-400 hover:text-[#7C0E44] hover:bg-[#FAF4F0] transition-colors"
              title="Previous tip"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={() => setCurrentIdx((prev) => (prev + 1) % PRO_TIPS.length)}
              className="w-6 h-6 rounded flex items-center justify-center text-slate-400 hover:text-[#7C0E44] hover:bg-[#FAF4F0] transition-colors"
              title="Next tip"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area: Spacious & Professional */}
      <div className="space-y-1.5">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md bg-[#FAF4F0] text-[#7C0E44] border border-[#D49A9A]/30">
            {tip.category}
          </span>
        </div>
        <h4 className="text-sm font-semibold text-slate-900 tracking-tight">
          {tip.headline}
        </h4>
        <p className="text-xs text-slate-600 leading-relaxed max-w-4xl">
          {tip.content}
        </p>
      </div>

      {/* Minimal, Smooth Realtime Progress Bar at the very bottom */}
      {isHydrating && (
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-slate-100 overflow-hidden">
          <div
            key={currentIdx}
            className="h-full bg-[#7C0E44]"
            style={{ animation: "tipProgress 4.5s linear forwards" }}
          />
        </div>
      )}
    </div>
  );
}
