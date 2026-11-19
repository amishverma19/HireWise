import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantStyles = {
    default: "border-transparent bg-[#7C0E44] text-white hover:bg-[#600B35]",
    secondary: "border-[#D49A9A]/40 bg-[#F2DACE]/50 text-[#7C0E44]",
    destructive: "border-rose-200 bg-rose-50 text-rose-800",
    success: "border-[#D49A9A]/50 bg-[#F2DACE]/60 text-[#7C0E44] font-semibold",
    warning: "border-[#D49A9A]/40 bg-[#FAF4F0] text-[#AA5E7A] font-semibold",
    outline: "text-slate-700 border border-[#D49A9A]/60 bg-white hover:bg-[#F2DACE]/20",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[#7C0E44]",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  );
}

export { Badge };
