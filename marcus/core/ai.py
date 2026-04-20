import requests
from marcus import GROQ_API_KEY, GROQ_URL, GROQ_MODEL, MAX_TOKENS, SYSTEM_PROMPT
from marcus import get_recent_memory


def ask_ai(prompt: str) -> str:
    memory = get_recent_memory()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for m in memory:
        messages.append({"role": "user", "content": m["user"]})
        messages.append({"role": "assistant", "content": m["ai"]})

    messages.append({"role": "user", "content": prompt})

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Network error: {e}"
    except (KeyError, IndexError):
        return "Marcus couldn't process that. Try again."