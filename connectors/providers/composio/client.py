"""
Composio Client Manager
=======================
Manages the lifecycle, authentication, and configuration of the Composio SDK.
Reads credentials from BABY's config.ini and provides a thread-safe singleton toolset.
"""

import os
import sys
import threading
from typing import Optional

# Ensure bundled libs are available
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LIBS_DIR = os.path.join(BASE_DIR, "libs")
if os.path.exists(LIBS_DIR) and LIBS_DIR not in sys.path:
    sys.path.insert(0, LIBS_DIR)

from config.get_config import get_config
from logs.Logging import log

try:
    from composio import ComposioToolSet, App, Action
    _COMPOSIO_AVAILABLE = True
except ImportError as err:
    log.warning(f"ComposioClient: Failed to import composio SDK: {err}")
    _COMPOSIO_AVAILABLE = False
    ComposioToolSet = None
    App = None
    Action = None


_lock = threading.Lock()
_toolset_instance: Optional[ComposioToolSet] = None


def get_composio_api_key() -> str:
    """
    Retrieves the Composio API key from config.ini or environment variables.
    """
    # 1. Check environment variable first
    env_key = os.environ.get("COMPOSIO_API_KEY", "").strip()
    if env_key:
        return env_key

    # 2. Check config.ini under [composio] section
    ini_key = get_config("composio", "api_key", fallback="")
    return str(ini_key or "").strip()


def get_composio_user_id() -> str:
    """
    Returns the configured user identity string used to scope connected accounts.
    Defaults to 'baby_desktop_user'.
    """
    user_id = get_config("composio", "user_id", fallback="baby_desktop_user")
    return str(user_id or "baby_desktop_user").strip()


def get_composio_toolset() -> Optional[ComposioToolSet]:
    """
    Returns a shared thread-safe ComposioToolSet instance.
    Returns None if composio is unavailable or API key is missing.
    """
    global _toolset_instance

    if not _COMPOSIO_AVAILABLE:
        log.warning("ComposioClient: composio-core package is not installed.")
        return None

    with _lock:
        if _toolset_instance is None:
            api_key = get_composio_api_key()
            if not api_key:
                log.warning("ComposioClient: No api_key found in config.ini [composio].")
                return None

            try:
                user_id = get_composio_user_id()
                _toolset_instance = ComposioToolSet(api_key=api_key, entity_id=user_id)
                log.info(f"ComposioClient: Initialized ComposioToolSet for entity '{user_id}'.")
            except Exception as e:
                log.error(f"ComposioClient: Failed to initialize ComposioToolSet: {e}")
                return None

        return _toolset_instance
