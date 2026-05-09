export interface StandaloneConfig {
  deploymentUrl: string;
  assistantId: string;
  langsmithApiKey?: string;
}

const CONFIG_KEY = "deepagent-video-maker-config";

export const DEFAULT_CONFIG: StandaloneConfig = {
  deploymentUrl:
    process.env.NEXT_PUBLIC_LANGGRAPH_API_URL || "http://127.0.0.1:2024",
  assistantId: process.env.NEXT_PUBLIC_ASSISTANT_ID || "video-maker",
  langsmithApiKey: process.env.NEXT_PUBLIC_LANGSMITH_API_KEY || undefined,
};

export function getConfig(): StandaloneConfig | null {
  if (typeof window === "undefined") return null;

  const stored = localStorage.getItem(CONFIG_KEY);
  if (!stored) return DEFAULT_CONFIG;

  try {
    const parsed = JSON.parse(stored) as Partial<StandaloneConfig>;
    return {
      ...DEFAULT_CONFIG,
      ...parsed,
      deploymentUrl:
        typeof parsed.deploymentUrl === "string"
          ? parsed.deploymentUrl.trim() || DEFAULT_CONFIG.deploymentUrl
          : DEFAULT_CONFIG.deploymentUrl,
      assistantId:
        typeof parsed.assistantId === "string"
          ? parsed.assistantId.trim() || DEFAULT_CONFIG.assistantId
          : DEFAULT_CONFIG.assistantId,
    };
  } catch {
    return DEFAULT_CONFIG;
  }
}

export function saveConfig(config: StandaloneConfig): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
}
