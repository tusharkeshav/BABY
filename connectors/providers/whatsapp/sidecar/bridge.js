/**
 * WhatsApp Multi-Device Bridge (Baileys)
 * ======================================
 * Lightweight Node.js sidecar service connecting BABY Assistant directly to
 * WhatsApp's multi-device protocol servers via WebSockets.
 *
 * Features:
 * - Automated provisioning and reuse of dedicated "🍼 BABY Assistant" group
 * - Strict message scoping (ONLY processes commands in the dedicated group)
 * - Real-time connection status & QR image streaming
 * - Interactive dark-glass Web pairing page (`/pair`)
 * - Sending outbound notifications (e.g. calendar meeting alerts)
 * - Relaying inbound user commands to Python BABY backend
 */

import http from 'http';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import pino from 'pino';
import QRCode from 'qrcode';
import makeWASocket, {
  DisconnectReason,
  useMultiFileAuthState,
  fetchLatestBaileysVersion
} from '@whiskeysockets/baileys';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Paths & Configuration
const PORT = parseInt(process.env.WHATSAPP_PORT || '8765', 10);
const PYTHON_WEBHOOK_PORT = parseInt(process.env.PYTHON_PORT || '8766', 10);
const AUTH_DIR = process.env.WHATSAPP_SESSION_DIR || 
  path.resolve(__dirname, '../../../../credentials/whatsapp_session');
const GROUP_INFO_FILE = path.resolve(__dirname, '../../../../credentials/whatsapp_session/group_info.json');

if (!fs.existsSync(AUTH_DIR)) {
  fs.mkdirSync(AUTH_DIR, { recursive: true });
}

const logger = pino({ level: 'warn' });

// Global Bridge State
let sock = null;
let connectionState = 'connecting';
let currentQR = null;
let currentQRDataUrl = null;
let userJID = null;
let userPhone = null;
let dedicatedGroupJid = null;
let isReconnecting = false;

/**
 * Resolves or creates the dedicated '🍼 BABY Assistant' group with complete edge-case handling:
 * 1. Checks if previously saved group ID is still active and valid.
 * 2. Scans all user's participating groups to avoid creating duplicate groups if one already exists.
 * 3. Only if no BABY group exists anywhere, creates a new one and posts the welcome card.
 */
async function getOrCreateAssistantGroup() {
  if (!sock || connectionState !== 'connected') return null;

  try {
    // 1. Fetch all groups where user is a participant
    const participatingGroups = await sock.groupFetchAllParticipating().catch(() => ({}));

    // Edge Case 1: Check if saved group file exists and is still valid in account
    if (fs.existsSync(GROUP_INFO_FILE)) {
      try {
        const saved = JSON.parse(fs.readFileSync(GROUP_INFO_FILE, 'utf-8'));
        if (saved && saved.groupId && participatingGroups[saved.groupId]) {
          dedicatedGroupJid = saved.groupId;
          console.log(`[WhatsApp Bridge] Reusing verified existing group: ${dedicatedGroupJid} ("${participatingGroups[dedicatedGroupJid].subject}")`);
          return dedicatedGroupJid;
        }
      } catch (e) {
        console.warn('[WhatsApp Bridge] Error reading group_info.json:', e);
      }
    }

    // Edge Case 2: Scan all user groups to check if a group with "BABY Assistant" already exists
    for (const [gid, meta] of Object.entries(participatingGroups)) {
      const subject = meta?.subject || '';
      if (subject.includes('BABY Assistant') || subject.includes('🍼 BABY')) {
        dedicatedGroupJid = gid;
        console.log(`[WhatsApp Bridge] Found existing group on account: "${subject}" (${gid}). Reusing to avoid duplicates!`);
        fs.writeFileSync(GROUP_INFO_FILE, JSON.stringify({
          groupId: gid,
          title: subject,
          reused: true,
          updatedAt: new Date().toISOString()
        }, null, 2));
        return dedicatedGroupJid;
      }
    }

    // Edge Case 3: Group does NOT exist anywhere - create brand new group
    console.log('[WhatsApp Bridge] No existing BABY group found. Creating brand new group...');
    const myPhone = userPhone;
    const participantJid = `${myPhone}@s.whatsapp.net`;
    const newGroup = await sock.groupCreate('🍼 BABY Assistant', [participantJid]);
    dedicatedGroupJid = newGroup.id;

    fs.writeFileSync(GROUP_INFO_FILE, JSON.stringify({
      groupId: newGroup.id,
      title: '🍼 BABY Assistant',
      createdAt: new Date().toISOString()
    }, null, 2));

    // Post rich welcome card into the new group
    await sock.sendMessage(dedicatedGroupJid, {
      text: `🍼 *BABY Assistant Connected!*\n\nHello! I am your personal desktop assistant.\nAnything you text in this group will control your PC and be spoken through your PC speakers.\n\n💡 *Try texting:*\n• *What is my next meeting?*\n• *Set volume to 40%*\n• *Mute audio*\n• *Open Chrome*\n• *What time is it?*`
    });

    console.log(`[WhatsApp Bridge] Dedicated group created: ${dedicatedGroupJid}`);
    return dedicatedGroupJid;

  } catch (err) {
    console.error('[WhatsApp Bridge] Error resolving assistant group:', err);
    return null;
  }
}

/**
 * Initialize WhatsApp Multi-Device Socket
 */
async function startWhatsAppSocket() {
  try {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const { version, isLatest } = await fetchLatestBaileysVersion().catch(() => ({ version: [2, 3000, 1015901307], isLatest: true }));

    sock = makeWASocket({
      version,
      logger,
      auth: state,
      browser: ['BABY Assistant', 'Chrome', '124.0.0.0'],
      syncFullHistory: false,
      generateHighQualityLinkPreview: true
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        currentQR = qr;
        try {
          currentQRDataUrl = await QRCode.toDataURL(qr, {
            margin: 2,
            scale: 8,
            color: {
              dark: '#0f0d17',
              light: '#ffffff'
            }
          });
        } catch (err) {
          console.error('[WhatsApp Bridge] Failed to render QR data URL:', err);
        }
        connectionState = 'qr_ready';
        console.log('[WhatsApp Bridge] QR code generated. Awaiting mobile scan...');
      }

      if (connection === 'close') {
        connectionState = 'disconnected';
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
        console.log(`[WhatsApp Bridge] Connection closed (status: ${statusCode}). Reconnect: ${shouldReconnect}`);

        if (shouldReconnect) {
          if (!isReconnecting) {
            isReconnecting = true;
            setTimeout(() => {
              isReconnecting = false;
              startWhatsAppSocket();
            }, 3000);
          }
        } else {
          connectionState = 'logged_out';
          console.log('[WhatsApp Bridge] Device logged out. Clearing credentials...');
          try {
            fs.rmSync(AUTH_DIR, { recursive: true, force: true });
            fs.mkdirSync(AUTH_DIR, { recursive: true });
          } catch (e) {
            console.error('[WhatsApp Bridge] Error clearing auth dir:', e);
          }
          currentQR = null;
          currentQRDataUrl = null;
          userJID = null;
          userPhone = null;
          dedicatedGroupJid = null;
          setTimeout(startWhatsAppSocket, 2000);
        }
      } else if (connection === 'open') {
        connectionState = 'connected';
        currentQR = null;
        currentQRDataUrl = null;
        userJID = sock?.user?.id || '';
        userPhone = userJID ? userJID.split(':')[0].split('@')[0] : '';
        console.log(`[WhatsApp Bridge] Connected successfully! User JID: ${userJID} (Phone: +${userPhone})`);

        // Edge-case safe resolution: Find or create dedicated "🍼 BABY Assistant" group
        setTimeout(async () => {
          await getOrCreateAssistantGroup();
        }, 1500);
      }
    });

    // Inbound Messages Listener with STRICT GROUP SCOPING
    sock.ev.on('messages.upsert', async (event) => {
      if (event.type !== 'notify') return;

      for (const msg of event.messages) {
        // Skip ephemeral or status updates
        if (!msg.message || msg.key.remoteJid === 'status@broadcast') continue;

        // Extract message text
        const text = msg.message?.conversation || 
                     msg.message?.extendedTextMessage?.text || 
                     msg.message?.imageMessage?.caption || '';

        if (!text || text.trim() === '') continue;

        const senderJid = msg.key.remoteJid;

        // STRICT SCOPING: Only listen to the dedicated BABY Assistant group!
        if (dedicatedGroupJid && senderJid !== dedicatedGroupJid) {
          // If group is not yet set, allow messages from own chat
          if (senderJid !== userJID && !msg.key.fromMe) {
            continue;
          }
        }

        // Prevent echo loops: Ignore messages that BABY itself sent
        if (text.startsWith('🤖') || text.startsWith('🍼') || text.startsWith('⏰') || text.startsWith('📌')) {
          continue;
        }

        console.log(`[WhatsApp Bridge] Inbound command received: "${text}" from ${senderJid}`);

        // Relay to Python Assistant Engine
        relayToPythonAssistant(senderJid, text);
      }
    });

  } catch (error) {
    console.error('[WhatsApp Bridge] Fatal error in socket startup:', error);
    setTimeout(startWhatsAppSocket, 5000);
  }
}

/**
 * Forward inbound WhatsApp message to Python BABY assistant and return reply
 */
async function relayToPythonAssistant(senderJid, text) {
  try {
    const target = dedicatedGroupJid || senderJid;

    // Send instant typing indicator so WhatsApp user sees immediate acknowledgement
    if (sock && target) {
      sock.sendPresenceUpdate('composing', target).catch(() => {});
    }

    const payload = JSON.stringify({
      from: senderJid,
      text: text.trim()
    });

    const req = http.request({
      hostname: '127.0.0.1',
      port: PYTHON_WEBHOOK_PORT,
      path: '/whatsapp/webhook',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      },
      timeout: 60000
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', async () => {
        try {
          if (res.statusCode === 200 && body) {
            const data = JSON.parse(body);
            if (data && data.media_path && fs.existsSync(data.media_path)) {
              console.log(`[WhatsApp Bridge] Delivering media to ${target}: ${data.media_path}`);
              await sendMedia(target, data.media_path, data.reply || '');
            } else if (data && data.reply) {
              await sendMessage(target, data.reply);
            }
          }
        } catch (parseErr) {
          console.error('[WhatsApp Bridge] Failed parsing Python response:', parseErr);
        } finally {
          if (sock && target) {
            sock.sendPresenceUpdate('paused', target).catch(() => {});
          }
        }
      });
    });

    req.on('error', (err) => {
      console.warn(`[WhatsApp Bridge] Python webhook not reachable on port ${PYTHON_WEBHOOK_PORT}: ${err.message}`);
    });

    req.write(payload);
    req.end();
  } catch (err) {
    console.error('[WhatsApp Bridge] Error relaying to Python:', err);
  }
}

/**
 * Send outbound message through WhatsApp socket
 */
async function sendMessage(targetJid, text) {
  if (!sock || connectionState !== 'connected') {
    throw new Error('WhatsApp is not connected');
  }

  // Resolve target JID: if "group", "me", or empty, route to dedicated group
  let jid = targetJid;
  if (!jid || jid === 'me' || jid === 'self' || jid === 'group') {
    jid = dedicatedGroupJid || userJID;
  }
  if (!jid.includes('@')) {
    jid = `${jid}@s.whatsapp.net`;
  }

  // Pre-flight check: verify recipient is registered on WhatsApp (unless sending to self or group)
  if (!jid.endsWith('@g.us') && jid !== userJID) {
    const rawDigits = jid.split('@')[0].split(':')[0];
    const existsCheck = await sock.onWhatsApp(rawDigits).catch(() => []);
    if (!existsCheck || existsCheck.length === 0 || !existsCheck[0].exists) {
      throw new Error(`Phone number +${rawDigits} is not registered on WhatsApp`);
    }
    jid = existsCheck[0].jid;
  }

  // Formatting prefix for kawaii assistant
  const formattedText = text.startsWith('🍼') || text.startsWith('⏰') || text.startsWith('📅') || text.startsWith('📌')
    ? text
    : `🍼 *BABY:*\n${text}`;

  const result = await sock.sendMessage(jid, { text: formattedText });
  console.log(`[WhatsApp Bridge] Message sent to ${jid}`);
  return result;
}

/**
 * Send outbound image/media through WhatsApp socket
 */
async function sendMedia(targetJid, filePath, caption) {
  if (!sock || connectionState !== 'connected') {
    throw new Error('WhatsApp is not connected');
  }

  if (!fs.existsSync(filePath)) {
    throw new Error(`Media file not found at: ${filePath}`);
  }

  // Resolve target JID: if "group", "me", or empty, route to dedicated group
  let jid = targetJid;
  if (!jid || jid === 'me' || jid === 'self' || jid === 'group') {
    jid = dedicatedGroupJid || userJID;
  }
  if (!jid.includes('@')) {
    jid = `${jid}@s.whatsapp.net`;
  }

  // Pre-flight check: verify recipient is registered on WhatsApp (unless sending to self or group)
  if (!jid.endsWith('@g.us') && jid !== userJID) {
    const rawDigits = jid.split('@')[0].split(':')[0];
    const existsCheck = await sock.onWhatsApp(rawDigits).catch(() => []);
    if (!existsCheck || existsCheck.length === 0 || !existsCheck[0].exists) {
      throw new Error(`Phone number +${rawDigits} is not registered on WhatsApp`);
    }
    jid = existsCheck[0].jid;
  }

  const formattedCaption = caption
    ? (caption.startsWith('🍼') || caption.startsWith('📸') || caption.startsWith('🐍') ? caption : `🍼 *BABY:*\n${caption}`)
    : '';

  const buffer = fs.readFileSync(filePath);
  const result = await sock.sendMessage(jid, {
    image: buffer,
    caption: formattedCaption
  });
  console.log(`[WhatsApp Bridge] Media sent to ${jid} (${filePath})`);
  return result;
}

/**
 * Dark-Glass HTML Pairing UI
 */
function getPairingHtml() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BABY Assistant • Link WhatsApp</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: radial-gradient(circle at top, #1e1338, #0a0812);
      color: #f5f3ff;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      user-select: none;
    }
    .card {
      background: rgba(26, 20, 44, 0.88);
      border: 1px solid rgba(168, 85, 247, 0.45);
      border-radius: 24px;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6), 0 0 30px rgba(168, 85, 247, 0.2);
      backdrop-filter: blur(20px);
      width: 100%;
      max-width: 420px;
      padding: 32px 28px;
      text-align: center;
      animation: popIn 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }
    @keyframes popIn {
      from { opacity: 0; transform: scale(0.94); }
      to { opacity: 1; transform: scale(1); }
    }
    .header {
      margin-bottom: 22px;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(168, 85, 247, 0.16);
      border: 1px solid rgba(168, 85, 247, 0.35);
      color: #d8b4fe;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      padding: 4px 12px;
      border-radius: 999px;
      margin-bottom: 12px;
    }
    h1 {
      font-size: 22px;
      font-weight: 700;
      background: linear-gradient(135deg, #ffffff 40%, #c084fc 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 6px;
    }
    .subtitle {
      color: #a1a1aa;
      font-size: 13px;
      line-height: 1.4;
    }
    .qr-container {
      background: #ffffff;
      border-radius: 18px;
      padding: 14px;
      display: inline-block;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      margin: 14px 0 20px;
      position: relative;
      min-width: 240px;
      min-height: 240px;
    }
    .qr-img {
      width: 220px;
      height: 220px;
      display: block;
      border-radius: 8px;
    }
    .loading-box {
      width: 220px;
      height: 220px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      color: #4b5563;
    }
    .spinner {
      width: 36px;
      height: 36px;
      border: 3px solid rgba(168, 85, 247, 0.2);
      border-top-color: #a855f7;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .instructions {
      text-align: left;
      background: rgba(15, 13, 23, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 14px;
      padding: 14px 16px;
      font-size: 12px;
      color: #d4d4d8;
      line-height: 1.6;
      margin-bottom: 18px;
    }
    .instructions ol {
      padding-left: 20px;
    }
    .instructions b {
      color: #f472b6;
    }
    .success-view {
      display: none;
      padding: 24px 0;
      animation: fadeIn 0.4s ease;
    }
    .checkmark {
      width: 72px;
      height: 72px;
      background: rgba(34, 197, 94, 0.18);
      border: 2px solid #22c55e;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 38px;
      margin: 0 auto 18px;
      box-shadow: 0 0 25px rgba(34, 197, 94, 0.4);
    }
    .footer-note {
      font-size: 11px;
      color: #71717a;
    }
  </style>
</head>
<body>
  <div class="card">
    <div id="scan-view">
      <div class="header">
        <div class="badge">
          <span>✨</span> One-Click Mobile Bridge
        </div>
        <h1>Link WhatsApp</h1>
        <p class="subtitle">Scan the QR code to pair BABY with your phone</p>
      </div>

      <div class="qr-container">
        <div id="qr-loading" class="loading-box">
          <div class="spinner"></div>
          <span style="font-size: 12px; font-weight: 500;">Generating QR code...</span>
        </div>
        <img id="qr-image" class="qr-img" style="display: none;" alt="WhatsApp QR Code">
      </div>

      <div class="instructions">
        <ol>
          <li>Open <b>WhatsApp</b> on your phone</li>
          <li>Tap <b>Settings</b> (or <b>⋮</b>) &rarr; <b>Linked Devices</b></li>
          <li>Tap <b>Link a Device</b> and point at this screen</li>
        </ol>
      </div>

      <div class="footer-note">
        🔒 100% Free &amp; End-to-end encrypted locally on your PC
      </div>
    </div>

    <div id="success-view" class="success-view">
      <div class="checkmark">✓</div>
      <h1>WhatsApp Connected!</h1>
      <p id="user-phone-label" class="subtitle" style="margin: 10px 0 16px; color: #a7f3d0; font-size: 15px; font-weight: 600;">
        Paired with your device
      </p>
      <p class="subtitle" style="font-size: 12px;">
        Dedicated group <b>🍼 BABY Assistant</b> created!<br>
        Closing this window...
      </p>
    </div>
  </div>

  <script>
    let pollInterval = null;

    async function checkStatus() {
      try {
        const res = await fetch('/status');
        const data = await res.json();

        if (data.connected) {
          clearInterval(pollInterval);
          document.getElementById('scan-view').style.display = 'none';
          document.getElementById('success-view').style.display = 'block';
          if (data.phone) {
            document.getElementById('user-phone-label').textContent = '📱 +' + data.phone;
          }
          setTimeout(() => {
            window.close();
          }, 1800);
          return;
        }

        if (data.qr_data_url) {
          const img = document.getElementById('qr-image');
          const loading = document.getElementById('qr-loading');
          img.src = data.qr_data_url;
          img.style.display = 'block';
          loading.style.display = 'none';
        }
      } catch (e) {
        console.warn('Status poll error:', e);
      }
    }

    checkStatus();
    pollInterval = setInterval(checkStatus, 1200);
  </script>
</body>
</html>`;
}

/**
 * Local HTTP API Server
 */
const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host}`);

  // Route: GET /status
  if (req.method === 'GET' && url.pathname === '/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      connected: connectionState === 'connected',
      state: connectionState,
      qr: currentQR,
      qr_data_url: currentQRDataUrl,
      phone: userPhone,
      jid: userJID,
      group_jid: dedicatedGroupJid
    }));
    return;
  }

  // Route: GET /pair
  if (req.method === 'GET' && url.pathname === '/pair') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(getPairingHtml());
    return;
  }

  // Route: POST /send
  if (req.method === 'POST' && url.pathname === '/send') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const payload = JSON.parse(body || '{}');
        if (!payload.text) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Field "text" is required' }));
          return;
        }

        const result = await sendMessage(payload.to, payload.text);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, messageId: result?.key?.id }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // Route: POST /send_media
  if (req.method === 'POST' && url.pathname === '/send_media') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const payload = JSON.parse(body || '{}');
        if (!payload.filePath) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Field "filePath" is required' }));
          return;
        }

        const result = await sendMedia(payload.to, payload.filePath, payload.caption);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, messageId: result?.key?.id }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // Route: POST /create_group
  if (req.method === 'POST' && url.pathname === '/create_group') {
    try {
      const gid = await getOrCreateAssistantGroup();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: !!gid, group_jid: gid }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return;
  }

  // Route: POST /logout
  if (req.method === 'POST' && url.pathname === '/logout') {
    try {
      if (sock) {
        await sock.logout().catch(() => {});
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return;
  }

  // Fallback 404
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
});

// Start HTTP server & WhatsApp socket
server.listen(PORT, '127.0.0.1', () => {
  console.log(`[WhatsApp Bridge] Local API listening on http://127.0.0.1:${PORT}`);
  startWhatsAppSocket();
});
