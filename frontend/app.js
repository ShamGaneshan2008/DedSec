/* =========================
   ELEMENTS
========================= */
const lava        = document.getElementById('lava');
const sphere      = document.getElementById('sphere');
const rings       = document.getElementById('rings');
const orbLabel    = document.getElementById('orbLabel');
const waveform    = document.getElementById('waveform');
const transcript  = document.getElementById('transcript');
const controls    = document.getElementById('controls');
const micBtn      = document.getElementById('micBtn');
const chatPanel   = document.getElementById('chatPanel');
const messages    = document.getElementById('messages');
const chatInput   = document.getElementById('chatInput');
const sendBtn     = document.getElementById('sendBtn');
const typing      = document.getElementById('typing');
const statusLabel = document.getElementById('statusLabel');
const btnVoice    = document.getElementById('btnVoice');
const btnChat     = document.getElementById('btnChat');

/* =========================
   WAVEFORM BARS
========================= */
for (let i = 0; i < 52; i++) {
  const b = document.createElement('div');
  b.className = 'bar';
  b.style.animationDelay    = (Math.random() * 1.6) + 's';
  b.style.animationDuration = (0.9 + Math.random() * 0.9) + 's';
  waveform.appendChild(b);
}

/* =========================
   STATUS + LABEL
========================= */
function setStatus(t) { statusLabel.textContent = t; }

let labelTimer;
function showLabel(text, persist) {
  clearTimeout(labelTimer);
  orbLabel.textContent = text;
  orbLabel.classList.add('show');
  if (!persist) labelTimer = setTimeout(() => orbLabel.classList.remove('show'), 3200);
}

/* =========================
   IDLE LOOP
========================= */
const idleLines = ["Hello — I'm Marcus.", "How can I help?", "Ask me anything.", "Tap to start speaking."];
let idleIdx = 0, idleLoop = null;

function startIdle() {
  setStatus('Ready');
  showLabel(idleLines[idleIdx], true);
  idleLoop = setInterval(() => {
    idleIdx = (idleIdx + 1) % idleLines.length;
    showLabel(idleLines[idleIdx], true);
  }, 4000);
}
function stopIdle() { clearInterval(idleLoop); idleLoop = null; }

/* =========================
   WEBSOCKET
========================= */
const WS_URL = 'ws://127.0.0.1:8000/ws';
let ws = null;
let wsReady = false;
let pendingResolve = null;
let streamBuffer = '';
let currentAiBubble = null;

function connectWS() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    wsReady = true;
    console.log('[Marcus] WebSocket connected');
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {

      case 'connected':
        if (data.user && data.user !== 'Operative') {
          idleLines[0] = `Hello, ${data.user} — I'm Marcus.`;
        }
        startIdle();
        break;

      case 'thinking':
        typing.classList.add('show');
        messages.scrollTop = messages.scrollHeight;
        streamBuffer = '';
        currentAiBubble = null;
        break;

      case 'token':
        typing.classList.remove('show');
        waveform.querySelectorAll('.bar').forEach(b => b.classList.add('active'));
        streamBuffer += data.text;
        if (!currentAiBubble) {
          currentAiBubble = document.createElement('div');
          currentAiBubble.className = 'bubble ai';
          messages.insertBefore(currentAiBubble, typing);
        }
        currentAiBubble.textContent = streamBuffer;
        messages.scrollTop = messages.scrollHeight;
        break;

      case 'done':
        typing.classList.remove('show');
        waveform.querySelectorAll('.bar').forEach(b => b.classList.remove('active'));
        streamBuffer = '';
        currentAiBubble = null;
        if (pendingResolve) { pendingResolve(data.text); pendingResolve = null; }
        if (mode === 'chat') { showLabel('Type a message below', true); setStatus('Chat'); }
        break;

      case 'response':
        typing.classList.remove('show');
        waveform.querySelectorAll('.bar').forEach(b => b.classList.add('active'));
        addBubble('ai', data.text);
        setTimeout(() => waveform.querySelectorAll('.bar').forEach(b => b.classList.remove('active')), 600);
        if (pendingResolve) { pendingResolve(data.text); pendingResolve = null; }
        if (mode === 'chat') { showLabel('Type a message below', true); setStatus('Chat'); }
        break;

      case 'subtitle':
        transcript.textContent = data.text;
        transcript.classList.add('show');
        break;

      case 'clear_subtitle':
        transcript.classList.remove('show');
        break;

      case 'error':
        console.error('[Marcus WS error]', data.text);
        typing.classList.remove('show');
        if (pendingResolve) { pendingResolve("Something went wrong on my end."); pendingResolve = null; }
        break;

      case 'pong':
        break;
    }
  };

  ws.onclose = () => {
    wsReady = false;
    console.warn('[Marcus] WebSocket closed — reconnecting in 2s…');
    setTimeout(connectWS, 2000);
  };

  ws.onerror = (err) => {
    console.error('[Marcus] WebSocket error', err);
    wsReady = false;
  };
}

connectWS();

/* =========================
   SEND MESSAGE VIA WS
========================= */
function sendToMarcus(text) {
  return new Promise((resolve) => {
    if (!wsReady) {
      resolve("Not connected to Marcus yet — please wait a moment.");
      return;
    }
    pendingResolve = resolve;
    ws.send(JSON.stringify({ type: 'message', text }));
  });
}

/* =========================
   MODE SWITCH
========================= */
let mode = 'voice';
function setMode(m) {
  mode = m;
  btnVoice.classList.toggle('active', m === 'voice');
  btnChat.classList.toggle('active',  m === 'chat');
  const isChat = m === 'chat';

  lava.classList.toggle('raised',     isChat);
  sphere.classList.toggle('raised',   isChat);
  rings.classList.toggle('raised',    isChat);
  orbLabel.classList.toggle('raised', isChat);
  waveform.classList.toggle('raised', isChat);

  chatPanel.classList.toggle('open',  isChat);
  controls.classList.toggle('hidden', isChat);
  transcript.classList.remove('show');

  stopIdle();
  if (isChat) {
    showLabel('Type a message below', true);
    setStatus('Chat');
    setTimeout(() => chatInput.focus(), 600);
  } else {
    startIdle();
  }
}

/* =========================
   VOICE RECORDING
   Uses MediaRecorder → sends audio blob to /transcribe
   → Groq Whisper on the backend → text → Marcus
========================= */
let mediaRecorder = null;
let audioChunks   = [];
let isRecording   = false;
let micStream     = null;

const MIC_SVG  = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10a7 7 0 0 0 14 0"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="9" y1="22" x2="15" y2="22"/></svg>`;
const STOP_SVG = `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="5" width="14" height="14" rx="2"/></svg>`;

function setRecordingUI(on) {
  isRecording = on;
  micBtn.innerHTML = on ? STOP_SVG : MIC_SVG;
  micBtn.classList.toggle('recording', on);
  sphere.classList.toggle('listening', on);
  lava.classList.toggle('listening', on);
  rings.querySelectorAll('.ring').forEach(r => r.classList.toggle('active', on));
  // Bars animate while recording
  waveform.querySelectorAll('.bar').forEach(b => b.classList.toggle('active', on));
}

async function startRecording() {
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (err) {
    showLabel('Mic access denied', true);
    setStatus('Error');
    setTimeout(startIdle, 3000);
    return;
  }

  audioChunks = [];

  // Pick best supported format
  const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
    ? 'audio/webm;codecs=opus'
    : MediaRecorder.isTypeSupported('audio/webm')
    ? 'audio/webm'
    : 'audio/ogg';

  mediaRecorder = new MediaRecorder(micStream, { mimeType });

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) audioChunks.push(e.data);
  };

  mediaRecorder.onstop = async () => {
    // Stop all mic tracks
    micStream.getTracks().forEach(t => t.stop());
    micStream = null;

    const blob = new Blob(audioChunks, { type: mimeType });
    audioChunks = [];

    // Must have at least ~0.5s of audio
    if (blob.size < 3000) {
      showLabel("Didn't catch that — try again", true);
      setStatus('Error');
      setTimeout(startIdle, 2500);
      return;
    }

    // Send to backend /transcribe (Groq Whisper)
    showLabel('Transcribing…', true);
    setStatus('Transcribing');

    try {
      const form = new FormData();
      form.append('audio', blob, 'audio.webm');

      const res = await fetch('http://127.0.0.1:8000/transcribe', {
        method: 'POST',
        body: form
      });

      const json = await res.json();

      if (json.error) {
        console.error('[Transcribe error]', json.error);
        showLabel("Couldn't transcribe — try again", true);
        setStatus('Error');
        setTimeout(startIdle, 2500);
        return;
      }

      const text = json.transcript?.trim();
      if (!text) {
        showLabel("Didn't catch that — try again", true);
        setStatus('Error');
        setTimeout(startIdle, 2500);
        return;
      }

      // Show what was heard
      transcript.textContent = '\u201c' + text + '\u201d';
      transcript.classList.add('show');

      await handleVoice(text);

    } catch (err) {
      console.error('[Transcribe fetch error]', err);
      showLabel('Server error — is Marcus running?', true);
      setStatus('Error');
      setTimeout(startIdle, 3000);
    }
  };

  mediaRecorder.start();
  setRecordingUI(true);
  stopIdle();
  showLabel('Listening…', true);
  setStatus('Listening');
  transcript.textContent = '';
  transcript.classList.add('show');
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  // Bars go idle while transcribing — re-activated by 'token' events
  waveform.querySelectorAll('.bar').forEach(b => b.classList.remove('active'));
  setRecordingUI(false);
}

micBtn.addEventListener('click', () => {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

/* =========================
   HANDLE VOICE REPLY
========================= */
async function handleVoice(text) {
  showLabel('Thinking…', true);
  setStatus('Processing');
  sphere.classList.add('speaking');
  lava.classList.add('speaking');

  // Bars activate on 'token', deactivate on 'done' via ws.onmessage
  const reply = await sendToMarcus(text);

  // Re-activate bars while backend TTS plays
  waveform.querySelectorAll('.bar').forEach(b => b.classList.add('active'));
  showLabel(reply.length > 62 ? reply.slice(0, 59) + '…' : reply, true);
  setStatus('Speaking');

  setTimeout(() => {
    transcript.classList.remove('show');
    sphere.classList.remove('speaking');
    lava.classList.remove('speaking');
    waveform.querySelectorAll('.bar').forEach(b => b.classList.remove('active'));
    startIdle();
  }, Math.max(3000, reply.length * 55));
}

/* =========================
   CHAT PANEL
========================= */
function addBubble(role, text) {
  const d = document.createElement('div');
  d.className = 'bubble ' + role;
  d.textContent = text;
  messages.insertBefore(d, typing);
  messages.scrollTop = messages.scrollHeight;
}

async function sendChat() {
  const msg = chatInput.value.trim();
  if (!msg) return;
  chatInput.value = '';
  addBubble('user', msg);
  typing.classList.add('show');
  messages.scrollTop = messages.scrollHeight;
  showLabel('Thinking…', true);
  setStatus('Processing');
  await sendToMarcus(msg);
}

sendBtn.addEventListener('click', sendChat);
chatInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendChat(); });

/* =========================
   KEEP-ALIVE PING
========================= */
setInterval(() => {
  if (wsReady) ws.send(JSON.stringify({ type: 'ping' }));
}, 25000);