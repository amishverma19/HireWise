"use client";

import React, { useEffect, useState } from "react";
import { Briefcase, Building2, CheckCircle2, ChevronDown, ChevronUp, ArrowRight, Layers } from "lucide-react";
import { fetchJobs, JobDescription } from "@/lib/api";
import { useResumeStore } from "@/store/useResumeStore";

export function JobSelector() {
  const {
    activeJob,
    setActiveJob,
    isCustomJob,
    setIsCustomJob,
    customJobText,
    setCustomJobText,
    customJobTitle,
    setCustomJobTitle,
    customJobCompany,
    setCustomJobCompany,
    confirmJobSelection,
  } = useResumeStore();

  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedCardId, setExpandedCardId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchJobs();
        setJobs(data);
        if (data.length > 0 && !activeJob && !isCustomJob) {
          setActiveJob(data[0]);
        }
      } catch (e) {
        console.error("Failed to load jobs:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const toggleExpand = (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation();
    setExpandedCardId((prev) => (prev === jobId ? null : jobId));
  };

  const handleProceed = () => {
    if (isCustomJob && !customJobText.trim()) {
      alert("Please provide the custom job description requirements before proceeding.");
      return;
    }
    confirmJobSelection();
  };

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#D49A9A]/30">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-[#7C0E44]">Step 1 of 2</span>
          <h2 className="text-xl font-bold text-[#7C0E44] flex items-center gap-2 mt-0.5">
            <Briefcase className="w-5 h-5 text-[#AA5E7A]" />
            Define Target Position
          </h2>
          <p className="text-xs text-slate-600 mt-0.5">
            Select a verified role template or paste custom job specifications.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex rounded-lg bg-[#F2DACE]/40 p-1 border border-[#D49A9A]/40 self-start sm:self-auto">
          <button
            type="button"
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              !isCustomJob
                ? "bg-[#7C0E44] text-white shadow-xs"
                : "text-slate-700 hover:text-[#7C0E44]"
            }`}
            onClick={() => setIsCustomJob(false)}
          >
            Role Templates
          </button>
          <button
            type="button"
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              isCustomJob
                ? "bg-[#7C0E44] text-white shadow-xs"
                : "text-slate-700 hover:text-[#7C0E44]"
            }`}
            onClick={() => setIsCustomJob(true)}
          >
            Custom Job Description
          </button>
        </div>
      </div>

      {!isCustomJob ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="h-48 rounded-xl bg-white animate-pulse border border-[#D49A9A]/30"
              />
            ))
          ) : (
            jobs.map((job) => {
              const isSelected = activeJob?.id === job.id;
              const isExpanded = expandedCardId === job.id;
              const displayedSkills = isExpanded ? job.skills_required : job.skills_required.slice(0, 4);
              const remainingCount = job.skills_required.length - 4;

              return (
                <div
                  key={job.id}
                  onClick={() => setActiveJob(job)}
                  className={`group relative rounded-xl p-5 border cursor-pointer transition-all duration-200 flex flex-col justify-between ${
                    isSelected
                      ? "border-[#7C0E44] bg-[#FAF4F0] ring-2 ring-[#7C0E44]/20 shadow-sm"
                      : "border-[#D49A9A]/40 bg-white hover:border-[#AA5E7A] hover:shadow-xs"
                  }`}
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h3 className={`font-bold text-sm ${isSelected ? "text-[#7C0E44]" : "text-slate-900"}`}>
                        {job.title}
                      </h3>
                      {isSelected ? (
                        <CheckCircle2 className="w-5 h-5 text-[#7C0E44] shrink-0" />
                      ) : (
                        <div className="w-5 h-5 rounded-full border border-slate-300 group-hover:border-[#AA5E7A] shrink-0" />
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-500 mb-3">
                      <Building2 className="w-3.5 h-3.5 text-[#AA5E7A]" />
                      <span className="font-medium text-slate-700">{job.company}</span>
                      <span>•</span>
                      <span>{job.min_years_experience}+ yrs exp</span>
                    </div>

                    <p className="text-xs text-slate-600 line-clamp-2 mb-3 leading-relaxed">
                      {job.description}
                    </p>
                  </div>

                  {/* Skills Section with Expandable '+N more' */}
                  <div className="pt-3 border-t border-[#D49A9A]/20">
                    <div className="flex flex-wrap gap-1.5 items-center">
                      {displayedSkills.map((skill) => (
                        <span
                          key={skill}
                          className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                            isSelected
                              ? "bg-[#7C0E44] text-white"
                              : "bg-[#F2DACE]/60 text-[#7C0E44] border border-[#D49A9A]/40"
                          }`}
                        >
                          {skill}
                        </span>
                      ))}

                      {remainingCount > 0 && (
                        <button
                          type="button"
                          onClick={(e) => toggleExpand(e, job.id)}
                          className="text-[10px] text-[#AA5E7A] hover:text-[#7C0E44] font-semibold underline underline-offset-2 flex items-center gap-0.5 ml-1 py-0.5 cursor-pointer"
                        >
                          {isExpanded ? (
                            <>
                              <span>Show less</span>
                              <ChevronUp className="w-3 h-3" />
                            </>
                          ) : (
                            <>
                              <span>+{remainingCount} more</span>
                              <ChevronDown className="w-3 h-3" />
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      ) : (
        /* Custom JD Input Card */
        <div className="rounded-xl border border-[#D49A9A]/50 bg-white p-5 shadow-xs space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-[#7C0E44] mb-1 block">
                Target Role Title *
              </label>
              <input
                type="text"
                value={customJobTitle}
                onChange={(e) => setCustomJobTitle(e.target.value)}
                placeholder="e.g. Senior Backend Systems Engineer"
                className="w-full rounded-lg bg-white border border-[#D49A9A]/60 px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#7C0E44] focus:border-[#7C0E44]"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-[#7C0E44] mb-1 block">
                Hiring Organization / Company (Optional)
              </label>
              <input
                type="text"
                value={customJobCompany}
                onChange={(e) => setCustomJobCompany(e.target.value)}
                placeholder="e.g. Acme Tech Corporation"
                className="w-full rounded-lg bg-white border border-[#D49A9A]/60 px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#7C0E44] focus:border-[#7C0E44]"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-bold text-[#7C0E44] mb-1 block">
              Job Description, Key Responsibilities & Requirements *
            </label>
            <textarea
              value={customJobText}
              onChange={(e) => setCustomJobText(e.target.value)}
              rows={6}
              placeholder="Paste full job description from LinkedIn, Greenhouse, or company careers page..."
              className="w-full rounded-lg bg-white border border-[#D49A9A]/60 p-3.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#7C0E44] focus:border-[#7C0E44] resize-none font-sans leading-relaxed"
            />
          </div>
        </div>
      )}

      {/* Primary Proceed CTA to lock JD */}
      <div className="flex items-center justify-between pt-2">
        <div className="text-xs text-slate-500">
          Selected:{" "}
          <span className="font-semibold text-[#7C0E44]">
            {isCustomJob ? customJobTitle || "Custom Role" : activeJob?.title || "Choose a role above"}
          </span>
        </div>

        <button
          type="button"
          onClick={handleProceed}
          className="flex items-center gap-2 rounded-lg bg-[#7C0E44] text-white text-xs font-semibold py-2.5 px-5 hover:bg-[#630A36] active:bg-[#50082B] transition-colors shadow-xs"
        >
          <span>Save Role & Proceed to Resume Upload</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
