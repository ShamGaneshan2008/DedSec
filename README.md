<div align="center">

```
██████╗ ███████╗██████╗ ███████╗███████╗ ██████╗
██╔══██╗██╔════╝██╔══██╗██╔════╝██╔════╝██╔════╝
██║  ██║█████╗  ██║  ██║███████╗█████╗  ██║
██║  ██║██╔══╝  ██║  ██║╚════██║██╔══╝  ██║
██████╔╝███████╗██████╔╝███████║███████╗╚██████╗
╚═════╝ ╚══════╝╚═════╝ ╚══════╝╚══════╝ ╚═════╝
```

### `[ AI VOICE ASSISTANT — v1.0.0 ]`

*A modular, conversational AI voice assistant built with Python*  
*capable of listening, thinking, and speaking back*

![Python](https://img.shields.io/badge/Python-3.10+-00ff88?style=flat-square&logo=python&logoColor=black)
![Groq](https://img.shields.io/badge/LLM-Groq_API-00e5ff?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-00ff88?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-ffffff?style=flat-square)

</div>

---

## ⟫ Overview

**DedSec** is a Python-based AI voice assistant that captures your voice, processes it through a large language model, and responds with synthesized speech. Built with modularity at its core — drop in new skills, connect new APIs, and extend without limits.

---

## ⟫ Core Systems

| # | Module | Function |
|---|--------|----------|
| `SYS_01` | **Voice Input** | Real-time mic capture with noise filtering |
| `SYS_02` | **LLM Brain** | Routes queries via Groq / OpenAI |
| `SYS_03` | **TTS Output** | Synthesizes natural speech back |
| `SYS_04` | **Modular Skills** | Drop-in command modules |
| `SYS_05` | **Local First** | Runs on your machine — no cloud dependency |
| `SYS_06` | **Session Context** | Persistent conversation thread |

---

## ⟫ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | `Python 3.10+` |
| Speech Recognition | `SpeechRecognition` / `Whisper` |
| Language Model | `Groq API` / `OpenAI API` |
| Text-to-Speech | `pyttsx3` / `gTTS` |
| Audio I/O | `PyAudio` / `playsound` |
| Config | `python-dotenv` |

---

## ⟫ Project Structure

```
DedSec/
├── main.py              # Entry point — bootstraps the assistant
├── listener.py          # Mic capture & speech-to-text
├── brain.py             # LLM query handler & session context
├── speaker.py           # TTS output engine
├── commands/            # Modular skill handlers
│   ├── weather.py
│   ├── search.py
│   └── ...
├── config.py            # Runtime settings
├── .env                 # Secret keys — never commit
├── requirements.txt
└── README.md
```

---

## ⟫ Setup Protocol

**01 — Clone**
```bash
git clone https://github.com/ShamGaneshan2008/dedsec-voice-assistant.git
cd dedsec-voice-assistant
```

**02 — Install**
```bash
pip install -r requirements.txt

# Linux:   sudo apt-get install portaudio19-dev
# macOS:   brew install portaudio
# Windows: pip install pipwin && pipwin install pyaudio
```

**03 — Configure**
```env
# .env
GROQ_API_KEY=your_groq_api_key_here
```

**04 — Initialize**
```bash
python main.py
```

---

## ⟫ Live Session

```
Initializing DedSec v1.0.0 ...
Loading brain module     [OK]
Loading listener module  [OK]
Loading speaker module   [OK]

[DedSec]  Listening ...

» Voice detected — transcribing
You:      "What's the weather today?"

» Querying LLM ...
[DedSec]  "It's currently 28°C and sunny in your area."

[DedSec]  Listening ... █
```

---

## ⟫ Roadmap

- [x] Voice input pipeline
- [x] LLM integration
- [x] TTS output
- [ ] Wake word detection
- [ ] System tray GUI overlay
- [ ] Local LLM support via Ollama
- [ ] Smart home device control
- [ ] Persistent memory layer
- [ ] Plugin marketplace

---

## ⟫ Requirements

```
speechrecognition
pyaudio
pyttsx3
groq
python-dotenv
requests
```

---

## ⟫ Contributing

Pull requests are welcome. For major changes, open an issue first to discuss.

---

## ⟫ License

[MIT](LICENSE) — built by [@ShamGaneshan2008](https://github.com/ShamGaneshan2008)

---

<div align="center">
<sub>LISTEN · THINK · SPEAK · EVOLVE</sub>
</div>
