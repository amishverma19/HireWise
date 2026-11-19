import { create } from "zustand";
import {
  clearAuthToken,
  BulletImprovement,
  HireWiseAnalysisResult,
  HistoryItem,
  JobDescription,
  MatchResult,
  ParsedResume,
  UserProfile,
} from "@/lib/api";

export type AnalysisStep =
  | "idle"
  | "uploading"
  | "retrieving"
  | "cached"
  | "parsing"
  | "matching"
  | "optimizing"
  | "coaching"
  | "finalizing"
  | "completed"
  | "error";

export type WorkflowStep = "job" | "resume" | "results";

interface ResumeState {
  // Authentication State
  user: UserProfile | null;
  token: string | null;
  isAuthModalOpen: boolean;
  authModalMode: "login" | "register" | "forgot";

  // Workflow Step: "job" (1) -> "resume" (2) -> "results" (3)
  workflowStep: WorkflowStep;
  jobConfirmed: boolean;

  // Target Job State
  activeJob: JobDescription | null;
  customJobText: string;
  customJobTitle: string;
  customJobCompany: string;
  isCustomJob: boolean;

  // File State
  resumeFile: File | null;
  resumeFileName: string;

  // Pipeline Status & Progress
  analysisStep: AnalysisStep;
  analysisProgress: number;
  currentStepMessage: string;
  isHydrating: boolean;

  // Output Payload
  analysisResult: HireWiseAnalysisResult | null;
  errorMessage: string | null;

  // Active View Tab
  activeTab: "overview" | "skills" | "bullets" | "interview" | "checklist";

  // Sidebar & History State
  isSidebarOpen: boolean;
  historyItems: HistoryItem[];
  isHistoryLoading: boolean;

  // Auth Actions
  setUser: (user: UserProfile | null, token?: string | null) => void;
  setAuthModalOpen: (open: boolean, mode?: "login" | "register" | "forgot") => void;
  logout: () => void;

  // Actions
  setWorkflowStep: (step: WorkflowStep) => void;
  confirmJobSelection: () => void;
  editJobSelection: () => void;
  setActiveJob: (job: JobDescription | null) => void;
  setCustomJobText: (text: string) => void;
  setCustomJobTitle: (title: string) => void;
  setCustomJobCompany: (company: string) => void;
  setIsCustomJob: (isCustom: boolean) => void;
  setResumeFile: (file: File | null) => void;
  setAnalysisStep: (step: AnalysisStep, message?: string, progress?: number) => void;
  setPartialProfile: (profile: ParsedResume) => void;
  setPartialMatch: (matchResult: MatchResult, atsScore: number) => void;
  setPartialImprovements: (bulletImprovements: BulletImprovement[], interviewTips: string[]) => void;
  setAnalysisResult: (result: HireWiseAnalysisResult) => void;
  setErrorMessage: (msg: string | null) => void;
  setActiveTab: (tab: "overview" | "skills" | "bullets" | "interview" | "checklist") => void;
  
  // History Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setHistoryItems: (items: HistoryItem[]) => void;
  setIsHistoryLoading: (loading: boolean) => void;
  loadPastReport: (report: HireWiseAnalysisResult, roleTitle?: string) => void;
  resetToNewAnalysis: () => void;
}

export const useResumeStore = create<ResumeState>((set) => ({
  user: null,
  token: null,
  isAuthModalOpen: false,
  authModalMode: "login",

  workflowStep: "job",
  jobConfirmed: false,

  activeJob: null,
  customJobText: "",
  customJobTitle: "",
  customJobCompany: "",
  isCustomJob: false,

  resumeFile: null,
  resumeFileName: "",

  analysisStep: "idle",
  analysisProgress: 0,
  currentStepMessage: "",
  isHydrating: false,

  analysisResult: null,
  errorMessage: null,
  activeTab: "overview",

  isSidebarOpen: true,
  historyItems: [],
  isHistoryLoading: false,

  setUser: (user, token) => set((state) => ({ user, token: token !== undefined ? token : state.token })),
  setAuthModalOpen: (open, mode = "login") => set({ isAuthModalOpen: open, authModalMode: mode }),
  logout: () => {
    clearAuthToken();
    set({ user: null, token: null, historyItems: [] });
  },

  setWorkflowStep: (step) => set({ workflowStep: step }),
  confirmJobSelection: () => set({ jobConfirmed: true, workflowStep: "resume" }),
  editJobSelection: () => set({ jobConfirmed: false, workflowStep: "job" }),

  setActiveJob: (job) => set({ activeJob: job, isCustomJob: false }),
  setCustomJobText: (text) => set({ customJobText: text }),
  setCustomJobTitle: (title) => set({ customJobTitle: title }),
  setCustomJobCompany: (company) => set({ customJobCompany: company }),
  setIsCustomJob: (isCustom) => set({ isCustomJob: isCustom }),

  setResumeFile: (file) =>
    set({
      resumeFile: file,
      resumeFileName: file ? file.name : "",
      errorMessage: null,
    }),

  setAnalysisStep: (step, message = "", progress) =>
    set((state) => ({
      analysisStep: step,
      currentStepMessage: message || state.currentStepMessage,
      analysisProgress:
        progress !== undefined
          ? progress
          : step === "uploading"
          ? 20
          : step === "parsing"
          ? 50
          : step === "matching"
          ? 75
          : step === "optimizing"
          ? 90
          : step === "completed"
          ? 100
          : state.analysisProgress,
    })),

  setPartialProfile: (profile) =>
    set((state) => ({
      isHydrating: true,
      workflowStep: "results",
      analysisStep: "parsing",
      analysisProgress: 45,
      currentStepMessage: "Profile extracted. Computing ATS alignment...",
      analysisResult: {
        status: "partial",
        ats_score: 0,
        passed_threshold: false,
        parsed_profile: profile,
        match_result: {
          overall_score: 0,
          vector_similarity_score: 0,
          skill_match_score: 0,
          experience_score: 0,
          matched_skills: [],
          missing_skills: [],
          experience_years_required: state.activeJob?.min_years_experience || 2.0,
          experience_years_actual: profile.total_years_experience,
          match_summary: "Calculating real-world vector and skill match alignment...",
        },
        bullet_improvements: [],
        interview_tips: [],
        agent_logs: ["Candidate profile extracted."],
      },
    })),

  setPartialMatch: (matchResult, atsScore) =>
    set((state) => ({
      analysisStep: "matching",
      analysisProgress: 75,
      currentStepMessage: "ATS match computed. Generating Google XYZ STAR bullet rewrites...",
      analysisResult: state.analysisResult
        ? {
            ...state.analysisResult,
            ats_score: atsScore,
            passed_threshold: atsScore >= 80.0,
            match_result: matchResult,
          }
        : null,
    })),

  setPartialImprovements: (bulletImprovements, interviewTips) =>
    set((state) => ({
      analysisStep: "optimizing",
      analysisProgress: 95,
      currentStepMessage: "Finalizing evaluation report...",
      analysisResult: state.analysisResult
        ? {
            ...state.analysisResult,
            bullet_improvements: bulletImprovements,
            interview_tips: interviewTips,
          }
        : null,
    })),

  setAnalysisResult: (result) =>
    set({
      analysisResult: result,
      isHydrating: false,
      analysisStep: "completed",
      workflowStep: "results",
      analysisProgress: 100,
      currentStepMessage: "Analysis Complete",
      errorMessage: null,
      activeTab: "overview",
    }),

  setErrorMessage: (msg) =>
    set({
      errorMessage: msg,
      analysisStep: msg ? "error" : "idle",
      isHydrating: false,
    }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setSidebarOpen: (open) => set({ isSidebarOpen: open }),
  setHistoryItems: (items) => set({ historyItems: items }),
  setIsHistoryLoading: (loading) => set({ isHistoryLoading: loading }),

  loadPastReport: (report, roleTitle) =>
    set({
      analysisResult: report,
      workflowStep: "results",
      analysisStep: "completed",
      analysisProgress: 100,
      errorMessage: null,
      activeTab: "overview",
      jobConfirmed: true,
      isHydrating: false,
      customJobTitle: roleTitle || report.match_result?.match_summary?.slice(0, 30) || "Saved Role",
    }),

  resetToNewAnalysis: () =>
    set({
      workflowStep: "job",
      jobConfirmed: false,
      resumeFile: null,
      resumeFileName: "",
      analysisStep: "idle",
      analysisProgress: 0,
      currentStepMessage: "",
      analysisResult: null,
      errorMessage: null,
      isHydrating: false,
      activeTab: "overview",
    }),
}));
