import os
import shutil
import subprocess
from typing import Tuple, Dict, Any, Optional
from logs.Logging import log

# Pre-defined app registry for quick alias matching and window class detection
APP_REGISTRY: Dict[str, Dict[str, Any]] = {
    "chrome": {
        "display": "Google Chrome",
        "desktop": "google-chrome.desktop",
        "bins": ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"],
        "classes": ["google-chrome", "Google-chrome"],
    },
    "browser": {
        "display": "Web Browser",
        "desktop": "google-chrome.desktop",
        "bins": ["google-chrome", "google-chrome-stable", "firefox", "chromium"],
        "classes": ["google-chrome", "firefox"],
    },
    "firefox": {
        "display": "Firefox",
        "desktop": "firefox.desktop",
        "bins": ["firefox"],
        "classes": ["firefox", "Firefox"],
    },
    "code": {
        "display": "Visual Studio Code",
        "desktop": "code.desktop",
        "bins": ["code"],
        "classes": ["code", "Code"],
    },
    "vscode": {
        "display": "Visual Studio Code",
        "desktop": "code.desktop",
        "bins": ["code"],
        "classes": ["code", "Code"],
    },
    "pycharm": {
        "display": "PyCharm",
        "desktop": "pycharm.desktop",
        "bins": ["pycharm", "pycharm-community", "pycharm-professional"],
        "classes": ["jetbrains-pycharm", "pycharm", "PyCharm"],
    },
    "terminal": {
        "display": "Terminal",
        "desktop": ["mate-terminal.desktop", "gnome-terminal.desktop", "org.gnome.Terminal.desktop"],
        "bins": ["gnome-terminal", "mate-terminal", "x-terminal-emulator", "bash"],
        "classes": ["terminal", "gnome-terminal", "mate-terminal", "x-terminal-emulator"],
    },
    "calculator": {
        "display": "Calculator",
        "desktop": "org.gnome.Calculator.desktop",
        "bins": ["gnome-calculator", "mate-calc", "kcalc", "xcalc"],
        "classes": ["calculator", "gnome-calculator", "mate-calc"],
    },
    "calc": {
        "display": "Calculator",
        "desktop": "org.gnome.Calculator.desktop",
        "bins": ["gnome-calculator", "mate-calc", "kcalc", "xcalc"],
        "classes": ["calculator", "gnome-calculator", "mate-calc"],
    },
    "files": {
        "display": "File Manager",
        "desktop": "org.gnome.Nautilus.desktop",
        "bins": ["nautilus", "caja", "thunar", "dolphin"],
        "classes": ["nautilus", "caja", "thunar", "dolphin"],
    },
    "nautilus": {
        "display": "File Manager",
        "desktop": "org.gnome.Nautilus.desktop",
        "bins": ["nautilus", "caja", "thunar"],
        "classes": ["nautilus", "org.gnome.Nautilus"],
    },
    "settings": {
        "display": "Settings",
        "desktop": "gnome-control-center.desktop",
        "bins": ["gnome-control-center", "mate-control-center"],
        "classes": ["control-center", "gnome-control-center"],
    },
    "spotify": {
        "display": "Spotify",
        "desktop": "spotify.desktop",
        "bins": ["spotify"],
        "classes": ["spotify", "Spotify"],
    },
    "vlc": {
        "display": "VLC Media Player",
        "desktop": "vlc.desktop",
        "bins": ["vlc"],
        "classes": ["vlc", "Vlc"],
    },
    "text editor": {
        "display": "Text Editor",
        "desktop": "org.gnome.TextEditor.desktop",
        "bins": ["gnome-text-editor", "gedit", "pluma", "mousepad"],
        "classes": ["gedit", "gnome-text-editor", "TextEditor"],
    },
    "gedit": {
        "display": "Text Editor",
        "desktop": "gedit.desktop",
        "bins": ["gedit", "gnome-text-editor"],
        "classes": ["gedit", "Gedit"],
    },
}

COMMON_DESKTOP_DIRS = [
    "/usr/share/applications",
    "/usr/local/share/applications",
    os.path.expanduser("~/.local/share/applications"),
    "/var/lib/flatpak/exports/share/applications",
]


def _find_desktop_file(app_key: str, desktop_name: Optional[Any] = None) -> Optional[str]:
    """Finds the absolute path to a .desktop file, checking specified candidates or searching by key."""
    if desktop_name:
        candidates = [desktop_name] if isinstance(desktop_name, str) else list(desktop_name)
        for name in candidates:
            for d in COMMON_DESKTOP_DIRS:
                path = os.path.join(d, name)
                if os.path.exists(path):
                    return path
        return None

    # Fuzzy search in desktop directories
    clean_key = app_key.lower().replace(" ", "").replace("-", "")
    for d in COMMON_DESKTOP_DIRS:
        if not os.path.isdir(d):
            continue
        try:
            for f in os.listdir(d):
                if f.endswith(".desktop"):
                    clean_f = f.lower().replace(" ", "").replace("-", "")
                    if clean_key in clean_f:
                        return os.path.join(d, f)
        except Exception:
            pass
    return None


def launch_app(app_name: str) -> Tuple[bool, str]:
    """
    Launches an application by voice alias, desktop entry, or binary name.
    Returns (success, spoken_response).
    """
    if not app_name:
        return False, "Which application would you like me to open?"

    key = app_name.lower().strip()
    entry = APP_REGISTRY.get(key)
    display_name = entry["display"] if entry else app_name.title()

    log.info(f"AppLauncher: Attempting to launch '{app_name}' (mapped: {display_name})")

    # 1. Try launching via gtk-launch or gio launch
    desktop_target = entry.get("desktop") if entry else None
    desktop_path = _find_desktop_file(key, desktop_target)

    if desktop_path and shutil.which("gtk-launch"):
        try:
            desktop_filename = os.path.basename(desktop_path)
            subprocess.Popen(
                ["gtk-launch", desktop_filename],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            log.info(f"AppLauncher: Launched via gtk-launch: {desktop_filename}")
            return True, f"Opening {display_name}"
        except Exception as e:
            log.warning(f"gtk-launch failed: {e}")

    if desktop_path and shutil.which("gio"):
        try:
            subprocess.Popen(
                ["gio", "launch", desktop_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            log.info(f"AppLauncher: Launched via gio launch: {desktop_path}")
            return True, f"Opening {display_name}"
        except Exception as e:
            log.warning(f"gio launch failed: {e}")

    # 2. Try launching via binary path
    candidate_bins = entry.get("bins", [key]) if entry else [key]
    for b in candidate_bins:
        bin_path = shutil.which(b)
        if bin_path:
            try:
                subprocess.Popen(
                    [bin_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                log.info(f"AppLauncher: Launched via binary: {bin_path}")
                return True, f"Opening {display_name}"
            except Exception as e:
                log.warning(f"Binary spawn failed for {bin_path}: {e}")

    log.error(f"AppLauncher: Could not find application '{app_name}'")
    return False, f"Sorry, I could not find {display_name} on your system."


def switch_to_app(app_name: str) -> Tuple[bool, str]:
    """
    Searches for an open window matching the application and activates it.
    If no window is open, launches the application.
    """
    if not app_name:
        return False, "Which application would you like to switch to?"

    key = app_name.lower().strip()
    entry = APP_REGISTRY.get(key)
    display_name = entry["display"] if entry else app_name.title()

    if not shutil.which("xdotool"):
        # If xdotool isn't present, fall back to launch
        return launch_app(app_name)

    # 1. Search by class
    classes = entry.get("classes", [key]) if entry else [key]
    for cls in classes:
        try:
            out = subprocess.check_output(
                ["xdotool", "search", "--onlyvisible", "--class", cls],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            if out:
                win_id = out.split()[0]
                subprocess.run(["xdotool", "windowactivate", win_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                log.info(f"AppLauncher: Activated window {win_id} for class '{cls}'")
                return True, f"Switched to {display_name}"
        except Exception:
            pass

    # 2. Search by window name/title
    try:
        out = subprocess.check_output(
            ["xdotool", "search", "--onlyvisible", "--name", display_name],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        if out:
            win_id = out.split()[0]
            subprocess.run(["xdotool", "windowactivate", win_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log.info(f"AppLauncher: Activated window {win_id} by name '{display_name}'")
            return True, f"Switched to {display_name}"
    except Exception:
        pass

    # 3. Not found: Launch app instead
    log.info(f"AppLauncher: Window not found for '{display_name}', launching app instead")
    success, _ = launch_app(app_name)
    if success:
        return True, f"{display_name} was not open, opening it now."
    return False, f"Could not find or launch {display_name}."


def close_active_window() -> Tuple[bool, str]:
    """Closes the current foreground window via xdotool."""
    if not shutil.which("xdotool"):
        return False, "Window control tool is not installed."
    try:
        win_id = subprocess.check_output(["xdotool", "getactivewindow"], stderr=subprocess.DEVNULL).decode().strip()
        if win_id:
            subprocess.run(["xdotool", "windowclose", win_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Closed window."
    except Exception as e:
        log.warning(f"close_active_window failed: {e}")
    return False, "No active window found to close."


def minimize_active_window() -> Tuple[bool, str]:
    """Minimizes the current foreground window via xdotool."""
    if not shutil.which("xdotool"):
        return False, "Window control tool is not installed."
    try:
        win_id = subprocess.check_output(["xdotool", "getactivewindow"], stderr=subprocess.DEVNULL).decode().strip()
        if win_id:
            subprocess.run(["xdotool", "windowminimize", win_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, "Minimized window."
    except Exception as e:
        log.warning(f"minimize_active_window failed: {e}")
    return False, "No active window found to minimize."


def handle_window_control(action: str, app_name: str = "") -> Tuple[bool, str]:
    """Dispatches window management actions (close, minimize, switch)."""
    action_clean = action.lower().strip()
    if action_clean == "close":
        return close_active_window()
    elif action_clean == "minimize":
        return minimize_active_window()
    elif action_clean in ("switch", "open", "focus"):
        return switch_to_app(app_name)
    elif app_name:
        return switch_to_app(app_name)
    return False, "Unsupported window action."
