"use client";

import React, { useEffect, useState } from "react";
import {
  FileText,
  FileCheck2,
  Clock,
  ChevronLeft,
  ChevronRight,
  PlusCircle,
  Trash2,
  Briefcase,
  Layers,
  History,
  LogIn,
  LogOut,
  User,
} from "lucide-react";
import { fetchCurrentUser, fetchHistory, fetchHistoryDetail, deleteHistoryRecord, HistoryItem } from "@/lib/api";
import { useResumeStore } from "@/store/useResumeStore";

export function HistorySidebar() {
  const {
    isSidebarOpen,
    toggleSidebar,
    historyItems,
    setHistoryItems,
    isHistoryLoading,
    setIsHistoryLoading,
    loadPastReport,
    resetToNewAnalysis,
    analysisResult,
    user,
    setUser,
    logout,
    setAuthModalOpen,
  } = useResumeStore();

  const [loadingDetailId, setLoadingDetailId] = useState<string | null>(null);

  useEffect(() => {
    async function initUserAndHistory() {
      try {
        const currentUser = await fetchCurrentUser();
        if (currentUser) {
          setUser(currentUser);
          setIsHistoryLoading(true);
          const data = await fetchHistory(25);
          setHistoryItems(data);
        } else {
          setHistoryItems([]);
        }
      } catch (err) {
        console.error("Failed to load user or history:", err);
      } finally {
        setIsHistoryLoading(false);
      }
    }
    initUserAndHistory();
  }, []);

  const handleSelectRecord = async (item: HistoryItem) => {
    try {
      setLoadingDetailId(item.id);
      const report = await fetchHistoryDetail(item.id);
      loadPastReport(report, item.target_role);
    } catch (err) {
      console.error("Error loading past report:", err);
    } finally {
      setLoadingDetailId(null);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await deleteHistoryRecord(id);
      setHistoryItems(historyItems.filter((h) => h.id !== id));
    } catch (err) {
      console.error("Error deleting record:", err);
    }
  };

  return (
    <>
      {/* Desktop Sticky Left Sidebar */}
      <aside
        className={`bg-white border-r border-[#D49A9A]/40 transition-all duration-300 flex flex-col shrink-0 z-40 sticky top-0 h-screen ${
          isSidebarOpen ? "w-72" : "w-16"
        }`}
      >
        {/* Top Header / Branding */}
        <div className="h-16 px-4 border-b border-[#D49A9A]/30 flex items-center justify-between shrink-0">
          {isSidebarOpen ? (
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#7C0E44] text-white flex items-center justify-center font-bold shadow-xs shrink-0">
                <FileCheck2 className="w-4.5 h-4.5" />
              </div>
              <div>
                <h1 className="text-sm font-bold text-[#7C0E44] tracking-tight">HireWise</h1>
                <p className="text-[10px] text-[#AA5E7A] font-medium">Resume Evaluator</p>
              </div>
            </div>
          ) : (
            <div className="w-8 h-8 rounded-xl bg-[#7C0E44] text-white flex items-center justify-center font-bold shadow-xs mx-auto">
              <FileCheck2 className="w-4.5 h-4.5" />
            </div>
          )}

          <button
            type="button"
            onClick={toggleSidebar}
            className="p-1.5 rounded-lg text-[#AA5E7A] hover:bg-[#F2DACE]/40 hover:text-[#7C0E44] transition-colors"
            title={isSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          >
            {isSidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>

        {/* New Evaluation Action Button */}
        <div className="p-3 border-b border-[#D49A9A]/30 shrink-0">
          <button
            type="button"
            onClick={resetToNewAnalysis}
            className={`w-full py-2 px-3 rounded-lg bg-[#7C0E44] hover:bg-[#600B35] text-white text-xs font-semibold flex items-center justify-center gap-2 transition-all shadow-xs ${
              !isSidebarOpen && "px-0"
            }`}
            title="Start New Assessment"
          >
            <PlusCircle className="w-4 h-4 shrink-0" />
            {isSidebarOpen && <span>New Evaluation</span>}
          </button>
        </div>

        {/* History List Section (Independent Scroll Container) */}
        <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-2 overscroll-contain">
          {isSidebarOpen && (
            <div className="flex items-center justify-between px-1 mb-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#7C0E44] flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-[#AA5E7A]" />
                Evaluation History
              </span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-[#F2DACE] text-[#7C0E44] font-bold">
                {historyItems.length}
              </span>
            </div>
          )}

          {!user ? (
            /* Unauthenticated Prompt */
            isSidebarOpen ? (
              <div className="p-4 rounded-xl border border-[#D49A9A]/40 bg-[#FAF4F0]/60 text-center space-y-2 mt-2">
                <User className="w-6 h-6 text-[#AA5E7A] mx-auto" />
                <p className="text-xs font-bold text-[#7C0E44]">Sign In to Save History</p>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  Sign in or register to securely access and manage your past evaluations.
                </p>
                <button
                  type="button"
                  onClick={() => setAuthModalOpen(true, "login")}
                  className="w-full py-1.5 rounded-lg bg-[#7C0E44] text-white text-xs font-semibold shadow-xs hover:bg-[#600B35] transition-colors"
                >
                  Sign In / Register
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setAuthModalOpen(true, "login")}
                className="w-full py-2 flex justify-center text-[#7C0E44] hover:bg-[#F2DACE]/30 rounded-lg"
                title="Sign In"
              >
                <LogIn className="w-4 h-4" />
              </button>
            )
          ) : isHistoryLoading ? (
            <div className="space-y-2 pt-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-14 rounded-lg bg-[#F2DACE]/20 animate-pulse border border-[#D49A9A]/20" />
              ))}
            </div>
          ) : historyItems.length === 0 ? (
            isSidebarOpen && (
              <div className="p-4 text-center text-xs text-slate-500 rounded-lg border border-dashed border-[#D49A9A]/40 my-4">
                <p className="font-semibold text-slate-700">No evaluations yet.</p>
                <p className="text-[11px] mt-1 text-slate-500">
                  Select a job and upload your resume to see your first report here.
                </p>
              </div>
            )
          ) : (
            historyItems.map((item) => {
              const score = item.ats_score || 0;
              let scoreColor = "bg-[#7C0E44] text-white";
              if (score < 60) {
                scoreColor = "bg-[#D49A9A] text-[#7C0E44]";
              } else if (score < 80) {
                scoreColor = "bg-[#AA5E7A] text-white";
              }

              if (!isSidebarOpen) {
                return (
                  <button
                    key={item.id}
                    onClick={() => handleSelectRecord(item)}
                    className="w-full flex flex-col items-center py-2 px-1 rounded-lg hover:bg-[#F2DACE]/30 transition-colors border border-transparent hover:border-[#D49A9A]/40"
                    title={`${item.full_name} — ${item.target_role} (${score}%)`}
                  >
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${scoreColor}`}>
                      {score.toFixed(0)}%
                    </span>
                  </button>
                );
              }

              return (
                <div
                  key={item.id}
                  onClick={() => handleSelectRecord(item)}
                  className="group relative rounded-xl p-3 bg-white border border-[#D49A9A]/30 hover:border-[#7C0E44] hover:bg-[#FAF4F0]/50 cursor-pointer transition-all shadow-2xs"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-bold text-[#7C0E44] truncate">
                        {item.full_name || "Candidate"}
                      </p>
                      <p className="text-[11px] text-slate-600 truncate flex items-center gap-1 mt-0.5">
                        <Briefcase className="w-3 h-3 text-[#AA5E7A] shrink-0" />
                        <span className="truncate">{item.target_role || "Position"}</span>
                      </p>
                    </div>

                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md shrink-0 ${scoreColor}`}>
                      {score.toFixed(0)}%
                    </span>
                  </div>

                  <div className="mt-2 pt-2 border-t border-[#D49A9A]/20 flex items-center justify-between text-[10px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-[#D49A9A]" />
                      {item.created_at}
                    </span>

                    <button
                      type="button"
                      onClick={(e) => handleDelete(e, item.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-600 rounded transition-all"
                      title="Delete record"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* User Card / Auth Footer */}
        {user ? (
          <div className="p-3 border-t border-[#D49A9A]/30 bg-[#FAF8F7] shrink-0">
            {isSidebarOpen ? (
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold text-[#7C0E44] truncate">{user.full_name || user.email.split("@")[0]}</p>
                  <p className="text-[10px] text-slate-500 truncate">{user.email}</p>
                </div>
                <button
                  type="button"
                  onClick={logout}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={logout}
                className="w-full py-2 flex justify-center text-slate-400 hover:text-rose-600"
                title="Sign Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        ) : (
          isSidebarOpen && (
            <div className="p-3 border-t border-[#D49A9A]/30 text-[10px] text-[#AA5E7A] text-center shrink-0">
              <span>HireWise Platform</span>
            </div>
          )
        )}
      </aside>
    </>
  );
}
