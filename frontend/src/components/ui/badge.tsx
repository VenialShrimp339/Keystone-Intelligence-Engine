import * as React from "react";

import { cn } from "../../lib/utils";

export function Badge({
  className,
  tone = "neutral",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & {
  tone?: "neutral" | "active" | "success" | "warning" | "danger";
}) {
  const tones = {
    neutral: "border bg-white text-muted-foreground",
    active: "border-blue-200 bg-blue-50 text-blue-800",
    success: "border-emerald-200 bg-emerald-50 text-emerald-800",
    warning: "border-amber-200 bg-amber-50 text-amber-800",
    danger: "border-red-200 bg-red-50 text-red-800",
  };
  return (
    <span
      className={cn(
        "inline-flex h-6 max-w-full items-center rounded-sm border px-2 text-xs font-medium",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}

