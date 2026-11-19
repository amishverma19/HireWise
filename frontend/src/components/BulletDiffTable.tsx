"use client";

import React, { useState } from "react";
import { Check, Copy, TrendingUp, AlertTriangle, FileText } from "lucide-react";
import { BulletImprovement } from "@/lib/api";

interface BulletDiffTableProps {
  improvements: BulletImprovement[];
}

export function BulletDiffTable({ improvements }: BulletDiffTableProps) {
  const [copiedIndex, setCopiedIndex] = useState<string | number | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);

  const handleCopy = (text: string, indexKey: string | number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(indexKey);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleCopyAll = () => {
    const allText = improvements.map((b) => `• ${b.improved}`).join("\n");
    navigator.clipboard.writeText(allText);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  if (!improvements || improvements.length === 0) {
    return (
      <div className="rounded-xl border border-[#D49A9A]/50 bg-white p-8 text-center shadow-xs">
        <div className="w-12 h-12 rounded-full bg-[#F2DACE]/50 border border-[#D49A9A]/40 flex items-center justify-center text-[#7C0E44] mx-auto mb-3">
          <Check className="w-6 h-6" />
        </div>
        <h4 className="text-base font-bold text-[#7C0E44]">Strong Existing Bullet Points</h4>
        <p className="text-xs text-slate-600 mt-1 max-w-md mx-auto">
          Your resume achieved an ATS fit score of &ge; 80%. Your bullet points already demonstrate good impact and structure. Proceed to the Interview Coaching section for targeted discussion guidance.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[#D49A9A]/50 bg-white p-6 shadow-xs space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#D49A9A]/30">
        <div>
          <h3 className="text-base font-bold flex items-center gap-2 text-[#7C0E44]">
            <TrendingUp className="w-4 h-4 text-[#AA5E7A]" />
            STAR Bullet Point Improvements
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Transform passive responsibilities into measurable STAR achievements (Situation, Task, Action, Result).
          </p>
        </div>

        <button
          type="button"
          onClick={handleCopyAll}
          className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#D49A9A]/60 text-[#7C0E44] hover:bg-[#F2DACE]/30 transition-all flex items-center gap-1.5 self-start sm:self-auto cursor-pointer"
        >
          {copiedAll ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          {copiedAll ? "Copied All Bullets!" : "Copy All Improved Bullets"}
        </button>
      </div>

      <div className="space-y-4">
        {improvements.map((item, index) => (
          <div
            key={index}
            className="rounded-xl border border-[#D49A9A]/40 bg-[#FAF8F7] p-4 transition-all hover:border-[#AA5E7A] space-y-3"
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Original Bullet */}
              <div className="rounded-lg bg-rose-50/70 border border-rose-200/80 p-3.5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-rose-200/80 text-rose-900">
                      Original Statement
                    </span>
                  </div>
                  <p className="text-xs text-slate-800 leading-relaxed">
                    &ldquo;{item.original}&rdquo;
                  </p>
                </div>

                <div className="mt-3 pt-2 border-t border-rose-200/60 flex items-start gap-1.5 text-[11px] text-rose-800">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-rose-600" />
                  <span>{item.critique}</span>
                </div>
              </div>

              {/* Improved STAR Bullet */}
              <div className="rounded-lg bg-[#FAF4F0] border border-[#D49A9A]/60 p-3.5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#7C0E44] text-white">
                      Recommended STAR Rewrite
                    </span>
                    <button
                      type="button"
                      onClick={() => handleCopy(item.improved, index)}
                      className="text-xs text-[#7C0E44] hover:text-[#AA5E7A] font-semibold flex items-center gap-1 cursor-pointer"
                      title="Copy bullet"
                    >
                      {copiedIndex === index ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span className="text-emerald-700 font-bold">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>

                  <p className="text-xs text-slate-900 font-medium leading-relaxed">
                    &ldquo;{item.improved}&rdquo;
                  </p>
                </div>

                <div className="mt-3 pt-2 border-t border-[#D49A9A]/30 flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">
                    Target Impact: <strong className="text-[#7C0E44]">{item.impact_metric || "Measurable Outcome"}</strong>
                  </span>
                  <span className="text-emerald-700 font-semibold flex items-center gap-1">
                    <Check className="w-3 h-3" /> STAR Structured
                  </span>
                </div>
              </div>
            </div>

            {/* Conversational Interview Script Section */}
            {item.interview_script && (
              <div className="rounded-lg bg-white border border-[#D49A9A]/50 p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-[#7C0E44] flex items-center gap-1.5">
                    <span>🗣️</span> How to Speak to This in an Interview
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(item.interview_script!, `script-${index}`)}
                    className="text-[11px] text-[#7C0E44] hover:text-[#AA5E7A] font-semibold flex items-center gap-1 cursor-pointer"
                  >
                    {copiedIndex === `script-${index}` ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                        <span className="text-emerald-700 font-bold">Copied Script</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy Script</span>
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-slate-800 italic bg-[#FAF8F7] p-2.5 rounded-md border border-[#D49A9A]/30 leading-relaxed font-sans">
                  {item.interview_script}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
