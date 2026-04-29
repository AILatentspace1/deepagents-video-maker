"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, CheckCircle2, Loader2, XCircle, Circle } from "lucide-react";
import type { SubAgent } from "@/app/types/types";
import { cn } from "@/lib/utils";

interface SubAgentIndicatorProps {
  subAgent: SubAgent;
  onClick: () => void;
  isExpanded?: boolean;
}

function StatusDot({ status }: { status: SubAgent["status"] }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 size={13} className="shrink-0 text-emerald-500" />;
    case "active":
    case "pending":
      return <Loader2 size={13} className="shrink-0 animate-spin text-blue-400" />;
    case "error":
      return <XCircle size={13} className="shrink-0 text-destructive" />;
    default:
      return <Circle size={13} className="shrink-0 text-muted-foreground/60" />;
  }
}

export const SubAgentIndicator = React.memo<SubAgentIndicatorProps>(
  ({ subAgent, onClick, isExpanded = false }) => {
    return (
      <div className="w-fit max-w-[70vw] overflow-hidden rounded-lg border-none bg-card shadow-none outline-none">
        <Button
          variant="ghost"
          size="sm"
          onClick={onClick}
          className="flex w-full items-center justify-between gap-2 border-none px-3 py-1.5 text-left shadow-none outline-none transition-colors duration-200"
        >
          <div className="flex w-full items-center gap-2">
            <StatusDot status={subAgent.status as SubAgent["status"]} />
            <span className={cn(
              "font-sans text-[14px] font-semibold leading-[140%] tracking-[-0.4px]",
              subAgent.status === "completed" ? "text-foreground/70" : "text-foreground"
            )}>
              {subAgent.subAgentName}
            </span>
            {isExpanded ? (
              <ChevronUp size={12} className="ml-1 shrink-0 text-muted-foreground" />
            ) : (
              <ChevronDown size={12} className="ml-1 shrink-0 text-muted-foreground" />
            )}
          </div>
        </Button>
      </div>
    );
  }
);

SubAgentIndicator.displayName = "SubAgentIndicator";

