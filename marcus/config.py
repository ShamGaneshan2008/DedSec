# ==============================
# 🎙️ VOICE SETTINGS (TTS)
# ==============================

TTS_ENABLED = True        # Turn voice ON/OFF
TTS_RATE = 170            # Speed of speech (default ~200)
TTS_VOLUME = 1.0          # Volume (0.0 to 1.0)
TTS_VOICE_INDEX = 0       # Change if multiple voices exist


# ==============================
# 🤖 ASSISTANT IDENTITY
# ==============================

ASSISTANT_NAME = "Marcus"
WAKE_WORD = "hey marcus"   # Used for voice activation


# ==============================
# 🧠 AI MODEL SETTINGS
# ==============================

MODEL = "llama3-8b-8192"   # Groq model (fast + free)
TEMPERATURE = 0.85         # Creativity (0.0 = strict, 1.0 = creative)
MAX_TOKENS = 1024          # Response length limit


# ==============================
# 💾 MEMORY SETTINGS
# ==============================

MEMORY_ENABLED = True
MAX_HISTORY = 10           # Number of past chats remembered


# ==============================
# 🗂️ FILE PATHS
# ==============================

DATA_DIR = "data"
MEMORY_FILE = "data/memory.json"
LOG_FILE = "data/logs/conversation.log"
SHORTCUTS_FILE = "data/shortcuts.json"


# ==============================
# 🔊 VOICE INPUT SETTINGS
# ==============================

MIC_TIMEOUT = 5            # Seconds to wait for speech
PHRASE_TIME_LIMIT = 10     # Max speaking duration


# ==============================
# 🧪 DEBUG MODE
# ==============================

DEBUG = True              # Prints extra logs in terminal