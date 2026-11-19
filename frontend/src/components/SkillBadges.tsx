"use client";

import React, { useState } from "react";
import { CheckCircle2, AlertCircle, Search, Layers } from "lucide-react";

interface SkillBadgesProps {
  matchedSkills: string[];
  missingSkills: string[];
  candidateSkills: string[];
}

export function SkillBadges({ matchedSkills, missingSkills, candidateSkills }: SkillBadgesProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const filter = (list: string[]) =>
    list.filter((s) => s.toLowerCase().includes(searchQuery.toLowerCase()));

  const filteredMatched = filter(matchedSkills);
  const filteredMissing = filter(missingSkills);
  const filteredCandidate = filter(candidateSkills);

  return (
    <div className="rounded-xl border border-[#D49A9A]/50 bg-white p-6 shadow-xs space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#D49A9A]/30">
        <div>
          <h3 className="text-base font-bold flex items-center gap-2 text-[#7C0E44]">
            <Layers className="w-4 h-4 text-[#AA5E7A]" />
            Skill Alignment & Gap Analysis
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Detailed comparison of qualifications found on your resume versus target role requirements.
          </p>
        </div>

        <div className="relative w-full sm:w-60">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search skills..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-50 border border-[#D49A9A]/40 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#7C0E44]"
          />
        </div>
      </div>

      <div className="space-y-6">
        {/* Matched Skills */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle2 className="w-4 h-4 text-[#7C0E44]" />
            <h4 className="text-sm font-bold text-[#7C0E44]">
              Matched Qualifications ({matchedSkills.length})
            </h4>
            <span className="text-[11px] text-slate-500">
              Present on both your resume and the target job description
            </span>
          </div>

          {filteredMatched.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {filteredMatched.map((skill) => (
                <span
                  key={skill}
                  className="px-3 py-1 text-xs font-semibold rounded-full bg-[#F2DACE]/60 text-[#7C0E44] border border-[#D49A9A]/50 flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-3 h-3 text-[#7C0E44]" />
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No matched skills match the search filter.</p>
          )}
        </div>

        {/* Missing Skills */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-4 h-4 text-[#AA5E7A]" />
            <h4 className="text-sm font-bold text-[#AA5E7A]">
              Identified Skill Gaps ({missingSkills.length})
            </h4>
            <span className="text-[11px] text-slate-500">
              Required by the job listing but not explicitly identified on your resume
            </span>
          </div>

          {filteredMissing.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {filteredMissing.map((skill) => (
                <span
                  key={skill}
                  className="px-3 py-1 text-xs font-semibold rounded-full bg-[#FAF4F0] text-[#AA5E7A] border border-[#D49A9A]/60 flex items-center gap-1.5"
                >
                  <AlertCircle className="w-3 h-3 text-[#AA5E7A]" />
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">
              No skill gaps found! Your resume covers all specified requirements.
            </p>
          )}
        </div>

        {/* Other Candidate Skills */}
        {candidateSkills.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <h4 className="text-xs font-bold text-slate-700">
                Additional Detected Candidate Skills ({candidateSkills.length})
              </h4>
              <span className="text-[11px] text-slate-500">
                Skills found on your resume not explicitly listed in the job post
              </span>
            </div>

            {filteredCandidate.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {filteredCandidate.map((skill) => (
                  <span
                    key={skill}
                    className="px-2.5 py-0.5 text-[11px] rounded-md bg-slate-100 text-slate-700 border border-slate-200"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No additional skills match the search filter.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
