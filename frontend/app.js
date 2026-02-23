'use strict';

// ── DOM refs ─────────────────────────────────────────────────────────────────
const messagesEl   = document.getElementById('messages');
const promptInput  = document.getElementById('promptInput');
const sendBtn      = document.getElementById('sendBtn');
const sendIcon     = document.getElementById('sendIcon');
const spinner      = document.getElementById('spinner');
const actorIdEl    = document.getElementById('actorId');
const threadIdEl   = document.getElementById('threadId');
const sessionPanel = document.getElementById('sessionPanel');
const sessionToggle= document.getElementById('sessionToggle');
const clearBtn     = document.getElementById('clearBtn');

// ── Session toggle ────────────────────────────────────────────────────────────
sessionToggle.addEventListener('click', () => {
  sessionPanel.classList.toggle('open');
});

clearBtn.addEventListener('click', () => {
  messagesEl.innerHTML = '';
  showWelcome();
});

// ── Auto-resize textarea ──────────────────────────────────────────────────────
promptInput.addEventListener('input', () => {
  promptInput.style.height = 'auto';
  promptInput.style.height = Math.min(promptInput.scrollHeight, 160) + 'px';
});

// ── Enter to send (Shift+Enter = new line) ────────────────────────────────────
promptInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});

sendBtn.addEventListener('click', handleSend);

// ── Main send handler ─────────────────────────────────────────────────────────
async function handleSend() {
  const prompt = promptInput.value.trim();
  if (!prompt || sendBtn.disabled) return;

  const actorId  = actorIdEl.value.trim()  || 'web-user';
  const threadId = threadIdEl.value.trim() || 'web-session-1';

  removeWelcome();
  appendMessage('user', prompt);
  clearInput();
  setLoading(true);

  const typingEl = appendTyping();

  try {
    const res = await fetch('/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ prompt, actor_id: actorId, thread_id: threadId }),
    });

    const data = await res.json();
    removeTyping(typingEl);

    if (!res.ok || data.error) {
      appendMessage('bot', data.error || `HTTP ${res.status}`, true);
    } else {
      appendMessage('bot', formatBotText(data.result || 'No response.'));
    }
  } catch (err) {
    removeTyping(typingEl);
    appendMessage('bot', `Connection error: ${err.message}`, true);
  } finally {
    setLoading(false);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function appendMessage(role, text, isError = false) {
  const msg    = document.createElement('div');
  msg.className = `msg ${role}`;

  const label  = document.createElement('div');
  label.className = 'msg-label';
  label.textContent = role === 'user' ? 'You' : 'Lauki Agent';

  const bubble = document.createElement('div');
  bubble.className = `bubble${isError ? ' error' : ''}`;
  bubble.innerHTML = text;   // already sanitised by formatBotText for bot; plain for user

  // For user messages sanitise properly
  if (role === 'user') bubble.textContent = text;

  msg.append(label, bubble);
  messagesEl.appendChild(msg);
  scrollToBottom();
  return msg;
}

function appendTyping() {
  const msg  = document.createElement('div');
  msg.className = 'msg bot typing';

  const label = document.createElement('div');
  label.className = 'msg-label';
  label.textContent = 'Lauki Agent';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

  msg.append(label, bubble);
  messagesEl.appendChild(msg);
  scrollToBottom();
  return msg;
}

function removeTyping(el) {
  if (el && el.parentNode) el.parentNode.removeChild(el);
}

/**
 * Minimal bot-text formatter:
 * - **bold** → <strong>
 * - `code` → <code>
 * - Newlines preserved via CSS white-space:pre-wrap
 */
function formatBotText(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function clearInput() {
  promptInput.value = '';
  promptInput.style.height = 'auto';
}

function setLoading(on) {
  sendBtn.disabled = on;
  sendIcon.classList.toggle('hidden', on);
  spinner.classList.toggle('hidden', !on);
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function removeWelcome() {
  const w = messagesEl.querySelector('.welcome');
  if (w) w.remove();
}

function showWelcome() {
  const w = document.createElement('div');
  w.className = 'welcome';
  w.innerHTML = `
    <div class="welcome-icon">&#129302;</div>
    <p>Hi! I'm the Lauki FAQ Agent. Ask me anything about Lauki Mobile's network, plans, or services.</p>
  `;
  messagesEl.appendChild(w);
}
