// Shared helpers for talking to `langgraph dev` and LangSmith deployments.

// Stream modes supported by the langgraph-api server.
// Newer @langchain/langgraph-sdk versions may request "tools" which older
// server versions don't support — filter it out before the request goes out.
export const SUPPORTED_STREAM_MODES = new Set([
  "values",
  "messages",
  "updates",
  "events",
  "debug",
  "tasks",
  "checkpoints",
  "custom",
  "messages-tuple",
]);

export function filterStreamModes(_url: URL, init: RequestInit): RequestInit {
  if (typeof init.body === "string") {
    try {
      const body = JSON.parse(init.body) as Record<string, unknown>;
      if (Array.isArray(body.stream_mode)) {
        const filtered = (body.stream_mode as string[]).filter((m) =>
          SUPPORTED_STREAM_MODES.has(m)
        );
        if (filtered.length !== body.stream_mode.length) {
          return {
            ...init,
            body: JSON.stringify({ ...body, stream_mode: filtered }),
          };
        }
      }
    } catch {
      // Non-JSON body — pass through unchanged
    }
  }
  return init;
}

