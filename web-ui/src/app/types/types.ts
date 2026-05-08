export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
  result?: string;
  status: "pending" | "completed" | "error" | "interrupted";
}

export interface SubAgent {
  id: string;
  name: string;
  subAgentName: string;
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
  status: "pending" | "active" | "completed" | "error";
}

export interface FileItem {
  path: string;
  content: string;
}

export interface TodoItem {
  id: string;
  content: string;
  status: "pending" | "in_progress" | "completed";
  updatedAt?: Date;
}

export type VideoMakerMilestoneStatus =
  | "pending"
  | "in_progress"
  | "interrupted"
  | "blocked"
  | "completed"
  | "failed";

export interface VideoMakerTimelineMilestone {
  id: string;
  label?: string;
  status: VideoMakerMilestoneStatus;
  blockingReason?: string | null;
  artifactPaths?: string[];
}

export interface VideoMakerArtifactLink {
  kind: string;
  path: string;
  exists?: boolean;
}

export interface VideoMakerPublishReadiness {
  status: "publish_ready" | "needs_revision" | "not_reviewed";
  reportPath?: string;
  notes?: string;
}

export interface VideoMakerUiState {
  outputDir?: string;
  workflowStatus?: "in_progress" | "blocked" | "completed" | "failed";
  milestones?: VideoMakerTimelineMilestone[];
  artifacts?: VideoMakerArtifactLink[];
  currentBlocker?: string | null;
  nextActions?: string[];
  publishReadiness?: VideoMakerPublishReadiness;
}

export interface Thread {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface InterruptData {
  value: any;
  ns?: string[];
  scope?: string;
}

export interface ActionRequest {
  name: string;
  args: Record<string, unknown>;
  description?: string;
}

export interface ReviewConfig {
  actionName: string;
  action_name?: string;
  allowedDecisions?: string[];
  allowed_decisions?: string[];
}

export interface ToolApprovalInterruptData {
  action_requests: ActionRequest[];
  review_configs?: ReviewConfig[];
}

export interface ThinkingBlock {
  /** Raw reasoning text from Anthropic extended thinking content block */
  thinking: string;
}
