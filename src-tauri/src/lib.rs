use std::{
    io::{Read, Write},
    net::{SocketAddr, TcpListener, TcpStream},
    process::Command,
    sync::{Mutex, OnceLock},
    thread,
    time::{Duration, Instant},
};

use tauri::{AppHandle, Listener};
use tauri_plugin_shell::{
    process::{CommandChild, CommandEvent},
    ShellExt,
};

const BACKEND_HOST: &str = "127.0.0.1";
const BACKEND_DEFAULT_PORT: u16 = 8765;
const SIDECAR_PROGRAM: &str = "douyingo-sidecar";
const SIDECAR_STARTUP_TIMEOUT: Duration = Duration::from_secs(20);

#[derive(Default)]
struct SidecarState {
    child: Option<CommandChild>,
    port: Option<u16>,
    last_message: Option<String>,
}

static SIDECAR_STATE: OnceLock<Mutex<SidecarState>> = OnceLock::new();

fn sidecar_state() -> &'static Mutex<SidecarState> {
    SIDECAR_STATE.get_or_init(|| Mutex::new(SidecarState::default()))
}

fn stop_sidecar(child: CommandChild) {
    #[cfg(target_os = "windows")]
    {
        use std::os::windows::process::CommandExt;

        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        let status = Command::new("taskkill")
            .args(["/PID", &child.pid().to_string(), "/T", "/F"])
            .creation_flags(CREATE_NO_WINDOW)
            .status();
        if status.is_ok_and(|status| status.success()) {
            return;
        }
    }

    let _ = child.kill();
}

fn backend_url(port: u16) -> String {
    format!("http://{BACKEND_HOST}:{port}")
}

fn backend_is_ready(port: u16) -> bool {
    let address = SocketAddr::from(([127, 0, 0, 1], port));
    let Ok(mut stream) = TcpStream::connect_timeout(&address, Duration::from_millis(250)) else {
        return false;
    };

    let _ = stream.set_read_timeout(Some(Duration::from_millis(500)));
    let _ = stream.set_write_timeout(Some(Duration::from_millis(500)));
    let request =
        format!("GET /health HTTP/1.1\r\nHost: {BACKEND_HOST}:{port}\r\nConnection: close\r\n\r\n");
    if stream.write_all(request.as_bytes()).is_err() {
        return false;
    }

    let mut response = String::new();
    stream.read_to_string(&mut response).is_ok()
        && response.starts_with("HTTP/1.1 200")
        && response.contains("douyingo-sidecar")
}

fn select_available_port(preferred_port: u16) -> Result<u16, String> {
    if TcpListener::bind((BACKEND_HOST, preferred_port)).is_ok() {
        return Ok(preferred_port);
    }

    let listener = TcpListener::bind((BACKEND_HOST, 0))
        .map_err(|err| format!("failed to reserve a sidecar port: {err}"))?;
    listener
        .local_addr()
        .map(|address| address.port())
        .map_err(|err| format!("failed to read the reserved sidecar port: {err}"))
}

async fn wait_for_backend(port: u16) -> Result<bool, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let deadline = Instant::now() + SIDECAR_STARTUP_TIMEOUT;
        while Instant::now() < deadline {
            if backend_is_ready(port) {
                return true;
            }
            thread::sleep(Duration::from_millis(200));
        }
        false
    })
    .await
    .map_err(|err| format!("failed to wait for sidecar: {err}"))
}

#[tauri::command]
async fn ensure_backend(app: AppHandle) -> Result<String, String> {
    let managed_port = sidecar_state()
        .lock()
        .ok()
        .and_then(|state| state.port.filter(|_| state.child.is_some()));
    if let Some(port) = managed_port {
        if backend_is_ready(port) {
            return Ok(backend_url(port));
        }
    }

    if backend_is_ready(BACKEND_DEFAULT_PORT) {
        return Ok(backend_url(BACKEND_DEFAULT_PORT));
    }

    let port = {
        let mut state = sidecar_state()
            .lock()
            .map_err(|_| "sidecar state mutex poisoned".to_string())?;

        if state.child.is_some() && state.port.is_none() {
            if let Some(child) = state.child.take() {
                stop_sidecar(child);
            }
        }

        if state.child.is_none() {
            state.last_message = None;
            let selected_port = select_available_port(BACKEND_DEFAULT_PORT)?;
            let port_argument = selected_port.to_string();
            let parent_pid = std::process::id().to_string();
            let command = app
                .shell()
                .sidecar(SIDECAR_PROGRAM)
                .map_err(|err| format!("failed to resolve sidecar: {err}"))?
                .args([
                    "serve",
                    "--host",
                    BACKEND_HOST,
                    "--port",
                    &port_argument,
                    "--parent-pid",
                    &parent_pid,
                ]);
            let (mut rx, child) = command
                .spawn()
                .map_err(|err| format!("failed to start sidecar: {err}"))?;
            let pid = child.pid();
            state.child = Some(child);
            state.port = Some(selected_port);

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    let mut terminal = false;
                    let message = match event {
                        CommandEvent::Stdout(bytes) | CommandEvent::Stderr(bytes) => {
                            let line = String::from_utf8_lossy(&bytes).trim().to_string();
                            if line.is_empty() {
                                None
                            } else {
                                Some(line)
                            }
                        }
                        CommandEvent::Error(error) => Some(error),
                        CommandEvent::Terminated(payload) => {
                            terminal = true;
                            Some(format!("sidecar exited with code {:?}", payload.code))
                        }
                        _ => None,
                    };

                    if let Ok(mut state) = sidecar_state().lock() {
                        if terminal {
                            let terminal_message =
                                message.unwrap_or_else(|| "sidecar exited".into());
                            state.last_message = Some(match state.last_message.take() {
                                Some(previous) => format!("{terminal_message}: {previous}"),
                                None => terminal_message,
                            });
                        } else if let Some(message) = message {
                            state.last_message = Some(message);
                        }
                        if terminal && state.child.as_ref().is_some_and(|child| child.pid() == pid)
                        {
                            state.child.take();
                            state.port = None;
                        }
                    }
                }
            });
        }

        state
            .port
            .ok_or_else(|| "sidecar port was not initialized".to_string())?
    };

    if wait_for_backend(port).await? {
        if let Ok(mut state) = sidecar_state().lock() {
            state.last_message = None;
        }
        return Ok(backend_url(port));
    }

    let mut state = sidecar_state()
        .lock()
        .map_err(|_| "sidecar state mutex poisoned".to_string())?;
    let detail = state
        .last_message
        .clone()
        .unwrap_or_else(|| "health check timed out".to_string());
    if let Some(child) = state.child.take() {
        stop_sidecar(child);
    }
    state.port = None;
    Err(format!("sidecar did not become ready: {detail}"))
}

#[tauri::command]
async fn reveal_path(path: String) -> Result<(), String> {
    let path = std::path::PathBuf::from(path);
    let target = if path.is_file() {
        path
    } else if path.is_dir() {
        path
    } else {
        path.parent()
            .map(std::path::Path::to_path_buf)
            .ok_or_else(|| "path does not exist".to_string())?
    };

    #[cfg(target_os = "windows")]
    {
        let mut command = Command::new("explorer.exe");
        if target.is_file() {
            command.arg(format!("/select,{}", target.display()));
        } else {
            command.arg(target);
        }
        command.spawn().map_err(|err| err.to_string())?;
    }

    #[cfg(target_os = "macos")]
    {
        let mut command = Command::new("open");
        if target.is_file() {
            command.arg("-R").arg(target);
        } else {
            command.arg(target);
        }
        command.spawn().map_err(|err| err.to_string())?;
    }

    #[cfg(all(unix, not(target_os = "macos")))]
    {
        let open_target = if target.is_file() {
            target.parent().unwrap_or(target.as_path()).to_path_buf()
        } else {
            target
        };
        Command::new("xdg-open")
            .arg(open_target)
            .spawn()
            .map_err(|err| err.to_string())?;
    }

    Ok(())
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![ensure_backend, reveal_path])
        .setup(|app| {
            let app_handle = app.handle().clone();
            app_handle.listen("tauri://close-requested", |_| {
                if let Ok(mut state) = sidecar_state().lock() {
                    if let Some(child) = state.child.take() {
                        stop_sidecar(child);
                    }
                    state.port = None;
                }
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running DouyinGo desktop shell");
}

#[cfg(test)]
mod tests {
    use super::{backend_url, select_available_port, BACKEND_HOST, SIDECAR_PROGRAM};
    use std::net::TcpListener;
    use std::path::Path;

    #[test]
    fn packaged_sidecar_is_resolved_next_to_the_desktop_executable() {
        assert_eq!(Path::new(SIDECAR_PROGRAM).components().count(), 1);
    }

    #[test]
    fn occupied_preferred_port_uses_an_available_fallback() {
        let occupied = TcpListener::bind((BACKEND_HOST, 0)).expect("bind occupied test port");
        let occupied_port = occupied.local_addr().expect("read occupied port").port();

        let selected_port = select_available_port(occupied_port).expect("select fallback port");

        assert_ne!(selected_port, occupied_port);
        assert_eq!(
            backend_url(selected_port),
            format!("http://127.0.0.1:{selected_port}")
        );
    }
}
