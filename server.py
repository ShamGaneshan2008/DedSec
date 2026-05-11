import os
import json
import asyncio
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import webbrowser
import sys

# ── LOAD ENV ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

print("Loading .env from:", ENV_PATH)
load_dotenv(dotenv_path=ENV_PATH)

# ── IMPORT MARCUS CORE ────────────────────────────────────────────────
from backend.marcus.core.ai import AI
from backend.marcus.core.router import Router
from backend.marcus.core.memory import Memory
from backend.marcus.utils.speech import Speech

# ── MEMORY PATH ───────────────────────────────────────────────────────
MEMORY_PATH = BASE_DIR / "backend" / "data" / "memory.json"

def _load_raw() -> dict:
    try:
        with open(MEMORY_PATH, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            data = {"user_name": None, "events": data}
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"user_name": None, "events": []}

def get_user_name() -> str:
    return _load_raw().get("user_name") or "Operative"

# ── GLOBALS ───────────────────────────────────────────────────────────
current_websocket = None
main_loop = None

# ── SUBTITLE CALLBACK ─────────────────────────────────────────────────
def subtitle_callback(text: str):
    global current_websocket, main_loop
    if not current_websocket or not main_loop:
        return
    try:
        asyncio.run_coroutine_threadsafe(
            current_websocket.send_json({"type": "subtitle", "text": text}),
            main_loop
        )
    except Exception as e:
        print(f"[SUBTITLE ERROR] {e}")

# ── INIT COMPONENTS ───────────────────────────────────────────────────
memory = Memory()
ai = AI(memory)
speech = Speech(subtitle_callback=subtitle_callback)
router = Router(ai, memory, speech=speech)

# ── FASTAPI APP ───────────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── FRONTEND DIR ──────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    FRONTEND_DIR = Path(sys._MEIPASS) / "frontend"
else:
    FRONTEND_DIR = BASE_DIR / "frontend"

# ── SERVE STATIC FILES (css, js, images, etc.) ───────────────────────
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# ── SERVE INDEX ───────────────────────────────────────────────────────
@app.get("/")
def home():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/app.js")
def serve_js():
    return FileResponse(str(FRONTEND_DIR / "app.js"), media_type="application/javascript")

@app.get("/style.css")
def serve_css():
    return FileResponse(str(FRONTEND_DIR / "style.css"), media_type="text/css")

@app.get("/favicon.ico")
def favicon():
    icon_path = FRONTEND_DIR / "favicon.ico"
    if icon_path.exists():
        return FileResponse(str(icon_path))
    return JSONResponse({"status": "no favicon"})

# ── REST CHAT ─────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_rest(req: ChatRequest):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, router.handle, req.message)
    return {"response": result}

# ── TRANSCRIBE ────────────────────────────────────────────────────────
@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    try:
        import tempfile
        from pydub import AudioSegment

        contents = await audio.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        wav_path = tmp_path + ".wav"
        audio_segment = AudioSegment.from_file(tmp_path)
        audio_segment.export(wav_path, format="wav")

        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        with open(wav_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=("audio.wav", f),
                response_format="text"
            )

        transcript = result if isinstance(result, str) else result.text
        os.unlink(tmp_path)
        os.unlink(wav_path)

        return JSONResponse({"transcript": transcript.strip()})

    except Exception as e:
        print(f"[TRANSCRIBE ERROR] {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ── WEBSOCKET ─────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global current_websocket, main_loop

    await websocket.accept()
    current_websocket = websocket
    main_loop = asyncio.get_running_loop()

    user_name = get_user_name()
    await websocket.send_json({
        "type": "connected",
        "user": user_name,
        "time": datetime.now().strftime("%H:%M")
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")

            if msg_type == "message":
                text = data.get("text", "").strip()
                if not text:
                    continue

                await websocket.send_json({"type": "thinking"})

                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, router.handle_stream, text)

                if hasattr(result, '__iter__') and not isinstance(result, str):
                    full_response = ""
                    for token in result:
                        full_response += token
                        await websocket.send_json({"type": "token", "text": token})

                    await websocket.send_json({"type": "done", "text": full_response})

                    threading.Thread(
                        target=speech.speak,
                        args=(full_response,),
                        daemon=True
                    ).start()

                else:
                    await websocket.send_json({"type": "response", "text": str(result)})
                    threading.Thread(
                        target=speech.speak,
                        args=(str(result),),
                        daemon=True
                    ).start()

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "clear_subtitle":
                await websocket.send_json({"type": "clear_subtitle"})

    except WebSocketDisconnect:
        print("[MARCUS] UI disconnected.")
        current_websocket = None

    except Exception as e:
        print(f"[MARCUS] WS error: {e}")
        current_websocket = None
        try:
            await websocket.send_json({"type": "error", "text": str(e)})
        except Exception:
            pass

# ── AUTO OPEN BROWSER ─────────────────────────────────────────────────
def open_browser():
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    import uvicorn
    threading.Timer(2, open_browser).start()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_config=None,
        access_log=False
    )