"use client";

import { createContext, useContext, useMemo, ReactNode } from "react";
import { Client } from "@langchain/langgraph-sdk";

interface ClientContextValue {
  client: Client;
}

const ClientContext = createContext<ClientContextValue | null>(null);

interface ClientProviderProps {
  children: ReactNode;
  deploymentUrl: string;
  apiKey: string;
}

// Stream modes supported by the langgraph-api server.
// Newer @langchain/langgraph-sdk versions may request "tools" which older
// server versions don't support — filter it out before the request goes out.
const SUPPORTED_STREAM_MODES = new Set([
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

function filterStreamModes(_url: URL, init: RequestInit): RequestInit {
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

export function ClientProvider({
  children,
  deploymentUrl,
  apiKey,
}: ClientProviderProps) {
  const client = useMemo(() => {
    return new Client({
      apiUrl: deploymentUrl,
      defaultHeaders: {
        "Content-Type": "application/json",
        "X-Api-Key": apiKey,
      },
      onRequest: filterStreamModes,
    });
  }, [deploymentUrl, apiKey]);

  const value = useMemo(() => ({ client }), [client]);

  return (
    <ClientContext.Provider value={value}>{children}</ClientContext.Provider>
  );
}

export function useClient(): Client {
  const context = useContext(ClientContext);

  if (!context) {
    throw new Error("useClient must be used within a ClientProvider");
  }
  return context.client;
}
