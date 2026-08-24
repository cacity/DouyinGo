use std::{
    process::Command,
    sync::{Mutex, OnceLock},
    thread,
    time::Duration,
};

use tauri::{AppHandle, Listener};
use tauri_plugin_shell::{
    process::{CommandChild, CommandEvent},
    ShellExt,
};

const BACKEND_HOST: &str = "127.0.0.1";
const BACKEND_PORT: u16 = 8765;

static SIDECAR_CHILD: OnceLock<Mutex<Option<CommandChild>>> = OnceLock::new();

fn sidecar_child() -> &'static Mutex<Option<CommandChild>> {
    SIDECAR_CHILD.get_or_init(|| Mutex::new(None))
}

#[tauri::command]
async fn ensure_backend(app: AppHandle) -> Result<String, String> {
    let backend_url = format!("http://{}:{}", BACKEND_HOST, BACKEND_PORT);
    let mut guard = sidecar_child()
        .lock()
        .map_err(|_| "sidecar mutex poisoned".to_string())?;

    if guard.is_none() {
        let port = BACKEND_PORT.to_string();
        let command = app
            .shell()
            .sidecar("binaries/douyingo-sidecar")
            .map_err(|err| err.to_string())?
            .args(["serve", "--host", BACKEND_HOST, "--port", &port]);
        match command.spawn() {
            Ok((mut rx, child)) => {
                tauri::async_runtime::spawn(async move {
                    while let Some(event) = rx.recv().await {
                        match event {
                            CommandEvent::Stdout(bytes) | CommandEvent::Stderr(bytes) => {
                                let line = String::from_utf8_lossy(&bytes);
                                println!("[sidecar] {line}");
                            }
                            _ => {}
                        }
                    }
                });
                *guard = Some(child);
                thread::sleep(Duration::from_millis(500));
            }
            Err(err) => {
                return Err(format!("failed to start sidecar: {err}"));
            }
        }
    }

    Ok(backend_url)
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
                if let Ok(mut guard) = sidecar_child().lock() {
                    if let Some(child) = guard.take() {
                        let _ = child.kill();
                    }
                }
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running DouyinGo desktop shell");
}
