"""
Standalone OAuth Popup & Local Callback Server
===============================================
Launches Google Sign-In inside a dedicated, isolated popup window (just like Meta Muse
and the VS Code Google extensions) without browser tab clutter, and captures the OAuth
redirect via a lightweight local loopback server that auto-closes the popup.
"""

import os
import sys
import shutil
import socket
import urllib.parse
import webbrowser
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Tuple

from logs.Logging import log

# Custom Dark Glass Success Screen served when authorization completes
SUCCESS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BABY Assistant &bull; Connected</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #0f0d17;
            color: #f5f3ff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 24px;
        }
        .card {
            background: #181524;
            border: 2px solid #a855f7;
            box-shadow: 0 20px 50px rgba(168, 85, 247, 0.25);
            border-radius: 20px;
            padding: 40px 32px;
            text-align: center;
            max-width: 420px;
            width: 100%;
            animation: fadeIn 0.4s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .icon {
            font-size: 54px;
            line-height: 1;
            margin-bottom: 20px;
        }
        h1 {
            font-size: 24px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 12px;
        }
        p {
            font-size: 15px;
            color: #c4b5fd;
            line-height: 1.5;
            margin-bottom: 24px;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid #10b981;
            color: #6ee7b7;
            padding: 8px 16px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 24px;
        }
        .footer {
            font-size: 12px;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">✨</div>
        <div class="badge">&check; Authorization Successful</div>
        <h1>BABY is Connected!</h1>
        <p>Google Calendar has been successfully linked. I can now manage your meetings and schedule.</p>
        <div class="footer">This window will close automatically...</div>
    </div>
    <script>
        // Automatically close the popup window after 1.8 seconds
        setTimeout(() => {
            window.open('', '_self', '');
            window.close();
        }, 1800);
    </script>
</body>
</html>
"""


def find_free_port() -> int:
    """Finds an available local port for the loopback server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def launch_auth_popup(auth_url: str, width: int = 500, height: int = 680) -> bool:
    """
    Opens the Google OAuth URL inside a dedicated, standalone desktop popup window.
    
    This matches the visual experience of Meta Muse and VS Code extensions:
    - No browser tabs
    - No address bar
    - Dedicated 500x680 window dimensions
    - Uses existing Chrome/Chromium user profiles so accounts are pre-populated!
    """
    log.info(f"PopupAuth: Launching standalone popup window for: {auth_url[:60]}...")

    # Look for Chromium-based browsers that support the '--app' window mode
    candidates = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "brave-browser"]
    browser_bin = None

    for name in candidates:
        path = shutil.which(name)
        if path:
            browser_bin = path
            break

    if browser_bin:
        try:
            cmd = [
                browser_bin,
                f"--app={auth_url}",
                f"--window-size={width},{height}",
                "--window-position=500,160",
                "--no-first-run",
                "--no-default-browser-check"
            ]
            log.info(f"PopupAuth: Spawning standalone window with: {browser_bin}")
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return True
        except Exception as e:
            log.warning(f"PopupAuth: Failed to launch via --app flag: {e}")

    # Fallback to standard system browser
    log.info("PopupAuth: Falling back to default system browser.")
    webbrowser.open(auth_url)
    return True


def run_oauth_callback_server(port: int = 8080, timeout_seconds: int = 120) -> Tuple[Optional[str], Optional[str]]:
    """
    Runs a temporary single-request HTTP server on 127.0.0.1 to capture the OAuth code.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: (auth_code, error_message)
    """
    captured_code = None
    captured_error = None

    class OAuthCallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal captured_code, captured_error

            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)

            if "code" in query:
                captured_code = query["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(SUCCESS_HTML.encode("utf-8"))
            elif "error" in query:
                captured_error = query["error"][0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h3>Authentication Cancelled: {captured_error}</h3>".encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            # Suppress default server console output
            pass

    server_address = ("127.0.0.1", port)
    try:
        httpd = HTTPServer(server_address, OAuthCallbackHandler)
        httpd.timeout = timeout_seconds
        log.info(f"PopupAuth: Local callback server listening at http://127.0.0.1:{port}/")

        # Wait for the single incoming redirect
        httpd.handle_request()
        httpd.server_close()
        log.info("PopupAuth: Callback captured and server closed.")

        return captured_code, captured_error

    except Exception as e:
        log.error(f"PopupAuth: Error running local callback server: {e}")
        return None, str(e)
