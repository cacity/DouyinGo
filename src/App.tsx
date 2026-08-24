import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  BookOpen,
  Bot,
  CircleAlert,
  CircleCheck,
  CircleX,
  Clipboard,
  Cpu,
  Download,
  FolderOpen,
  LoaderCircle,
  MessageCircle,
  Music2,
  PlaySquare,
  RefreshCw,
  Settings,
  Trash2,
  Wrench
} from "lucide-react";
import {
  cancelDownload,
  createDownload,
  ensureBackend,
  getDownloads,
  getHealth,
  getModels,
  getTools,
  revealPath
} from "./api";
import type { AIModelInfo, DownloadJob, JobStatus, Platform, ToolInfo } from "./types";

const platforms: Array<{ id: Platform; label: string; icon: typeof Music2 }> = [
  { id: "douyin", label: "抖音", icon: Music2 },
  { id: "youtube", label: "YouTube", icon: PlaySquare },
  { id: "twitter", label: "Twitter/X", icon: MessageCircle },
  { id: "koushare", label: "寇享", icon: BookOpen }
];

const qualityOptions: Record<Platform, string[]> = {
  douyin: ["原画", "超清(1080p)", "高清(720p)", "标清(480p)"],
  youtube: ["最佳质量", "4K", "1440p", "1080p", "720p", "480p", "360p"],
  twitter: ["最佳质量", "1080p", "720p", "480p", "360p"],
  koushare: ["最佳质量", "1080p", "720p", "480p"],
  unknown: ["最佳质量"]
};

const statusLabels: Record<JobStatus, string> = {
  queued: "排队中",
  resolving: "解析中",
  downloading: "下载中",
  success: "已完成",
  error: "失败",
  cancelled: "已取消"
};

function App() {
  const [backendUrl, setBackendUrl] = useState("http://127.0.0.1:8765");
  const [backendState, setBackendState] = useState<"starting" | "online" | "offline">("starting");
  const [backendVersion, setBackendVersion] = useState("");
  const [platform, setPlatform] = useState<Platform>("douyin");
  const [quality, setQuality] = useState("原画");
  const [format, setFormat] = useState("MP4");
  const [downloadType, setDownloadType] = useState<"video" | "audio" | "cover">("video");
  const [input, setInput] = useState("");
  const [jobs, setJobs] = useState<DownloadJob[]>([]);
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [models, setModels] = useState<AIModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [error, setError] = useState<string>("");

  const activeJobs = useMemo(
    () => jobs.filter((job) => ["queued", "resolving", "downloading"].includes(job.status)).length,
    [jobs]
  );

  const refresh = useCallback(
    async (base = backendUrl) => {
      try {
        const [health, downloads, toolList, modelList] = await Promise.all([
          getHealth(base),
          getDownloads(base),
          getTools(base),
          getModels(base)
        ]);
        setBackendState("online");
        setBackendVersion(health.version);
        setJobs(downloads);
        setTools(toolList);
        setModels(modelList);
        setError("");
      } catch (err) {
        setBackendState("offline");
        setError(err instanceof Error ? err.message : String(err));
      }
    },
    [backendUrl]
  );

  useEffect(() => {
    let disposed = false;
    ensureBackend().then((url) => {
      if (disposed) {
        return;
      }
      setBackendUrl(url);
      refresh(url);
    });
    return () => {
      disposed = true;
    };
  }, [refresh]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      refresh().catch(() => undefined);
    }, activeJobs > 0 ? 1000 : 3000);
    return () => window.clearInterval(timer);
  }, [activeJobs, refresh]);

  useEffect(() => {
    const options = qualityOptions[platform];
    setQuality(options[0]);
  }, [platform]);

  async function pasteFromClipboard() {
    try {
      const text = await navigator.clipboard.readText();
      setInput(text.trim());
    } catch {
      setError("剪贴板读取失败，请手动粘贴链接。");
    }
  }

  async function submitDownload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!input.trim()) {
      setError("请输入或粘贴一个链接。");
      return;
    }

    try {
      await createDownload(backendUrl, {
        text: input.trim(),
        platform,
        options: {
          quality,
          format,
          download_type: downloadType,
          save_metadata: false,
          ai_model_id: selectedModel || null
        }
      });
      setInput("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function cancel(jobId: string) {
    try {
      await cancelDownload(backendUrl, jobId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <main className="appShell">
      <aside className="sidebar">
        <div className="brand">
          <Download size={22} />
          <span>DouyinGo</span>
        </div>
        <nav className="platformNav" aria-label="平台">
          {platforms.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={platform === item.id ? "active" : ""}
                type="button"
                onClick={() => setPlatform(item.id)}
                title={item.label}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="sidebarFooter">
          <Settings size={16} />
          <span>v2.0.0</span>
        </div>
      </aside>

      <section className="workspace">
        <header className="toolbar">
          <form className="downloadForm" onSubmit={submitDownload}>
            <button className="iconButton" type="button" onClick={pasteFromClipboard} title="粘贴链接">
              <Clipboard size={18} />
            </button>
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="粘贴视频分享文本或链接"
            />
            <select value={downloadType} onChange={(event) => setDownloadType(event.target.value as typeof downloadType)}>
              <option value="video">视频</option>
              <option value="audio">音频</option>
              <option value="cover">封面</option>
            </select>
            <select value={quality} onChange={(event) => setQuality(event.target.value)}>
              {qualityOptions[platform].map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <select value={format} onChange={(event) => setFormat(event.target.value)}>
              <option value="MP4">MP4</option>
              <option value="MKV">MKV</option>
              <option value="MOV">MOV</option>
            </select>
            <select value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)}>
              <option value="">AI: 无</option>
              {models
                .filter((model) => model.status === "available")
                .map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))}
            </select>
            <button className="primaryButton" type="submit">
              <Download size={18} />
              <span>开始</span>
            </button>
          </form>
          <div className={`backendPill ${backendState}`}>
            {backendState === "online" ? <CircleCheck size={16} /> : <CircleAlert size={16} />}
            <span>{backendState === "online" ? `Sidecar ${backendVersion}` : "Sidecar 离线"}</span>
          </div>
        </header>

        {error ? (
          <div className="errorBanner">
            <CircleAlert size={18} />
            <span>{error}</span>
          </div>
        ) : null}

        <div className="contentGrid">
          <section className="taskSection">
            <div className="sectionHeader">
              <h1>下载任务</h1>
              <button className="iconButton" type="button" onClick={() => refresh()} title="刷新">
                <RefreshCw size={18} />
              </button>
            </div>
            <div className="taskList">
              {jobs.length === 0 ? (
                <div className="emptyState">暂无任务</div>
              ) : (
                jobs.map((job) => (
                  <TaskRow key={job.id} job={job} onCancel={cancel} onReveal={revealPath} />
                ))
              )}
            </div>
          </section>

          <aside className="inventoryPanel">
            <PanelBlock title="工具" icon={Wrench}>
              {tools.map((tool) => (
                <InventoryRow
                  key={tool.name}
                  icon={tool.name === "python" ? Cpu : Wrench}
                  title={tool.name}
                  status={tool.available ? "可用" : "缺失"}
                  detail={tool.version || tool.path || ""}
                  ok={tool.available}
                />
              ))}
            </PanelBlock>
            <PanelBlock title="AI 模型" icon={Bot}>
              {models.map((model) => (
                <InventoryRow
                  key={model.id}
                  icon={Bot}
                  title={model.name}
                  status={model.status === "available" ? "可用" : "未配置"}
                  detail={model.path || model.provider}
                  ok={model.status === "available"}
                />
              ))}
            </PanelBlock>
          </aside>
        </div>
      </section>
    </main>
  );
}

function TaskRow({
  job,
  onCancel,
  onReveal
}: {
  job: DownloadJob;
  onCancel: (jobId: string) => void;
  onReveal: (path: string) => Promise<void>;
}) {
  const StatusIcon = getStatusIcon(job.status);
  const completedFile = job.downloaded_files.find((file) => file.type === "video") ?? job.downloaded_files[0];

  return (
    <article className="taskRow">
      <div className="taskStatus">
        <StatusIcon size={20} />
      </div>
      <div className="taskMain">
        <div className="taskTitleRow">
          <h2>{job.title}</h2>
          <span className={`statusTag ${job.status}`}>{statusLabels[job.status]}</span>
        </div>
        <div className="taskMeta">
          <span>{job.platform}</span>
          <span>{job.options.quality}</span>
          <span>{job.output_dir}</span>
        </div>
        <div className="progressTrack">
          <div className="progressFill" style={{ width: `${Math.max(0, Math.min(100, job.progress))}%` }} />
        </div>
        <div className="taskMessage">{job.error || job.message || job.url}</div>
      </div>
      <div className="taskActions">
        <button
          className="iconButton"
          type="button"
          onClick={() => onReveal(completedFile?.path || job.output_dir)}
          title="打开位置"
        >
          <FolderOpen size={18} />
        </button>
        {["queued", "resolving", "downloading"].includes(job.status) ? (
          <button className="iconButton danger" type="button" onClick={() => onCancel(job.id)} title="取消任务">
            <Trash2 size={18} />
          </button>
        ) : null}
      </div>
    </article>
  );
}

function PanelBlock({
  title,
  icon: Icon,
  children
}: {
  title: string;
  icon: typeof Wrench;
  children: ReactNode;
}) {
  return (
    <section className="panelBlock">
      <div className="panelHeader">
        <Icon size={18} />
        <h2>{title}</h2>
      </div>
      <div className="inventoryList">{children}</div>
    </section>
  );
}

function InventoryRow({
  icon: Icon,
  title,
  status,
  detail,
  ok
}: {
  icon: typeof Wrench;
  title: string;
  status: string;
  detail: string;
  ok: boolean;
}) {
  return (
    <div className="inventoryRow">
      <Icon size={16} />
      <div>
        <strong>{title}</strong>
        <span>{detail}</span>
      </div>
      <em className={ok ? "ok" : "missing"}>{status}</em>
    </div>
  );
}

function getStatusIcon(status: JobStatus) {
  if (status === "success") {
    return CircleCheck;
  }
  if (status === "error") {
    return CircleX;
  }
  if (status === "cancelled") {
    return CircleAlert;
  }
  if (status === "downloading" || status === "resolving") {
    return LoaderCircle;
  }
  return Download;
}

export default App;
