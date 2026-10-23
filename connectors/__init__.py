"""
BABY Connectors Framework
=========================
A modular, provider-agnostic integration framework for external services
such as Google Calendar, Gmail, Slack, Notion, and GitHub.
"""

import os
import sys

# Ensure bundled libraries in BABY/libs are on python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBS_DIR = os.path.join(BASE_DIR, "libs")
if os.path.exists(LIBS_DIR) and LIBS_DIR not in sys.path:
    sys.path.insert(0, LIBS_DIR)

from .manager import get_connector_manager, ConnectorManager
from .providers.whatsapp import (
    WhatsAppConnector,
    ContactAliasManager,
    WhatsAppError,
    WhatsAppNotConnectedError,
    WhatsAppLoggedOutError,
    WhatsAppUnregisteredRecipientError
)

__all__ = [
    "get_connector_manager",
    "ConnectorManager",
    "WhatsAppConnector",
    "ContactAliasManager",
    "WhatsAppError",
    "WhatsAppNotConnectedError",
    "WhatsAppLoggedOutError",
    "WhatsAppUnregisteredRecipientError"
]

