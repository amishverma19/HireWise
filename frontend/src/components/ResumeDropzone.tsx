"use client";

import React, { useRef, useState } from "react";
import {
  UploadCloud,
  FileText,
  X,
  AlertCircle,
  Search,
  CheckCircle,
  FileCheck,
  Briefcase,
  Edit3,
  Loader2,
  ArrowRight,
} from "lucide-react";
import { analyzeResume, analyzeResumeStream } from "@/lib/api";
import { useResumeStore } from "@/store/useResumeStore";

export function ResumeDropzone() {
  const {
    resumeFile,
    setResumeFile,
    activeJob,
    isCustomJob,
    customJobText,
    customJobTitle,
    customJobCompany,
    analysisStep,
    setAnalysisStep,
    analysisProgress,
    currentStepMessage,
    setPartialProfile,
    setPartialMatch,
    setPartialImprovements,
    setAnalysisResult,
    errorMessage,
    setErrorMessage,
    editJobSelection,
  } = useResumeStore();

  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const targetRoleTitle = isCustomJob
    ? customJobTitle || "Custom Job Opening"
    : activeJob?.title || "Target Role";

  const targetRoleCompany = isCustomJob
    ? customJobCompany || "Custom Specifications"
    : activeJob?.company || "Standard Opening";

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setErrorMessage("Please select a PDF document (.pdf).");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage("File exceeds 10MB limit. Please upload a smaller PDF.");
      return;
    }
    setErrorMessage(null);
    setResumeFile(file);
  };

  const handleStartAnalysis = async () => {
    if (!resumeFile) {
      setErrorMessage("Please select or upload a resume PDF before starting analysis.");
      return;
    }

    try {
      setAnalysisStep("uploading", "Reading resume PDF document...", 20);

      await analyzeResumeStream(
        resumeFile,
        !isCustomJob ? activeJob?.id : undefined,
        isCustomJob ? customJobText : undefined,
        isCustomJob ? customJobTitle : undefined,
        {
          onStep: ({ step, message, progress }) => {
            setAnalysisStep(step as any, message, progress);
          },
          onProfile: ({ parsed_profile, progress }) => {
            // Instantly render Candidate Profile within ~2 seconds!
            setPartialProfile(parsed_profile);
          },
          onMatch: ({ match_result, ats_score, progress }) => {
            // Hydrate ATS score gauge and skill badges!
            setPartialMatch(match_result, ats_score);
          },
          onImprovements: ({ bullet_improvements, interview_tips, progress }) => {
            // Hydrate Google XYZ STAR bullet rewrites or coaching tips!
            setPartialImprovements(bullet_improvements, interview_tips);
          },
          onComplete: ({ final_result }) => {
            setAnalysisResult(final_result);
          },
          onError: (err) => {
            setErrorMessage(err.message || "An unexpected error occurred during resume evaluation.");
          },
        }
      );
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred during resume evaluation.");
    }
  };

  const isAnalyzing = analysisStep !== "idle" && analysisStep !== "completed" && analysisStep !== "error";

  return (
    <div className="space-y-6">
      {/* Locked Target Role Confirmation Banner */}
      <div className="rounded-xl border border-[#D49A9A]/50 bg-white p-4 sm:p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-[#F2DACE]/50 border border-[#D49A9A]/40 flex items-center justify-center text-[#7C0E44] shrink-0">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#AA5E7A]">
                Target Position Locked
              </span>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500" />
            </div>
            <h3 className="text-base font-bold text-[#7C0E44] leading-snug">
              {targetRoleTitle}{" "}
              <span className="text-xs font-normal text-slate-500">at {targetRoleCompany}</span>
            </h3>
          </div>
        </div>

        <button
          type="button"
          onClick={editJobSelection}
          disabled={isAnalyzing}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#D49A9A]/60 text-xs font-semibold text-[#7C0E44] hover:bg-[#F2DACE]/30 transition-all self-start sm:self-auto disabled:opacity-50"
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>Change Role</span>
        </button>
      </div>

      {/* Step 2 Heading */}
      <div className="pb-1 border-b border-[#D49A9A]/30">
        <span className="text-xs font-bold uppercase tracking-wider text-[#7C0E44]">Step 2 of 2</span>
        <h2 className="text-xl font-bold text-[#7C0E44] flex items-center gap-2 mt-0.5">
          <UploadCloud className="w-5 h-5 text-[#AA5E7A]" />
          Upload Candidate Resume
        </h2>
        <p className="text-xs text-slate-600 mt-0.5">
          Upload your resume in PDF format for direct comparison against the locked role.
        </p>
      </div>

      {/* PDF Dropzone Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !resumeFile && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-10 text-center transition-all duration-200 ${
          isDragging
            ? "border-[#7C0E44] bg-[#F2DACE]/30 scale-[1.005]"
            : resumeFile
            ? "border-[#D49A9A] bg-[#FAF4F0]/60"
            : "border-[#D49A9A]/60 bg-white hover:border-[#7C0E44] hover:bg-[#FAF4F0]/30 cursor-pointer shadow-xs"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileInput}
          className="hidden"
        />

        {!resumeFile ? (
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-14 h-14 rounded-full bg-[#F2DACE]/60 border border-[#D49A9A]/50 flex items-center justify-center text-[#7C0E44]">
              <UploadCloud className="w-7 h-7" />
            </div>
            <div>
              <p className="text-base font-bold text-[#7C0E44]">
                Drag and drop your resume (PDF)
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Standard PDF documents up to 10MB accepted
              </p>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
              className="mt-2 text-xs font-semibold px-4 py-2 rounded-lg bg-white border border-[#D49A9A] text-[#7C0E44] hover:bg-[#F2DACE]/40 transition-colors shadow-xs"
            >
              Browse Files
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between bg-white border border-[#D49A9A]/50 rounded-xl p-4 shadow-xs">
            <div className="flex items-center space-x-3 text-left">
              <div className="w-11 h-11 rounded-lg bg-[#FAF4F0] border border-[#D49A9A]/60 flex items-center justify-center text-[#7C0E44] shrink-0">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-bold text-slate-900 truncate max-w-xs md:max-w-md">
                  {resumeFile.name}
                </p>
                <p className="text-xs text-slate-500">
                  {(resumeFile.size / 1024).toFixed(1)} KB • PDF Document Ready
                </p>
              </div>
            </div>

            {!isAnalyzing && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setResumeFile(null);
                }}
                className="p-1.5 rounded-lg text-slate-400 hover:text-[#7C0E44] hover:bg-[#F2DACE]/40 transition-colors"
                title="Remove file"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Progress & Analysis Stepper */}
      {isAnalyzing && (
        <div className="rounded-xl border border-[#D49A9A]/50 bg-white p-5 space-y-3 shadow-xs">
          <div className="flex items-center justify-between text-xs text-slate-700">
            <span className="flex items-center gap-2 font-semibold text-[#7C0E44]">
              <Loader2 className="w-4 h-4 animate-spin text-[#7C0E44]" />
              {currentStepMessage}
            </span>
            <span className="font-bold text-[#7C0E44] font-mono">
              {analysisProgress}%
            </span>
          </div>

          <div className="w-full bg-[#F2DACE]/50 h-2 rounded-full overflow-hidden">
            <div
              className="bg-[#7C0E44] h-full transition-all duration-300 rounded-full"
              style={{ width: `${analysisProgress}%` }}
            />
          </div>

          <div className="grid grid-cols-4 gap-2 pt-2 text-[11px] text-slate-500">
            <div className={`flex items-center gap-1.5 ${analysisProgress >= 25 ? "text-[#7C0E44] font-bold" : ""}`}>
              <FileCheck className="w-3.5 h-3.5" />
              <span>1. Extract</span>
            </div>
            <div className={`flex items-center gap-1.5 ${analysisProgress >= 50 ? "text-[#7C0E44] font-bold" : ""}`}>
              <Search className="w-3.5 h-3.5" />
              <span>2. Match</span>
            </div>
            <div className={`flex items-center gap-1.5 ${analysisProgress >= 75 ? "text-[#7C0E44] font-bold" : ""}`}>
              <CheckCircle className="w-3.5 h-3.5" />
              <span>3. Score Fit</span>
            </div>
            <div className={`flex items-center gap-1.5 ${analysisProgress >= 90 ? "text-[#7C0E44] font-bold" : ""}`}>
              <Briefcase className="w-3.5 h-3.5" />
              <span>4. Optimize</span>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 text-xs shadow-xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Action CTA */}
      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={editJobSelection}
          disabled={isAnalyzing}
          className="text-xs text-slate-600 hover:text-[#7C0E44] font-semibold flex items-center gap-1 disabled:opacity-50"
        >
          &larr; Back to Job Selection
        </button>

        <button
          onClick={handleStartAnalysis}
          disabled={!resumeFile || isAnalyzing}
          className="px-6 py-2.5 rounded-lg bg-[#7C0E44] hover:bg-[#600B35] disabled:opacity-50 text-white font-semibold text-xs shadow-xs flex items-center gap-2 transition-all cursor-pointer"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing Resume...</span>
            </>
          ) : (
            <>
              <span>Run Assessment</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
