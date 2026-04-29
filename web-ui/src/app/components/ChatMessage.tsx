"use client";

import React, { useMemo, useState, useCallback } from "react";
import { SubAgentIndicator } from "@/app/components/SubAgentIndicator";
import { ToolCallBox } from "@/app/components/ToolCallBox";
import { MarkdownContent } from "@/app/components/MarkdownContent";
import { ThinkingBlock } from "@/app/components/ThinkingBlock";
import type {
  SubAgent,
  ToolCall,
  ActionRequest,
  ReviewConfig,
} from "@/app/types/types";
import { Message } from "@langchain/langgraph-sdk";
import {
  extractSubAgentContent,
  extractStringFromMessageContent,
  extractThinkingBlocks,
} from "@/app/utils/utils";
import { cn } from "@/lib/utils";

const SUBAGENT_CONTENT_LIMIT = 200;

function truncateContent(
  text: string,
  limit: number
): { text: string; truncated: boolean } {
  if (text.length <= limit) return { text, truncated: false };
  return { text: text.slice(0, limit).trimEnd() + "\u2026", truncated: true };
}

interface ChatMessageProps {
  message: Message;
  toolCalls: ToolCall[];
  isLoading?: boolean;
  isStreaming?: boolean;
  actionRequestsMap?: Map<string, ActionRequest>;
  reviewConfigsMap?: Map<string, ReviewConfig>;
  ui?: any[];
  stream?: any;
  onResumeInterrupt?: (value: any) => void;
  graphId?: string;
}

export const ChatMessage = React.memo<ChatMessageProps>(
  ({
    message,
    toolCalls,
    isLoading,
    isStreaming,
    actionRequestsMap,
    reviewConfigsMap,
    ui,
    stream,
    onResumeInterrupt,
    graphId,
  }) => {
    const isUser = message.type === "human";
    const messageContent = extractStringFromMessageContent(message);
    const hasContent = messageContent && messageContent.trim() !== "";
    const hasToolCalls = toolCalls.length > 0;

    const thinkingBlocks = useMemo(
      () => (!isUser ? extractThinkingBlocks(message) : []),
      [message, isUser]
    );

    const subAgents = useMemo(() => {
      return toolCalls
        .filter((toolCall: ToolCall) => {
          return (
            toolCall.name === "task" &&
            toolCall.args["subagent_type"] &&
            toolCall.args["subagent_type"] !== "" &&
            toolCall.args["subagent_type"] !== null
          );
        })
        .map((toolCall: ToolCall) => {
          const subagentType = (toolCall.args as Record<string, unknown>)[
            "subagent_type"
          ] as string;
          return {
            id: toolCall.id,
            name: toolCall.name,
            subAgentName: subagentType,
            input: toolCall.args,
            output: toolCall.result ? { result: toolCall.result } : undefined,
            status: toolCall.status,
          } as SubAgent;
        });
    }, [toolCalls]);

    const [expandedSubAgents, setExpandedSubAgents] = useState<
      Record<string, boolean>
    >({});
    // Default collapsed — user expands on demand
    const isSubAgentExpanded = useCallback(
      (id: string) => expandedSubAgents[id] ?? false,
      [expandedSubAgents]
    );
    const toggleSubAgent = useCallback((id: string) => {
      setExpandedSubAgents((prev) => ({
        ...prev,
        [id]: !(prev[id] ?? false),
      }));
    }, []);

    // Per-subagent "show full" state for input / output
    const [showFullContent, setShowFullContent] = useState<
      Record<string, { input?: boolean; output?: boolean }>
    >({});
    const toggleShowFull = useCallback(
      (id: string, field: "input" | "output") => {
        setShowFullContent((prev) => ({
          ...prev,
          [id]: { ...prev[id], [field]: !prev[id]?.[field] },
        }));
      },
      []
    );

    return (
      <div
        className={cn(
          "flex w-full max-w-full overflow-x-hidden",
          isUser && "flex-row-reverse"
        )}
      >
        <div
          className={cn(
            "min-w-0 max-w-full",
            isUser ? "max-w-[70%]" : "w-full"
          )}
        >
          {/* Thinking / reasoning blocks (Anthropic extended thinking) */}
          {!isUser && thinkingBlocks.length > 0 && (
            <ThinkingBlock
              blocks={thinkingBlocks}
              isActive={isStreaming === true && !hasContent}
            />
          )}

          {(hasContent || isStreaming) && (
            <div className={cn("relative flex items-end gap-0")}>
              <div
                className={cn(
                  "mt-4 overflow-hidden break-words text-sm font-normal leading-[150%]",
                  isUser
                    ? "rounded-xl rounded-br-none border border-border px-3 py-2 text-foreground"
                    : "text-primary"
                )}
                style={
                  isUser
                    ? { backgroundColor: "var(--color-user-message-bg)" }
                    : undefined
                }
              >
                {isUser ? (
                  <p className="m-0 whitespace-pre-wrap break-words text-sm leading-relaxed">
                    {messageContent}
                  </p>
                ) : hasContent ? (
                  <span className="relative">
                    <MarkdownContent content={messageContent} />
                    {isStreaming && !hasToolCalls && (
                      <span
                        className="ml-0.5 inline-block h-[1em] w-[2px] animate-pulse bg-current align-text-bottom opacity-70"
                        aria-hidden="true"
                      />
                    )}
                  </span>
                ) : isStreaming ? (
                  <span className="flex items-center gap-1.5 text-muted-foreground">
                    <span className="flex gap-1">
                      <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:0ms]" />
                      <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:150ms]" />
                      <span className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:300ms]" />
                    </span>
                  </span>
                ) : null}
              </div>
            </div>
          )}
          {hasToolCalls && (
            <div className="mt-2 flex w-full flex-col gap-1">
              {toolCalls.map((toolCall: ToolCall) => {
                if (toolCall.name === "task") return null;
                const toolCallGenUiComponent = ui?.find(
                  (u) => u.metadata?.tool_call_id === toolCall.id
                );
                const actionRequest = actionRequestsMap?.get(toolCall.name);
                const reviewConfig = reviewConfigsMap?.get(toolCall.name);
                return (
                  <ToolCallBox
                    key={toolCall.id}
                    toolCall={toolCall}
                    uiComponent={toolCallGenUiComponent}
                    stream={stream}
                    graphId={graphId}
                    actionRequest={actionRequest}
                    reviewConfig={reviewConfig}
                    onResume={onResumeInterrupt}
                    isLoading={isLoading}
                  />
                );
              })}
            </div>
          )}
          {!isUser && subAgents.length > 0 && (
            <div className="mt-2 flex w-fit max-w-full flex-col gap-2">
              {subAgents.map((subAgent) => {
                const inputText = extractSubAgentContent(subAgent.input);
                const outputText = subAgent.output
                  ? extractSubAgentContent(subAgent.output)
                  : null;
                const showFullInput =
                  showFullContent[subAgent.id]?.input ?? false;
                const showFullOutput =
                  showFullContent[subAgent.id]?.output ?? false;
                const { text: inputPreview, truncated: inputTruncated } =
                  truncateContent(inputText, SUBAGENT_CONTENT_LIMIT);
                const { text: outputPreview, truncated: outputTruncated } =
                  outputText
                    ? truncateContent(outputText, SUBAGENT_CONTENT_LIMIT)
                    : { text: "", truncated: false };

                return (
                  <div key={subAgent.id} className="flex w-full flex-col gap-1">
                    <SubAgentIndicator
                      subAgent={subAgent}
                      onClick={() => toggleSubAgent(subAgent.id)}
                      isExpanded={isSubAgentExpanded(subAgent.id)}
                    />

                    {isSubAgentExpanded(subAgent.id) && (
                      <div className="ml-1 w-full max-w-full">
                        <div className="rounded-md border border-border bg-muted/30 p-3 text-sm">
                          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                            Input
                          </p>
                          <div className="mb-3 text-foreground/80">
                            <MarkdownContent
                              content={showFullInput ? inputText : inputPreview}
                            />
                            {inputTruncated && (
                              <button
                                onClick={() =>
                                  toggleShowFull(subAgent.id, "input")
                                }
                                className="mt-1 text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
                              >
                                {showFullInput ? "Show less" : "Show more"}
                              </button>
                            )}
                          </div>

                          {outputText && (
                            <>
                              <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                                Output
                              </p>
                              <div className="text-foreground/80">
                                <MarkdownContent
                                  content={
                                    showFullOutput ? outputText : outputPreview
                                  }
                                />
                                {outputTruncated && (
                                  <button
                                    onClick={() =>
                                      toggleShowFull(subAgent.id, "output")
                                    }
                                    className="mt-1 text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
                                  >
                                    {showFullOutput ? "Show less" : "Show more"}
                                  </button>
                                )}
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    );
  }
);

ChatMessage.displayName = "ChatMessage";
