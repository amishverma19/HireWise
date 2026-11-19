"use client";

import React from "react";
import {
  FileCheck2,
  ListRestart,
  Download,
  Briefcase,
  Award,
  CheckCircle2,
  Target,
  Search,
  ArrowRight,
  TrendingUp,
  Check,
  ChevronRight,
  Layers,
  FileText,
} from "lucide-react";
import { useResumeStore } from "@/store/useResumeStore";
import { HistorySidebar } from "@/components/HistorySidebar";
import { AuthModal } from "@/components/AuthModal";
import { JobSelector } from "@/components/JobSelector";
import { ResumeDropzone } from "@/components/ResumeDropzone";
import { ScoreGauge } from "@/components/ScoreGauge";
import { SkillBadges } from "@/components/SkillBadges";
import { BulletDiffTable } from "@/components/BulletDiffTable";
import { InterviewTipsCarousel } from "@/components/InterviewTipsCarousel";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";

export default function HireWiseDashboard() {
  const {
    workflowStep,
    analysisResult,
    resetToNewAnalysis,
    activeTab,
    setActiveTab,
    activeJob,
    isCustomJob,
    customJobTitle,
    customJobCompany,
    user,
    setAuthModalOpen,
    isHydrating,
    currentStepMessage,
  } = useResumeStore();

  const handleExportJSON = () => {
    if (!analysisResult) return;
    const blob = new Blob([JSON.stringify(analysisResult, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hirewise-evaluation-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const targetTitle = isCustomJob
    ? customJobTitle || "Custom Position"
    : activeJob?.title || "Target Role";

  const targetCompany = isCustomJob
    ? customJobCompany || "Custom Specifications"
    : activeJob?.company || "Standard Opening";

  return (
    <div className="h-screen bg-[#FAF8F7] text-slate-900 flex font-sans overflow-hidden">
      {/* Authentication Modal */}
      <AuthModal />

      {/* Collapsible Left History Sidebar */}
      <HistorySidebar />

      {/* Main App Canvas */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-y-auto">
        {/* Top Header (Sticky on top with blur & shadow) */}
        <header className="border-b border-[#D49A9A]/30 bg-white/95 backdrop-blur-xs sticky top-0 z-30 shadow-xs shrink-0">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-[#7C0E44] text-white flex items-center justify-center font-bold shadow-xs">
                <FileCheck2 className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-base font-bold text-[#7C0E44] tracking-tight">HireWise</h1>
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-[#F2DACE]/60 text-[#7C0E44] border border-[#D49A9A]/40">
                    Evaluation Platform
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 hidden sm:block">
                  Candidate Qualification & Resume Alignment System
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {user ? (
                <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#F2DACE]/50 border border-[#D49A9A]/40 text-xs font-semibold text-[#7C0E44]">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span>{user.full_name || user.email.split("@")[0]}</span>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setAuthModalOpen(true, "login")}
                  className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#7C0E44] hover:bg-[#600B35] text-white shadow-xs transition-colors"
                >
                  Sign In
                </button>
              )}

              {analysisResult && (
                <button
                  type="button"
                  onClick={resetToNewAnalysis}
                  className="text-xs font-semibold px-3.5 py-1.5 rounded-lg border border-[#D49A9A]/60 text-[#7C0E44] hover:bg-[#F2DACE]/30 transition-all flex items-center gap-1.5"
                >
                  <ListRestart className="w-3.5 h-3.5" />
                  <span>New Evaluation</span>
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Main Content Area: max-w-7xl */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full flex-1 space-y-8">
          {/* Workflow Stepper / Status Bar */}
          <div className="rounded-xl border border-[#D49A9A]/40 bg-white p-4 shadow-xs">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              {/* Step 1 */}
              <div
                className={`flex items-center gap-2.5 p-2 rounded-lg transition-all ${
                  workflowStep === "job"
                    ? "bg-[#F2DACE]/50 text-[#7C0E44] font-bold"
                    : workflowStep === "resume" || workflowStep === "results"
                    ? "text-[#7C0E44]"
                    : "text-slate-400"
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 ${
                    workflowStep === "job"
                      ? "bg-[#7C0E44] text-white"
                      : workflowStep === "resume" || workflowStep === "results"
                      ? "bg-[#F2DACE] text-[#7C0E44] font-bold"
                      : "bg-slate-100 text-slate-400"
                  }`}
                >
                  1
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-[#AA5E7A] font-semibold">Step 1</div>
                  <div className="truncate">Select & Lock Job</div>
                </div>
              </div>

              {/* Step 2 */}
              <div
                className={`flex items-center gap-2.5 p-2 rounded-lg transition-all ${
                  workflowStep === "resume"
                    ? "bg-[#F2DACE]/50 text-[#7C0E44] font-bold"
                    : workflowStep === "results"
                    ? "text-[#7C0E44]"
                    : "text-slate-400"
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 ${
                    workflowStep === "resume"
                      ? "bg-[#7C0E44] text-white"
                      : workflowStep === "results"
                      ? "bg-[#F2DACE] text-[#7C0E44] font-bold"
                      : "bg-slate-100 text-slate-400"
                  }`}
                >
                  2
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-[#AA5E7A] font-semibold">Step 2</div>
                  <div className="truncate">Upload Resume (PDF)</div>
                </div>
              </div>

              {/* Step 3 */}
              <div
                className={`flex items-center gap-2.5 p-2 rounded-lg transition-all ${
                  workflowStep === "results"
                    ? "bg-[#F2DACE]/50 text-[#7C0E44] font-bold"
                    : "text-slate-400"
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 ${
                    workflowStep === "results"
                      ? "bg-[#7C0E44] text-white"
                      : "bg-slate-100 text-slate-400"
                  }`}
                >
                  3
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-[#AA5E7A] font-semibold">Step 3</div>
                  <div className="truncate">Analysis & Recommendations</div>
                </div>
              </div>
            </div>
          </div>

          {/* Sequential Step Routing */}
          {workflowStep === "job" && (
            <div className="space-y-6 animate-in fade-in-50 duration-200">
              <JobSelector />
            </div>
          )}

          {workflowStep === "resume" && (
            <div className="space-y-6 animate-in fade-in-50 duration-200">
              <ResumeDropzone />
            </div>
          )}

          {workflowStep === "results" && analysisResult && (
            <div className="space-y-8 animate-in fade-in-50 duration-300">
              {/* Header Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-[#D49A9A]/50 rounded-2xl p-5 shadow-xs">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[11px] uppercase tracking-wider text-[#AA5E7A] font-bold">
                      Candidate Evaluation Report
                    </span>
                    <span className="text-slate-300">•</span>
                    <span className="text-xs text-slate-700 font-semibold">
                      {analysisResult.parsed_profile.full_name || "Applicant"}
                    </span>
                    {isHydrating && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-300 text-[10px] font-bold animate-pulse">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-ping" />
                        <span>Live: {currentStepMessage || "Optimizing STAR bullets..."}</span>
                      </span>
                    )}
                  </div>
                  <h2 className="text-xl font-bold text-[#7C0E44] mt-0.5">
                    {targetTitle}{" "}
                    <span className="text-sm font-normal text-slate-500">at {targetCompany}</span>
                  </h2>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleExportJSON}
                    className="text-xs font-semibold px-3 py-2 rounded-lg border border-[#D49A9A]/60 bg-white text-[#7C0E44] hover:bg-[#F2DACE]/30 transition-all flex items-center gap-1.5 shadow-xs"
                  >
                    <Download className="w-3.5 h-3.5 text-[#AA5E7A]" />
                    <span>Export JSON</span>
                  </button>
                  <button
                    type="button"
                    onClick={resetToNewAnalysis}
                    className="text-xs font-semibold px-4 py-2 rounded-lg bg-[#7C0E44] hover:bg-[#600B35] text-white transition-all flex items-center gap-1.5 shadow-xs"
                  >
                    <ListRestart className="w-3.5 h-3.5" />
                    <span>New Evaluation</span>
                  </button>
                </div>
              </div>

              {/* Rotating Anti-Boredom Pro-Tips Carousel when hydrating (Placed on TOP of Score section) */}
              {isHydrating && (
                <div className="animate-in fade-in-50 slide-in-from-top-3 duration-300">
                  <InterviewTipsCarousel />
                </div>
              )}

              {/* ATS Score Radial Gauge & Sub-Scores */}
              <ScoreGauge
                score={analysisResult.ats_score}
                matchResult={analysisResult.match_result}
                profile={analysisResult.parsed_profile}
              />

              {/* Tab Navigation */}
              <Tabs
                value={activeTab}
                onValueChange={(val) => setActiveTab(val as any)}
                className="space-y-4"
              >
                <div className="flex justify-center sm:justify-start">
                  <TabsList>
                    <TabsTrigger value="overview">Executive Summary</TabsTrigger>
                    <TabsTrigger value="skills">
                      Skill Alignment ({analysisResult.match_result.matched_skills.length})
                    </TabsTrigger>
                    <TabsTrigger value="bullets" className="flex items-center gap-1.5">
                      <span>STAR Rewrites</span>
                      {isHydrating && analysisResult.bullet_improvements.length === 0 ? (
                        <span className="inline-block w-2 h-2 rounded-full bg-amber-500 animate-ping" />
                      ) : (
                        <span>({analysisResult.bullet_improvements.length})</span>
                      )}
                    </TabsTrigger>
                    {analysisResult.interview_tips.length > 0 && (
                      <TabsTrigger value="interview">
                        Interview Prep ({analysisResult.interview_tips.length})
                      </TabsTrigger>
                    )}
                    <TabsTrigger value="checklist">Action Checklist</TabsTrigger>
                  </TabsList>
                </div>

                {/* Tab 1: Executive Overview */}
                <TabsContent value="overview">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="rounded-xl border border-[#D49A9A]/40 bg-white p-6 shadow-xs space-y-4">
                      <div className="flex items-center gap-2 text-[#7C0E44] font-bold text-base border-b border-[#D49A9A]/30 pb-3">
                        <Award className="w-5 h-5 text-[#AA5E7A]" />
                        <span>Assessment Summary</span>
                      </div>
                      <p className="text-xs text-slate-800 leading-relaxed bg-[#FAF4F0] border border-[#D49A9A]/30 p-4 rounded-xl">
                        {analysisResult.match_result.match_summary}
                      </p>

                      <div className="space-y-2 pt-2">
                        <h4 className="font-bold text-[#7C0E44] text-xs">Readiness Benchmark:</h4>
                        {analysisResult.passed_threshold ? (
                          <div className="flex items-center gap-2 text-emerald-800 text-xs font-semibold bg-emerald-50 border border-emerald-200 p-3 rounded-lg">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                            <span>Candidate exceeds 80% benchmark. Profile is well prepared for submission.</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 text-[#7C0E44] text-xs font-semibold bg-[#F2DACE]/50 border border-[#D49A9A]/50 p-3 rounded-lg">
                            <Briefcase className="w-4 h-4 text-[#AA5E7A] shrink-0" />
                            <span>Score is under 80%. Review skill gaps and apply the recommended STAR bullet updates.</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="rounded-xl border border-[#D49A9A]/40 bg-white p-6 shadow-xs space-y-4">
                      <div className="flex items-center gap-2 text-[#7C0E44] font-bold text-base border-b border-[#D49A9A]/30 pb-3">
                        <Briefcase className="w-5 h-5 text-[#AA5E7A]" />
                        <span>Experience & Credentials</span>
                      </div>
                      <div className="space-y-3 text-xs text-slate-700">
                        <div>
                          <span className="text-slate-500 block mb-1">Total Experience Verified:</span>
                          <span className="text-lg font-bold text-[#7C0E44]">
                            {analysisResult.parsed_profile.total_years_experience} Years
                          </span>
                          <span className="text-slate-500 ml-2">
                            (Target role requires {analysisResult.match_result.experience_years_required} years)
                          </span>
                        </div>

                        {analysisResult.parsed_profile.education.length > 0 && (
                          <div className="pt-3 border-t border-[#D49A9A]/20">
                            <span className="text-slate-500 block mb-1 font-semibold">Education Credentials:</span>
                            <ul className="list-disc list-inside space-y-1 text-slate-800">
                              {analysisResult.parsed_profile.education.map((edu, idx) => (
                                <li key={idx}>{edu}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </TabsContent>

                {/* Tab 2: Skills Matrix */}
                <TabsContent value="skills">
                  <SkillBadges
                    matchedSkills={analysisResult.match_result.matched_skills}
                    missingSkills={analysisResult.match_result.missing_skills}
                    candidateSkills={analysisResult.parsed_profile.skills}
                  />
                </TabsContent>

                {/* Tab 3: STAR Bullet Improvements */}
                <TabsContent value="bullets">
                  {isHydrating && analysisResult.bullet_improvements.length === 0 ? (
                    <div className="space-y-4">
                      <div className="rounded-xl border border-amber-300/80 bg-amber-50/50 p-6 text-center space-y-2">
                        <div className="w-9 h-9 rounded-full bg-amber-100 border border-amber-300 text-amber-800 flex items-center justify-center mx-auto text-base animate-pulse">
                          ⚡
                        </div>
                        <h4 className="text-sm font-bold text-amber-900">
                          Synthesizing Senior STAR Bullets & Interview Talking Scripts...
                        </h4>
                        <p className="text-xs text-amber-800 max-w-md mx-auto leading-relaxed">
                          Applying senior engineering action verbs, real-world latency & throughput metrics, and crafting exact speaking scripts for your interview. Arriving in ~1-2 seconds.
                        </p>
                      </div>
                      <InterviewTipsCarousel />
                    </div>
                  ) : (
                    <BulletDiffTable improvements={analysisResult.bullet_improvements} />
                  )}
                </TabsContent>

                {/* Tab 4: Interview Coaching */}
                {analysisResult.interview_tips.length > 0 && (
                  <TabsContent value="interview">
                    <div className="rounded-xl border border-[#D49A9A]/50 bg-white p-6 shadow-xs space-y-4">
                      <div className="pb-3 border-b border-[#D49A9A]/30">
                        <h3 className="text-base font-bold text-[#7C0E44] flex items-center gap-2">
                          <Target className="w-5 h-5 text-[#AA5E7A]" />
                          Role-Specific Interview Discussion Topics
                        </h3>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Anticipated questions and talking points aligned with this position.
                        </p>
                      </div>

                      <div className="space-y-3">
                        {analysisResult.interview_tips.map((tip, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-3 p-4 rounded-xl bg-[#FAF4F0]/60 border border-[#D49A9A]/40 text-xs text-slate-800"
                          >
                            <span className="w-6 h-6 rounded-full bg-[#7C0E44] text-white font-bold flex items-center justify-center text-xs shrink-0">
                              {idx + 1}
                            </span>
                            <p className="leading-relaxed mt-0.5">{tip}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </TabsContent>
                )}

                {/* Tab 5: Action Checklist */}
                <TabsContent value="checklist">
                  <div className="rounded-xl border border-[#D49A9A]/50 bg-white p-6 shadow-xs space-y-4">
                    <div className="pb-3 border-b border-[#D49A9A]/30">
                      <h3 className="text-base font-bold text-[#7C0E44] flex items-center gap-2">
                        <FileCheck2 className="w-5 h-5 text-[#AA5E7A]" />
                        Application Finalization Checklist
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        High-leverage steps to complete before submitting your application.
                      </p>
                    </div>

                    <div className="space-y-3 text-xs text-slate-800">
                      <div className="flex items-start gap-3 p-3.5 rounded-xl bg-[#FAF4F0]/60 border border-[#D49A9A]/40">
                        <Check className="w-4 h-4 text-[#7C0E44] shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold text-[#7C0E44] block mb-0.5">
                            Incorporate Missing Technical Keywords
                          </span>
                          <span className="text-slate-600">
                            Add missing skills ({analysisResult.match_result.missing_skills.slice(0, 5).join(", ")}) into your skills summary or past project accomplishments where you have working familiarity.
                          </span>
                        </div>
                      </div>

                      <div className="flex items-start gap-3 p-3.5 rounded-xl bg-[#FAF4F0]/60 border border-[#D49A9A]/40">
                        <Check className="w-4 h-4 text-[#7C0E44] shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold text-[#7C0E44] block mb-0.5">
                            Apply STAR Formatted Achievements
                          </span>
                          <span className="text-slate-600">
                            Replace passive bullet phrasing with the STAR rewrites generated in the &lsquo;STAR Rewrites&rsquo; tab, highlighting concrete metrics and deliverables.
                          </span>
                        </div>
                      </div>

                      <div className="flex items-start gap-3 p-3.5 rounded-xl bg-[#FAF4F0]/60 border border-[#D49A9A]/40">
                        <Check className="w-4 h-4 text-[#7C0E44] shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold text-[#7C0E44] block mb-0.5">
                            Tailor Cover Letter & Talking Points
                          </span>
                          <span className="text-slate-600">
                            Emphasize your {analysisResult.parsed_profile.total_years_experience} years of experience in your cover letter and prepare responses for the topics outlined in the Interview Prep tab.
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </main>

        {/* Clean Light Footer */}
        <footer className="border-t border-[#D49A9A]/30 bg-white py-4 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4">
            <p>HireWise — Candidate Qualification & Resume Alignment System</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
