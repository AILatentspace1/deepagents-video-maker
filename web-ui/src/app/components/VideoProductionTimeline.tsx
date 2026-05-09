"use client";

import React, { useMemo } from "react";
import {
  AlertCircle,
  CheckCircle,
  Circle,
  Clock,
  FileText,
  PlayCircle,
} from "lucide-react";
import type {
  VideoMakerArtifactLink,
  VideoMakerTimelineMilestone,
  VideoMakerUiState,
} from "@/app/types/types";
import { cn } from "@/lib/utils";

const ORDERED_MILESTONES: VideoMakerTimelineMilestone[] = [
  { id: "source_intake", label: "Source Intake", status: "pending" },
  { id: "script", label: "Script Review", status: "pending" },
  { id: "build_scenes", label: "Build Scenes", status: "pending" },
  { id: "render_package", label: "Render Package", status: "pending" },
  { id: "publish_readiness", label: "Publish Readiness", status: "pending" },
];

const ARTIFACT_HINTS: Array<{ kind: string; pattern: RegExp }> = [
  { kind: "source_manifest", pattern: /source-manifest\.md$/ },
  { kind: "script", pattern: /script\.md$/ },
  { kind: "remotion_project", pattern: /remotion-project\/package\.json$/ },
  { kind: "final_video", pattern: /final\/video\.mp4$/ },
  { kind: "thumbnail", pattern: /final\/thumbnail\.jpg$/ },
  { kind: "publish_readiness", pattern: /publish-readiness\.md$/ },
];

function statusIcon(status: VideoMakerTimelineMilestone["status"]) {
  if (status === "completed") return <CheckCircle className="h-4 w-4 text-success/80" />;
  if (status === "in_progress") return <Clock className="h-4 w-4 text-warning/80" />;
  if (status === "blocked" || status === "failed") {
    return <AlertCircle className="h-4 w-4 text-destructive/80" />;
  }
  return <Circle className="h-4 w-4 text-tertiary/70" />;
}

function labelFor(id: string) {
  return ORDERED_MILESTONES.find((item) => item.id === id)?.label ?? id;
}

function normalizeTimeline(
  videoMaker: VideoMakerUiState | undefined,
  files: Record<string, string>
): {
  hasTimeline: boolean;
  outputDir?: string;
  milestones: VideoMakerTimelineMilestone[];
  artifacts: VideoMakerArtifactLink[];
  blocker?: string | null;
  nextActions: string[];
  publishStatus?: string;
} {
  const fileArtifacts = Object.keys(files).flatMap((path) => {
    const normalized = path.replaceAll("\\", "/");
    const match = ARTIFACT_HINTS.find((hint) => hint.pattern.test(normalized));
    return match ? [{ kind: match.kind, path, exists: true }] : [];
  });
  const explicitArtifacts = videoMaker?.artifacts ?? [];
  const artifacts = explicitArtifacts.length > 0 ? explicitArtifacts : fileArtifacts;
  const byId = new Map((videoMaker?.milestones ?? []).map((item) => [item.id, item]));
  const milestones = ORDERED_MILESTONES.map((fallback) => {
    const explicit = byId.get(fallback.id);
    if (explicit) {
      return { ...fallback, ...explicit, label: explicit.label ?? fallback.label };
    }
    return fallback;
  });
  const hasTimeline =
    Boolean(videoMaker?.outputDir) ||
    (videoMaker?.milestones?.length ?? 0) > 0 ||
    artifacts.length > 0;
  return {
    hasTimeline,
    outputDir: videoMaker?.outputDir,
    milestones,
    artifacts,
    blocker: videoMaker?.currentBlocker,
    nextActions: videoMaker?.nextActions ?? [],
    publishStatus: videoMaker?.publishReadiness?.status,
  };
}

export function VideoProductionTimeline({
  videoMaker,
  files,
}: {
  videoMaker?: VideoMakerUiState;
  files: Record<string, string>;
}) {
  const view = useMemo(() => normalizeTimeline(videoMaker, files), [videoMaker, files]);

  if (!view.hasTimeline) return null;

  return (
    <section className="mb-4 rounded-xl border border-border bg-sidebar p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold">Video production timeline</h2>
          <p className="text-xs text-muted-foreground">
            Source → Script review → Build → Render → Publish readiness
          </p>
        </div>
        {view.outputDir && (
          <span className="max-w-[420px] truncate rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
            {view.outputDir}
          </span>
        )}
      </div>

      <div className="grid gap-2 md:grid-cols-5">
        {view.milestones.map((milestone) => (
          <div
            key={milestone.id}
            className={cn(
              "rounded-lg border border-border bg-background p-3",
              milestone.status === "completed" && "border-success/30",
              milestone.status === "blocked" && "border-destructive/30",
              milestone.status === "failed" && "border-destructive/30"
            )}
          >
            <div className="flex items-center gap-2">
              {statusIcon(milestone.status)}
              <span className="truncate text-xs font-medium">{milestone.label ?? labelFor(milestone.id)}</span>
            </div>
            <div className="mt-1 text-[11px] text-muted-foreground">{milestone.status}</div>
            {milestone.blockingReason && (
              <div className="mt-2 text-[11px] text-destructive">{milestone.blockingReason}</div>
            )}
          </div>
        ))}
      </div>

      {(view.blocker || view.nextActions.length > 0 || view.publishStatus) && (
        <div className="mt-3 rounded-lg bg-muted p-3 text-xs">
          {view.blocker && <div className="text-destructive">Blocked: {view.blocker}</div>}
          {view.publishStatus && <div>Publish readiness: {view.publishStatus}</div>}
          {view.nextActions.length > 0 && (
            <ul className="mt-1 list-disc pl-5 text-muted-foreground">
              {view.nextActions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {view.artifacts.length > 0 && (
        <div className="mt-3 grid gap-2 md:grid-cols-3">
          {view.artifacts.map((artifact) => (
            <div
              key={`${artifact.kind}:${artifact.path}`}
              className="flex min-w-0 items-center gap-2 rounded-md border border-border bg-background px-2 py-2 text-xs"
            >
              {artifact.kind === "final_video" ? (
                <PlayCircle className="h-4 w-4 flex-shrink-0 text-success/80" />
              ) : (
                <FileText className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
              )}
              <div className="min-w-0">
                <div className="font-medium">{artifact.kind}</div>
                <div className="truncate text-muted-foreground" title={artifact.path}>
                  {artifact.path}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
