"use client";

import React, { useState } from "react";
import { X, Lock, Mail, User, AlertCircle, CheckCircle2, ArrowRight, KeyRound, Eye, EyeOff } from "lucide-react";
import { useResumeStore } from "@/store/useResumeStore";
import { forgotPassword, loginUser, registerUser, resetPassword, verifyResetCode } from "@/lib/api";

export function AuthModal() {
  const { isAuthModalOpen, setAuthModalOpen, authModalMode, setUser, setHistoryItems } = useResumeStore();

  const [mode, setMode] = useState<"login" | "register" | "forgot">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [forgotStep, setForgotStep] = useState<1 | 2 | 3>(1);
  const [devCode, setDevCode] = useState<string | null>(null);
  const [resendCooldown, setResendCooldown] = useState(0);

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [userNotFound, setUserNotFound] = useState(false);

  // Sync mode from store when modal opens
  React.useEffect(() => {
    if (isAuthModalOpen) {
      setMode(authModalMode);
      setErrorMsg(null);
      setSuccessMsg(null);
      setUserNotFound(false);
      setDevCode(null);
      setForgotStep(1);
      setResendCooldown(0);
    }
  }, [isAuthModalOpen, authModalMode]);

  // Resend OTP countdown timer
  React.useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setInterval(() => {
      setResendCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [resendCooldown]);

  if (!isAuthModalOpen) return null;

  const handleClose = () => {
    setAuthModalOpen(false);
    setErrorMsg(null);
    setSuccessMsg(null);
    setDevCode(null);
    setResendCooldown(0);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setLoading(true);
    try {
      const res = await loginUser(email, password);
      setUser(res.user, res.token);
      handleClose();
      // Reload history for this user
      window.location.reload();
    } catch (err: any) {
      setErrorMsg(err.message || "Invalid email or password.");
      setSuccessMsg(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setLoading(true);
    try {
      const res = await registerUser(email, password, fullName);
      setUser(res.user, res.token);
      handleClose();
      window.location.reload();
    } catch (err: any) {
      setErrorMsg(err.message || "Registration failed.");
      setSuccessMsg(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestResetCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setUserNotFound(false);
    setDevCode(null);
    setLoading(true);
    try {
      const res = await forgotPassword(email);
      if (res.dev_code) {
        setDevCode(res.dev_code);
        setResetCode(res.dev_code);
        setSuccessMsg(`Verification code: ${res.dev_code} (Auto-filled below for testing)`);
      } else {
        setSuccessMsg(`Verification code sent to ${email}. Please check your inbox.`);
      }
      setResendCooldown(60);
      setForgotStep(2);
    } catch (err: any) {
      let msg = err.message || "Email not registered.";
      if (msg === "Failed to fetch") {
        msg = "Unable to connect to server. Please ensure the backend is running.";
      }
      setErrorMsg(msg);
      setSuccessMsg(null);
      if (msg.toLowerCase().includes("no account found") || msg.toLowerCase().includes("not registered")) {
        setUserNotFound(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (resendCooldown > 0 || loading) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    setLoading(true);
    try {
      const res = await forgotPassword(email);
      if (res.dev_code) {
        setDevCode(res.dev_code);
        setResetCode(res.dev_code);
        setSuccessMsg(`New code: ${res.dev_code} (Auto-filled below for testing)`);
      } else {
        setSuccessMsg(`New verification code sent to ${email}. Please check your inbox.`);
      }
      setResendCooldown(60);
    } catch (err: any) {
      let msg = err.message || "Failed to resend verification code.";
      if (msg === "Failed to fetch") {
        msg = "Unable to connect to server. Please try again in a moment.";
      }
      setErrorMsg(msg);
      setSuccessMsg(null);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setLoading(true);
    try {
      await verifyResetCode(email, resetCode);
      setSuccessMsg("Code verified! Please set your new password below.");
      setForgotStep(3);
    } catch (err: any) {
      setErrorMsg(err.message || "Invalid or expired verification code.");
      setSuccessMsg(null);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setLoading(true);
    try {
      const res = await resetPassword(email, resetCode, newPassword);
      setSuccessMsg("Password reset successfully! You may now sign in.");
      setTimeout(() => {
        setMode("login");
        setSuccessMsg(null);
      }, 1500);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to reset password.");
      setSuccessMsg(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in-50 duration-200">
      <div className="bg-white rounded-2xl border border-[#D49A9A]/50 shadow-xl w-full max-w-md overflow-hidden relative">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-[#D49A9A]/30">
          <div>
            <h3 className="text-lg font-bold text-[#7C0E44]">
              {mode === "login" && "Sign In to HireWise"}
              {mode === "register" && "Create Your Account"}
              {mode === "forgot" && "Reset Password"}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {mode === "login" && "Access your saved evaluations and resume history."}
              {mode === "register" && "Save your resume evaluations securely in your account."}
              {mode === "forgot" && "Recover access to your account."}
            </p>
          </div>

          <button
            type="button"
            onClick={handleClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-[#F2DACE]/30 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <div className="p-6 space-y-4">
          {errorMsg ? (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
              <div>
                <p>{errorMsg}</p>
                {userNotFound && (
                  <button
                    type="button"
                    onClick={() => {
                      setMode("register");
                      setErrorMsg(null);
                      setSuccessMsg(null);
                      setUserNotFound(false);
                    }}
                    className="mt-1 text-xs font-bold text-[#7C0E44] underline flex items-center gap-1"
                  >
                    <span>Click here to create an account</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>
          ) : successMsg ? (
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>{successMsg}</span>
            </div>
          ) : null}

          {/* Mode 1: LOGIN */}
          {mode === "login" && (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-[#7C0E44] block mb-1">Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-[#D49A9A]/60 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-[#7C0E44]"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-bold text-[#7C0E44]">Password</label>
                  <button
                    type="button"
                    onClick={() => {
                      setMode("forgot");
                      setErrorMsg(null);
                      setSuccessMsg(null);
                    }}
                    className="text-[11px] font-semibold text-[#AA5E7A] hover:text-[#7C0E44]"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-9 pr-10 py-2 rounded-lg border border-[#D49A9A]/60 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-[#7C0E44]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#7C0E44] transition-colors p-0.5 cursor-pointer"
                    title={showPassword ? "Hide password" : "Show password"}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 rounded-lg bg-[#7C0E44] hover:bg-[#600B35] disabled:opacity-50 text-white font-semibold text-xs shadow-xs transition-colors flex items-center justify-center gap-1.5"
              >
                {loading ? "Signing In..." : "Sign In"}
              </button>

              <div className="text-center pt-2 border-t border-[#D49A9A]/30">
                <p className="text-xs text-slate-600">
                  Don&apos;t have an account?{" "}
                  <button
                    type="button"
                    onClick={() => {
                      setMode("register");
                      setErrorMsg(null);
                      setSuccessMsg(null);
                    }}
                    className="font-bold text-[#7C0E44] hover:underline"
                  >
                    Create Account
                  </button>
                </p>
              </div>
            </form>
          )}

          {/* Mode 2: REGISTER */}
          {mode === "register" && (
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-[#7C0E44] block mb-1">Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Alex Morgan"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-[#D49A9A]/60 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-[#7C0E44]"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-[#7C0E44] block mb-1">Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-[#D49A9A]/60 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-[#7C0E44]"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-[#7C0E44] block mb-1">Password (min 6 chars)</label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    minLength={6}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-9 pr-10 py-2 rounded-lg border border-[#D49A9A]/60 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-[#7C0E44]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#7C0E44] transition-colors p-0.5 cursor-pointer"
                    title={showPassword ? "Hide password" : "Show password"}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 rounded-lg bg-[#7C0E44] hover:bg-[#600B35] disabled:opacity-50 text-white font-semibold text-xs shadow-xs transition-colors flex items-center justify-center gap-1.5"
              >
                {loading ? "Creating Account..." : "Create Account"}
              </button>

              <div className="text-center pt-2 border-t border-[#D49A9A]/30">
                <p className="text-xs text-slate-600">
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => {
                      setMode("login");
                      setErrorMsg(null);
                      setSuccessMsg(null);
                    }}
                    className="font-bold text-[#7C0E44] hover:underline"
                  >
                    Sign In
                  </button>
                </p>
              </div>
            </form>
          )}

          {/* Mode 3: FORGOT PASSWORD */}
          {mode === "forgot" && (
            <div className="space-y-4">
              {forgotStep === 1 && (
                <form onSubmit={handleRequestResetCode} className="space-y-4">
                  <div>
                    <label className="text-xs font-bold text-[#7C0E44] block mb-1">Registered Email</label>
                    <div className="relative">
                      <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        className="w-full pl-9 pr-3 py-2 rounded-lg border border-[#D49A9A]/60 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-[#7C0E44]"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 rounded-lg bg-[#7C0E44] hover:bg-[#600B35] disabled:opacity-50 text-white font-semibold text-xs shadow-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    {loading ? "Checking..." : "Verify Email & Send Code"}
                  </button>
                </form>
              )}

              {forgotStep === 2 && (
                <form onSubmit={handleVerifyCode} className="space-y-4">
                  {devCode ? (
                    <div className="p-3.5 rounded-xl bg-amber-50/90 border border-amber-200/90 text-amber-900 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                          <span>🔑</span> Verification Code:
                        </span>
                        <span className="font-mono font-extrabold text-sm bg-white px-2.5 py-0.5 rounded-md border border-amber-300 text-[#7C0E44] tracking-widest select-all">
                          {devCode}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-amber-700 pt-0.5">
                        <span>(SMTP unconfigured in .env)</span>
                        <button
                          type="button"
                          onClick={() => setResetCode(devCode)}
                          className="font-bold text-[#7C0E44] hover:underline cursor-pointer bg-amber-100/90 px-2 py-0.5 rounded"
                        >
                          Auto-fill Code ⚡
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 rounded-lg bg-[#F2DACE]/40 border border-[#D49A9A]/30 text-[11px] text-slate-700">
                      Verification code sent to <strong className="text-[#7C0E44]">{email}</strong>. Please check your inbox.
                    </div>
                  )}

                  <div>
                    <label className="text-xs font-bold text-[#7C0E44] block mb-1">6-Digit Verification Code</label>
                    <div className="relative">
                      <KeyRound className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        type="text"
                        required
                        maxLength={6}
                        value={resetCode}
                        onChange={(e) => setResetCode(e.target.value)}
                        placeholder="123456"
                        className="w-full pl-9 pr-3 py-2 rounded-lg border border-[#D49A9A]/60 text-xs text-slate-900 tracking-widest font-mono text-center focus:outline-none focus:ring-1 focus:ring-[#7C0E44]"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading || resetCode.length < 6}
                    className="w-full py-2.5 rounded-lg bg-[#7C0E44] hover:bg-[#600B35] disabled:opacity-50 text-white font-semibold text-xs shadow-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    {loading ? "Verifying..." : "Verify Code"}
                  </button>

                  <div className="flex items-center justify-between text-xs pt-1">
                    <button
                      type="button"
                      onClick={() => {
                        setForgotStep(1);
                        setErrorMsg(null);
                        setSuccessMsg(null);
                        setDevCode(null);
                        setResetCode("");
                        setResendCooldown(0);
                      }}
                      className="text-[11px] font-semibold text-[#AA5E7A] hover:text-[#7C0E44] transition-colors"
                    >
                      &larr; Change email
                    </button>

                    <button
                      type="button"
                      disabled={resendCooldown > 0 || loading}
                      onClick={handleResendCode}
                      className={`text-[11px] font-semibold transition-colors ${
                        resendCooldown > 0 || loading
                          ? "text-slate-400 cursor-not-allowed"
                          : "text-[#7C0E44] hover:underline cursor-pointer"
                      }`}
                    >
                      {resendCooldown > 0 ? (
                        <span className="flex items-center gap-1">
                          <span className="inline-block w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse" />
                          Resend in {resendCooldown}s
                        </span>
                      ) : (
                        "Resend OTP"
                      )}
                    </button>
                  </div>
                </form>
              )}

              {forgotStep === 3 && (
                <form onSubmit={handleConfirmReset} className="space-y-4">
                  <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-800 flex items-center gap-1.5 font-medium">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Code verified! Please set your new password for <strong>{email}</strong>.</span>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-[#7C0E44] block mb-1">New Password</label>
                    <div className="relative">
                      <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        type={showNewPassword ? "text" : "password"}
                        required
                        minLength={6}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="New password (min 6 chars)"
                        className="w-full pl-9 pr-10 py-2 rounded-lg border border-[#D49A9A]/60 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-[#7C0E44]"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#7C0E44] transition-colors p-0.5 cursor-pointer"
                        title={showNewPassword ? "Hide password" : "Show password"}
                        tabIndex={-1}
                      >
                        {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading || newPassword.length < 6}
                    className="w-full py-2.5 rounded-lg bg-[#7C0E44] hover:bg-[#600B35] disabled:opacity-50 text-white font-semibold text-xs shadow-xs transition-colors flex items-center justify-center gap-1.5"
                  >
                    {loading ? "Updating..." : "Save New Password"}
                  </button>
                </form>
              )}

              <div className="text-center pt-2 border-t border-[#D49A9A]/30">
                <button
                  type="button"
                  onClick={() => {
                    setMode("login");
                    setErrorMsg(null);
                    setSuccessMsg(null);
                  }}
                  className="text-xs font-semibold text-slate-600 hover:text-[#7C0E44]"
                >
                  &larr; Back to Sign In
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

