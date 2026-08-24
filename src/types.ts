export type Platform = "douyin" | "youtube" | "twitter" | "koushare" | "unknown";

export type JobStatus =
  | "queued"
  | "resolving"
  | "downloading"
  | "success"
  | "error"
  | "cancelled";

export interface DownloadOptions {
  quality: string;
  format: string;
  download_type: "video" | "audio" | "cover";
  output_dir?: string | null;
  save_metadata: boolean;
  ai_model_id?: string | null;
}

export interface SidecarConfig {
  output_dir?: string | null;
  save_metadata: boolean;
  ai_model_id?: string | null;
  youtube_proxy_url?: string | null;
  youtube_cookies_from_browser?: CookieSource | null;
  twitter_proxy_url?: string | null;
  twitter_cookies_from_browser?: CookieSource | null;
}

export type CookieSource = "chrome" | "edge" | "firefox" | "brave" | "chromium";

export interface DownloadedFile {
  type: string;
  path: string;
  size?: number | null;
  format?: string | null;
  ext?: string | null;
  resolution?: string | null;
  thumbnail?: string | null;
  url?: string | null;
}

export interface DownloadJob {
  id: string;
  url: string;
  platform: Platform;
  title: string;
  status: JobStatus;
  progress: number;
  message: string;
  output_dir: string;
  error?: string | null;
  downloaded_files: DownloadedFile[];
  options: DownloadOptions;
  created_at: string;
  updated_at: string;
}

export interface ToolInfo {
  name: string;
  available: boolean;
  path?: string | null;
  version?: string | null;
  details?: Record<string, unknown>;
}

export interface AIModelInfo {
  id: string;
  name: string;
  provider: string;
  path?: string | null;
  status: "available" | "missing" | "disabled";
  capabilities: string[];
}
