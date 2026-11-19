import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    const baseStyles =
      "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#7C0E44] disabled:pointer-events-none disabled:opacity-50 cursor-pointer";

    const variantStyles = {
      default: "bg-[#7C0E44] text-white shadow-xs hover:bg-[#600B35] active:bg-[#4E082B]",
      destructive: "bg-rose-700 text-white shadow-xs hover:bg-rose-800",
      outline: "border border-[#D49A9A]/60 bg-white text-[#7C0E44] hover:bg-[#F2DACE]/30 shadow-xs",
      secondary: "bg-[#F2DACE]/60 text-[#7C0E44] border border-[#D49A9A]/40 shadow-xs hover:bg-[#F2DACE]",
      ghost: "text-slate-700 hover:bg-[#F2DACE]/30 hover:text-[#7C0E44]",
      link: "text-[#7C0E44] underline-offset-4 hover:underline",
    };

    const sizeStyles = {
      default: "h-9 px-4 py-2",
      sm: "h-8 rounded-md px-3 text-xs",
      lg: "h-11 rounded-xl px-6 text-sm",
      icon: "h-9 w-9",
    };

    return (
      <button
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
