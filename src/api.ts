import { invoke, isTauri } from "@tauri-apps/api/core";
import type { AIModelInfo, DownloadJob, Platform, SidecarConfig, ToolInfo } from "./types";

export async function ensureBackend(): Promise<string> {
  const configured = import.meta.env.VITE_DOUYINGO_BACKEND_URL;
  if (configured) {
    return configured.replace(/\/$/, "");
  }

  if (!isTauri()) {
    return "http://127.0.0.1:8765";
  }

  try {
    const url = await invoke<string>("ensure_backend");
    return url.replace(/\/$/, "");
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`Sidecar 启动失败：${detail}`);
  }
}

async function apiFetch<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // Keep HTTP status text.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export function getHealth(baseUrl: string) {
  return apiFetch<{ ok: boolean; version: string; service: string; time: string }>(baseUrl, "/health");
}

export function getDownloads(baseUrl: string) {
  return apiFetch<DownloadJob[]>(baseUrl, "/api/downloads");
}

export function createDownload(
  baseUrl: string,
  payload: {
    text: string;
    platform: Platform;
    options: {
      quality: string;
      format: string;
      download_type: "video" | "audio" | "cover";
      save_metadata: boolean;
      ai_model_id?: string | null;
      output_dir?: string | null;
    };
  }
) {
  return apiFetch<DownloadJob>(baseUrl, "/api/downloads", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function cancelDownload(baseUrl: string, jobId: string) {
  return apiFetch<DownloadJob>(baseUrl, `/api/downloads/${jobId}/cancel`, {
    method: "POST"
  });
}

export function deleteDownload(baseUrl: string, jobId: string) {
  return apiFetch<{ deleted: boolean }>(baseUrl, `/api/downloads/${jobId}`, {
    method: "DELETE"
  });
}

export function clearCompletedDownloads(baseUrl: string) {
  return apiFetch<{ deleted: number }>(baseUrl, "/api/downloads", {
    method: "DELETE"
  });
}

export function getTools(baseUrl: string) {
  return apiFetch<ToolInfo[]>(baseUrl, "/api/tools");
}

export function getModels(baseUrl: string) {
  return apiFetch<AIModelInfo[]>(baseUrl, "/api/models");
}

export function getConfig(baseUrl: string) {
  return apiFetch<SidecarConfig>(baseUrl, "/api/config");
}

export function updateConfig(baseUrl: string, config: SidecarConfig) {
  return apiFetch<SidecarConfig>(baseUrl, "/api/config", {
    method: "PUT",
    body: JSON.stringify(config)
  });
}

export async function revealPath(path: string): Promise<void> {
  try {
    await invoke("reveal_path", { path });
  } catch {
    throw new Error("Only the Tauri desktop shell can reveal files.");
  }
}
