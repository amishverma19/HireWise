"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, Target, Zap, Clock, UserCheck } from "lucide-react";
import { MatchResult, ParsedResume } from "@/lib/api";

interface ScoreGaugeProps {
  score: number;
  matchResult: MatchResult;
  profile: ParsedResume;
}

export function ScoreGauge({ score, matchResult, profile }: ScoreGaugeProps) {
  const radius = 70;
  const strokeWidth = 12;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  let strokeColor = "#D49A9A";
  let statusBadgeClasses = "bg-[#F2DACE] text-[#7C0E44] border border-[#D49A9A]";
  let statusText = "Requires Optimization (<60%)";

  if (score >= 80) {
    strokeColor = "#7C0E44";
    statusBadgeClasses = "bg-[#7C0E44] text-white";
    statusText = "Strong Alignment (80%+)";
  } else if (score >= 60) {
    strokeColor = "#AA5E7A";
    statusBadgeClasses = "bg-[#AA5E7A] text-white";
    statusText = "Moderate Alignment (60-79%)";
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
      {/* Radial Gauge Visual */}
      <div className="lg:col-span-5 flex flex-col items-center justify-center p-6 rounded-2xl bg-white border border-[#D49A9A]/50 shadow-xs relative">
        <div className="relative w-48 h-48 flex items-center justify-center">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
            {/* Background Track */}
            <circle
              cx="80"
              cy="80"
              r={radius}
              stroke="#F2DACE"
              fill="none"
              strokeWidth={strokeWidth}
            />
            {/* Value Arc */}
            <circle
              cx="80"
              cy="80"
              r={radius}
              stroke={strokeColor}
              fill="none"
              className="transition-all duration-1000 ease-out"
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
            />
          </svg>

          {/* Center Text */}
          <div className="absolute flex flex-col items-center justify-center text-center">
            <span className="text-4xl font-extrabold text-[#7C0E44] tracking-tight">
              {score.toFixed(0)}
              <span className="text-xl text-[#AA5E7A] font-medium">%</span>
            </span>
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold mt-0.5">
              ATS Fit Score
            </span>
          </div>
        </div>

        <div className="mt-4 flex flex-col items-center space-y-1.5">
          <span className={`text-xs px-3 py-1 font-semibold rounded-full ${statusBadgeClasses}`}>
            {statusText}
          </span>
          <p className="text-xs text-slate-600 text-center max-w-xs mt-1">
            {score >= 80
              ? "Your profile aligns well with this role. Recommended interview preparation topics are provided below."
              : "Review the missing skill gaps and targeted bullet rewrites below to improve role alignment."}
          </p>
        </div>
      </div>

      {/* Sub-Score Breakdown Cards */}
      <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Skill Match Sub-Score */}
        <div className="rounded-xl border border-[#D49A9A]/50 bg-white p-4 flex flex-col justify-between shadow-xs">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-600">Skill Alignment</span>
              <Target className="w-4 h-4 text-[#7C0E44]" />
            </div>
            <div className="text-2xl font-bold text-[#7C0E44]">
              {matchResult.skill_match_score.toFixed(1)}%
            </div>
          </div>
          <div className="mt-3 text-[11px] text-slate-600 border-t border-[#D49A9A]/30 pt-2">
            <span className="text-[#7C0E44] font-bold">
              {matchResult.matched_skills.length}
            </span>{" "}
            matched •{" "}
            <span className="text-[#AA5E7A] font-bold">
              {matchResult.missing_skills.length}
            </span>{" "}
            missing
          </div>
        </div>

        {/* Vector Similarity Sub-Score */}
        <div className="rounded-xl border border-[#D49A9A]/50 bg-white p-4 flex flex-col justify-between shadow-xs">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-600">Contextual Match</span>
              <Zap className="w-4 h-4 text-[#AA5E7A]" />
            </div>
            <div className="text-2xl font-bold text-[#7C0E44]">
              {matchResult.vector_similarity_score.toFixed(1)}%
            </div>
          </div>
          <div className="mt-3 text-[11px] text-slate-600 border-t border-[#D49A9A]/30 pt-2">
            Semantic relevance against requirements
          </div>
        </div>

        {/* Experience Sub-Score */}
        <div className="rounded-xl border border-[#D49A9A]/50 bg-white p-4 flex flex-col justify-between shadow-xs">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-600">Experience Fit</span>
              <Clock className="w-4 h-4 text-[#7C0E44]" />
            </div>
            <div className="text-2xl font-bold text-[#7C0E44]">
              {matchResult.experience_score.toFixed(1)}%
            </div>
          </div>
          <div className="mt-3 text-[11px] text-slate-600 border-t border-[#D49A9A]/30 pt-2">
            <span className="text-[#7C0E44] font-bold">{profile.total_years_experience}</span> /{" "}
            {matchResult.experience_years_required} yrs required
          </div>
        </div>

        {/* Candidate Profile Summary Banner */}
        <div className="sm:col-span-3 rounded-xl border border-[#D49A9A]/50 bg-[#FAF4F0]/60 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-700 shadow-xs">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#F2DACE] border border-[#D49A9A]/40 flex items-center justify-center text-[#7C0E44] shrink-0 mt-0.5">
              <UserCheck className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-[#7C0E44] text-sm block">
                {profile.full_name || "Candidate"}
              </span>
              <span className="text-slate-500">
                {profile.email} {profile.phone && `• ${profile.phone}`}
              </span>
            </div>
          </div>
          <div className="text-slate-700 max-w-sm text-[11px] leading-relaxed">
            <span className="text-[#7C0E44] font-semibold">Summary: </span>
            {profile.summary || "No professional summary provided in resume."}
          </div>
        </div>
      </div>
    </div>
  );
}
