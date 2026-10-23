"""
WhatsApp Multi-Device Connector (Python)
========================================
Production-grade Python interface managing the local Baileys Multi-Device sidecar.
Provides full exception handling for device logouts, socket disconnects, unregistered
recipients, contact resolution, automated sidecar process supervision, and an inbound
webhook listener that executes commands on the PC and speaks out loud.
"""

import os
import sys
import time
import json
import shutil
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List, Optional, Tuple, Any
import requests

from logs.Logging import log
from ...base import BaseMessagingConnector
from ...models import WhatsAppStatus
from .contacts import ContactAliasManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SIDECAR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sidecar")
DEFAULT_PORT = 8765
DEFAULT_WEBHOOK_PORT = 8766


# ==============================================================================
# Custom WhatsApp Exceptions
# ==============================================================================

class WhatsAppError(Exception):
    """Base exception for all WhatsApp connector errors."""
    pass


class WhatsAppNotConnectedError(WhatsAppError):
    """Raised when an operation requires an active WhatsApp connection but none exists."""
    pass


class WhatsAppLoggedOutError(WhatsAppError):
    """Raised when the session was unlinked / logged out from the mobile device."""
    pass


class WhatsAppUnregisteredRecipientError(WhatsAppError):
    """Raised when attempting to message a phone number not registered on WhatsApp."""
    pass


class WhatsAppConnectionTimeoutError(WhatsAppError):
    """Raised when the local sidecar bridge is unreachable or times out."""
    pass


# ==============================================================================
# Inbound Webhook HTTP Handler (Phone -> PC Execution)
# ==============================================================================

class _WhatsAppWebhookHandler(BaseHTTPRequestHandler):
    """
    Receives incoming WhatsApp messages from the dedicated group,
    executes them on the PC, speaks the answer, and returns JSON reply.
    """

    connector: Optional["WhatsAppConnector"] = None

    def log_message(self, format, *args):
        # Silence standard HTTP access logging to keep terminal clean
        pass

    def do_POST(self):
        if self.path == "/whatsapp/webhook":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            reply_text = "I received your command."
            media_path = None
            try:
                data = json.loads(body.decode("utf-8") if body else "{}")
                incoming_text = data.get("text", "").strip()

                if incoming_text and self.connector:
                    res = self.connector.execute_pc_command(incoming_text)
                    if isinstance(res, tuple):
                        reply_text, media_path = res
                    else:
                        reply_text = res

            except Exception as e:
                log.error(f"Error processing WhatsApp inbound webhook: {e}")
                reply_text = f"Encountered error executing command: {e}"

            resp_payload = {"reply": reply_text}
            if media_path and os.path.isfile(media_path):
                resp_payload["media_path"] = media_path
            response_bytes = json.dumps(resp_payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
        else:
            self.send_response(404)
            self.end_headers()


# ==============================================================================
# WhatsApp Connector Implementation
# ==============================================================================

class WhatsAppConnector(BaseMessagingConnector):
    """
    Robust connector providing WhatsApp messaging capabilities.
    Supervises the Node.js Baileys sidecar, normalizes recipients, and handles
    all disconnection and authentication edge cases.
    """

    def __init__(self, port: int = DEFAULT_PORT, webhook_port: int = DEFAULT_WEBHOOK_PORT):
        self.port = port
        self.webhook_port = webhook_port
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.contacts = ContactAliasManager()
        self._sidecar_process: Optional[subprocess.Popen] = None
        self._webhook_server: Optional[HTTPServer] = None
        self._webhook_thread: Optional[threading.Thread] = None

        # Start inbound webhook server
        self._start_webhook_server()

        # Automatically ensure the Node.js Baileys bridge daemon is listening on port 8765
        self.ensure_sidecar_running()

        log.info(f"WhatsAppConnector initialized targeting {self.base_url} (Webhook: :{self.webhook_port})")

    @property
    def name(self) -> str:
        return "whatsapp"

    @property
    def display_name(self) -> str:
        return "WhatsApp"

    # --------------------------------------------------------------------------
    # Inbound Webhook Server Lifecycle
    # --------------------------------------------------------------------------

    def _start_webhook_server(self):
        """Starts background HTTP server to receive inbound messages from sidecar."""
        try:
            _WhatsAppWebhookHandler.connector = self
            self._webhook_server = HTTPServer(("127.0.0.1", self.webhook_port), _WhatsAppWebhookHandler)
            self._webhook_thread = threading.Thread(target=self._webhook_server.serve_forever, daemon=True)
            self._webhook_thread.start()
            log.info(f"WhatsApp inbound webhook listening on 127.0.0.1:{self.webhook_port}")
        except Exception as e:
            log.warning(f"Could not bind WhatsApp webhook on port {self.webhook_port}: {e}")

    # --------------------------------------------------------------------------
    # Phone -> PC Command Execution Engine
    # --------------------------------------------------------------------------

    def execute_pc_command(self, text: str) -> str:
        """
        Executes a command received from WhatsApp directly on the PC:
        dispatches skill, speaks response through PC speakers, and returns reply text.
        """
        log.info(f"WhatsApp Phone Command executing on PC: '{text}'")
        reply_text = ""
        spoken_to_pc = None
        media_path = None

        try:
            # Detect compound / multi-step workflow requests immediately
            lower_words = text.lower().split()
            is_compound = any(w in lower_words for w in ["and", "then", "after", "also", "screenshot", "ram", "memory", "storage", "kill", "processes"])

            intent = None
            slots = {}

            if not is_compound:
                from speech_to_intent.hassil_intent import recognize_intent
                intent, voice2json = recognize_intent(text)
                slots = voice2json.get("slots", {}) if isinstance(voice2json, dict) else {}
                log.info(f"Fast-path intent parsed: {intent} (slots: {slots})")

            # 1. Volume Control (Fast Path)
            if intent == "Volume":
                from skills import volume
                action = slots.get("action", "")
                sound_val = slots.get("sound")
                if "increase" in action:
                    volume.increase_volume()
                    reply_text = "Increasing master volume on PC."
                elif "decrease" in action:
                    volume.decrease_volume()
                    reply_text = "Decreasing master volume on PC."
                elif sound_val is not None:
                    volume.change_volume(int(sound_val))
                    reply_text = f"Master volume set to {sound_val} percent."
                else:
                    reply_text = f"Current PC volume is {volume.get_volume()}%."

            # 2. Brightness Control
            elif intent == "Brightness":
                from skills import change_brightness
                action = slots.get("action", "")
                val = slots.get("brightness")
                if "increase" in action:
                    change_brightness.increase_brightness()
                    reply_text = "Increasing screen brightness on PC."
                elif "decrease" in action:
                    change_brightness.decrease_brightness()
                    reply_text = "Decreasing screen brightness on PC."
                elif val is not None:
                    change_brightness.set_brightness(int(val))
                    reply_text = f"Screen brightness set to {val} percent."
                else:
                    reply_text = "Adjusted screen brightness."

            # 3. Media Playback Control
            elif intent == "Media":
                from skills import media
                status = slots.get("status", "resume")
                if status in ("resume", "play", "pause", "stop"):
                    media.pause_resume_toggle()
                    reply_text = "Toggled media playback on PC."
                elif status == "mute":
                    media.mute()
                    reply_text = "Toggled PC audio mute."
                elif status == "next":
                    media.next_media()
                    reply_text = "Skipped to next media track."
                elif status == "previous":
                    media.previous_media()
                    reply_text = "Playing previous media track."

            # 4. App Launcher
            elif intent in ("Terminal", "AppLauncher"):
                from skills.app_launcher import launch_app
                app_name = slots.get("app", "terminal")
                ok, app_reply = launch_app(app_name)
                reply_text = app_reply

            # 5. Window Control
            elif intent == "WindowControl":
                from skills.app_launcher import handle_window_control
                action = slots.get("action", "switch")
                app_name = slots.get("app", "")
                ok, win_reply = handle_window_control(action=action, app_name=app_name)
                reply_text = win_reply

            # 6. Reminders
            elif intent in ("Reminder", "ReminderList", "ReminderClear"):
                from skills.reminder import handle_reminder
                ok, rem_reply = handle_reminder(voice2json)
                reply_text = rem_reply

            # 7. Calendar Agenda
            elif intent == "CalendarAgenda":
                from connectors.manager import get_connector_manager
                mgr = get_connector_manager()
                ok, cal_reply = mgr.handle_agenda(text)
                reply_text = cal_reply

            # 8. Calendar Next Meeting
            elif intent == "CalendarNextMeeting":
                from connectors.manager import get_connector_manager
                mgr = get_connector_manager()
                ok, meet_reply = mgr.handle_next_meeting()
                reply_text = meet_reply

            # 9. Time & Date
            elif intent == "Time":
                from datetime import datetime
                now_str = datetime.now().strftime("%I:%M %p").lstrip("0")
                reply_text = f"The current time is {now_str}."

            elif intent == "Date":
                from datetime import datetime
                today_str = datetime.now().strftime("%A, %B %d, %Y")
                reply_text = f"Today is {today_str}."

            # 10. Weather
            elif intent in ("CheckWeather", "RainSnow"):
                from skills import weather
                reply_text = weather.get_weather() or "Checking current weather."

            # 11. Complex Multi-Step Workflows / Autonomous Agentic Fallback
            else:
                try:
                    from agent import agent_orchestrator
                    agent_res = agent_orchestrator.run(text)
                    if agent_res:
                        reply_text = agent_res.chat_text or agent_res.spoken_text or ""
                        spoken_to_pc = agent_res.spoken_text or agent_res.chat_text
                        if agent_res.media_path and os.path.isfile(agent_res.media_path):
                            media_path = agent_res.media_path
                except Exception as agent_err:
                    log.error(f"Agent execution failed: {agent_err}", exc_info=True)
                    try:
                        from speech_to_intent.groq_brain import ask_groq
                        reply_text = ask_groq(text) or "I processed your request."
                    except Exception:
                        reply_text = "I received your command."

            if not reply_text:
                reply_text = "I received your command on PC."

        except Exception as exec_err:
            log.error(f"Error executing PC skill: {exec_err}")
            reply_text = f"Encountered error: {exec_err}"

        # Speak response out loud through PC speakers in a background thread
        # This prevents audio playback from delaying the WhatsApp message delivery (0ms lag)
        def _async_speak(speech_content: str):
            try:
                from speech.text2speech import speak
                speak(speech_content)
            except Exception as spk_err:
                log.debug(f"Could not speak through PC speakers: {spk_err}")

        text_to_speak = spoken_to_pc or reply_text
        if text_to_speak:
            import threading
            threading.Thread(target=_async_speak, args=(text_to_speak,), daemon=True).start()

        return reply_text, media_path

    # --------------------------------------------------------------------------
    # Daemon Supervision & Health Check
    # --------------------------------------------------------------------------

    def ensure_sidecar_running(self) -> bool:
        """
        Verifies that the Baileys bridge daemon is listening.
        If offline, automatically spawns it as a background process and waits for ready.
        """
        try:
            resp = requests.get(f"{self.base_url}/status", timeout=1.0)
            if resp.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass

        log.info("WhatsApp sidecar is not running. Spawning bridge.js...")
        node_path = shutil.which("node")
        if not node_path:
            node_alt = os.path.expanduser("~/.nvm/versions/node/v24.7.0/bin/node")
            node_path = node_alt if os.path.exists(node_alt) else "node"

        bridge_file = os.path.join(SIDECAR_DIR, "bridge.js")
        if not os.path.exists(bridge_file):
            log.error(f"WhatsApp bridge file not found at {bridge_file}")
            return False

        try:
            env = os.environ.copy()
            env["WHATSAPP_PORT"] = str(self.port)
            env["PYTHON_PORT"] = str(self.webhook_port)
            self._sidecar_process = subprocess.Popen(
                [node_path, bridge_file],
                cwd=SIDECAR_DIR,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # Wait up to 5 seconds for local API to respond
            for _ in range(25):
                time.sleep(0.2)
                try:
                    resp = requests.get(f"{self.base_url}/status", timeout=0.5)
                    if resp.status_code == 200:
                        log.info("WhatsApp sidecar daemon started successfully.")
                        return True
                except requests.exceptions.RequestException:
                    continue

            log.error("Timed out waiting for WhatsApp sidecar daemon to listen.")
            return False

        except Exception as e:
            log.error(f"Failed to spawn WhatsApp sidecar daemon: {e}")
            return False

    # --------------------------------------------------------------------------
    # Connection State & Telemetry
    # --------------------------------------------------------------------------

    def get_status(self) -> WhatsAppStatus:
        """
        Fetches structured telemetry from the local bridge.
        """
        try:
            resp = requests.get(f"{self.base_url}/status", timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                return WhatsAppStatus(
                    connected=bool(data.get("connected", False)),
                    state=str(data.get("state", "disconnected")),
                    phone=data.get("phone"),
                    jid=data.get("jid"),
                    qr=data.get("qr"),
                    error=None
                )
        except requests.exceptions.RequestException as e:
            log.debug(f"WhatsApp status check error: {e}")
            return WhatsAppStatus(
                connected=False,
                state="sidecar_offline",
                error=str(e)
            )

        return WhatsAppStatus(connected=False, state="unknown")

    def is_connected(self) -> bool:
        """
        Returns True if WhatsApp is currently authenticated and connected.
        """
        status = self.get_status()
        return status.connected

    # --------------------------------------------------------------------------
    # Pairing & Authentication
    # --------------------------------------------------------------------------

    def initiate_auth(self) -> Tuple[bool, str]:
        """
        Launches the dedicated dark-glass pairing popup displaying the QR code.
        """
        if not self.ensure_sidecar_running():
            return False, "Could not start WhatsApp bridge service."

        status = self.get_status()
        if status.connected:
            phone_str = f"+{status.phone}" if status.phone else "your phone"
            return True, f"WhatsApp is already connected to {phone_str}."

        pair_url = f"{self.base_url}/pair"
        log.info(f"Opening WhatsApp pairing window: {pair_url}")

        browser_bin = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
        display = os.environ.get("DISPLAY", ":1")
        env = os.environ.copy()
        env["DISPLAY"] = display

        if browser_bin:
            cmd = [browser_bin, f"--app={pair_url}", "--window-size=440,640"]
            try:
                subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True, "WhatsApp pairing window opened. Please scan the QR code with your phone."
            except Exception as e:
                log.error(f"Error launching popup browser: {e}")

        import webbrowser
        webbrowser.open(pair_url)
        return True, "Opened WhatsApp pairing screen in your browser."

    def disconnect(self) -> Tuple[bool, str]:
        """
        Unlinks the WhatsApp session and clears local credentials.
        """
        try:
            resp = requests.post(f"{self.base_url}/logout", timeout=5.0)
            if resp.status_code == 200:
                log.info("WhatsApp session successfully unlinked.")
                return True, "WhatsApp has been unlinked successfully."
        except Exception as e:
            log.error(f"Failed to unlink WhatsApp session: {e}")

        return False, "Could not disconnect WhatsApp session."

    def create_assistant_group(self) -> Tuple[bool, str]:
        """
        Explicitly triggers creation or reuse of the dedicated '🍼 BABY Assistant' group.
        """
        try:
            resp = requests.post(f"{self.base_url}/create_group", timeout=8.0)
            if resp.status_code == 200:
                data = resp.json()
                gid = data.get("group_jid")
                if gid:
                    return True, f"Dedicated group ready: {gid}"
        except Exception as e:
            log.error(f"Failed creating assistant group: {e}")
        return False, "Could not create or resolve assistant group."

    # --------------------------------------------------------------------------
    # Outbound Messaging & Recipient Resolution
    # --------------------------------------------------------------------------

    def send_message(self, recipient: str, text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Sends an outbound WhatsApp message with pre-flight recipient verification.

        Args:
            recipient: Phone number, contact name ('Mom', 'Rahul'), 'group', or 'me'.
            text: Message body to send.
        """
        if not text or not text.strip():
            return False, "Message text cannot be empty.", None

        if not self.ensure_sidecar_running():
            return False, "WhatsApp service is currently offline.", None

        status = self.get_status()
        if status.is_logged_out:
            log.warn("WhatsApp device was unlinked from phone.")
            return False, "WhatsApp was unlinked from your phone. Please scan the QR code to reconnect.", None

        if not status.connected:
            return False, "WhatsApp is not connected. Please say 'link WhatsApp' to pair your phone.", None

        success, resolved_target, friendly_label = self.contacts.resolve_recipient(recipient)
        if not success or not resolved_target:
            return False, resolved_target, None

        payload = {
            "to": resolved_target,
            "text": text.strip()
        }

        try:
            resp = requests.post(
                f"{self.base_url}/send",
                json=payload,
                timeout=12.0
            )

            data = resp.json() if resp.content else {}

            if resp.status_code == 200 and data.get("success"):
                msg_id = data.get("messageId")
                log.info(f"WhatsApp message dispatched to {friendly_label} (ID: {msg_id})")
                return True, f"Sent WhatsApp message to {friendly_label}.", msg_id

            error_msg = data.get("error", "Unknown error")
            log.error(f"WhatsApp send failed: {error_msg}")

            if "not registered" in error_msg.lower():
                return False, f"Number for {friendly_label} is not registered on WhatsApp.", None

            return False, f"Failed to send WhatsApp message: {error_msg}", None

        except requests.exceptions.Timeout:
            log.error("WhatsApp send timed out.")
            return False, "WhatsApp message timed out. Please check your phone connection.", None

        except requests.exceptions.RequestException as e:
            log.error(f"Network error sending WhatsApp message: {e}")
            return False, "Could not reach WhatsApp service.", None

    def send_media(self, recipient: str, file_path: str, caption: str = "") -> Tuple[bool, str, Optional[str]]:
        """
        Transmits an image/media file directly to a recipient or dedicated group via WhatsApp.
        """
        if not file_path or not os.path.exists(file_path):
            return False, f"Media file not found: {file_path}", None

        if not self.ensure_sidecar_running():
            return False, "WhatsApp service is currently offline.", None

        status = self.get_status()
        if not status.connected:
            return False, "WhatsApp is not connected.", None

        success, resolved_target, friendly_label = self.contacts.resolve_recipient(recipient)
        if not success or not resolved_target:
            return False, resolved_target, None

        payload = {
            "to": resolved_target,
            "filePath": os.path.abspath(file_path),
            "caption": caption.strip() if caption else ""
        }

        try:
            resp = requests.post(f"{self.base_url}/send_media", json=payload, timeout=25.0)
            data = resp.json() if resp.content else {}
            if resp.status_code == 200 and data.get("success"):
                msg_id = data.get("messageId")
                log.info(f"WhatsApp media dispatched to {friendly_label} (ID: {msg_id})")
                return True, f"Sent image to {friendly_label}.", msg_id
            error_msg = data.get("error", "Unknown error")
            return False, f"Failed to send media: {error_msg}", None
        except Exception as e:
            log.error(f"Error sending WhatsApp media: {e}")
            return False, str(e), None

    def send_to_group(self, text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Convenience method to dispatch a notification directly into the dedicated group.
        """
        return self.send_message(recipient="group", text=text)

    def send_to_contact(self, name: str, text: str) -> Tuple[bool, str]:
        """
        Helper method specifically for voice commands (e.g. 'text Rahul').
        """
        success, reply, _ = self.send_message(recipient=name, text=text)
        return success, reply

    def add_contact(self, name: str, phone: str) -> Tuple[bool, str]:
        """
        Saves a contact alias for voice recognition.
        """
        return self.contacts.add_contact(name, phone)
