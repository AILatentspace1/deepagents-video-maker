"use client";

import React, { useState, useEffect, useRef } from "react";
import { ChevronDown, ChevronUp, Brain, CheckCircle2 } from "lucide-react";
import { MarkdownContent } from "@/app/components/MarkdownContent";
import type { ThinkingBlock as ThinkingBlockType } from "@/app/types/types";
import { cn } from "@/lib/utils";

interface ThinkingBlockProps {
  /** All thinking content blocks from a single AI message */
  blocks: ThinkingBlockType[];
  /** True while the model is still streaming this message */
  isActive?: boolean;
}

export const ThinkingBlock = React.memo<ThinkingBlockProps>(
  ({ blocks, isActive = false }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [elapsedSeconds, setElapsedSeconds] = useState(0);
    const startTimeRef = useRef<number>(Date.now());
    const finalTimeRef = useRef<number | null>(null);

    // Run a 1-second interval while actively streaming; freeze on completion
    useEffect(() => {
      if (!isActive) {
        // Record final elapsed time once on deactivation
        if (finalTimeRef.current === null) {
          finalTimeRef.current = Math.round(
            (Date.now() - startTimeRef.current) / 1000
          );
          setElapsedSeconds(finalTimeRef.current);
        }
        return;
      }
      const id = setInterval(() => {
        setElapsedSeconds(
          Math.round((Date.now() - startTimeRef.current) / 1000)
        );
      }, 1000);
      return () => clearInterval(id);
    }, [isActive]);

    if (blocks.length === 0) return null;

    // Merge all thinking blocks into a single string
    const fullText = blocks.map((b) => b.thinking).join("\n\n");
    const displaySeconds = finalTimeRef.current ?? elapsedSeconds;

    return (
      <div className="mt-4 w-full">
        {/* Header — always visible */}
        <button
          type="button"
          onClick={() => setIsExpanded((v) => !v)}
          className={cn(
            "group flex w-fit items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm transition-colors",
            "hover:bg-accent",
            isActive
              ? "text-blue-500 dark:text-blue-400"
              : "text-muted-foreground hover:text-foreground"
          )}
          aria-expanded={isExpanded}
        >
          {isActive ? (
            <Brain
              size={14}
              className="shrink-0 animate-pulse"
              aria-hidden="true"
            />
          ) : (
            <CheckCircle2
              size={14}
              className="shrink-0 text-emerald-500"
              aria-hidden="true"
            />
          )}

          <span className={cn("font-medium", isActive && "animate-pulse")}>
            {isActive
              ? elapsedSeconds > 0
                ? `Thinking… ${elapsedSeconds}s`
                : "Thinking…"
              : `Thought for ${displaySeconds}s`}
          </span>

          {isExpanded ? (
            <ChevronUp size={12} className="shrink-0 opacity-60" />
          ) : (
            <ChevronDown size={12} className="shrink-0 opacity-60" />
          )}
        </button>

        {/* Expanded reasoning panel */}
        {isExpanded && (
          <div
            className={cn(
              "mt-1.5 rounded-lg border border-border/60 bg-muted/20 px-4 py-3",
              "max-h-[400px] overflow-y-auto"
            )}
          >
            <div className="text-xs leading-relaxed text-muted-foreground">
              <MarkdownContent content={fullText} />
            </div>

            {isActive && (
              <div className="mt-2 flex items-center gap-1.5 text-[11px] text-blue-400/70">
                <span className="flex gap-0.5">
                  <span className="inline-block h-1 w-1 animate-bounce rounded-full bg-blue-400 [animation-delay:0ms]" />
                  <span className="inline-block h-1 w-1 animate-bounce rounded-full bg-blue-400 [animation-delay:150ms]" />
                  <span className="inline-block h-1 w-1 animate-bounce rounded-full bg-blue-400 [animation-delay:300ms]" />
                </span>
                <span>Reasoning in progress…</span>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }
);

ThinkingBlock.displayName = "ThinkingBlock";
