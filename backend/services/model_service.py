import os
import requests


# ============================================================
# AI PROVIDER CONFIGURATION
# ============================================================

AI_PROVIDER = os.getenv(
    "AI_PROVIDER",
    "ollama"
).lower()

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:1b"
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free"
)

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)


# ============================================================
# OLLAMA
# ============================================================

def generate_with_ollama(
    prompt: str,
    system_prompt: str = ""
) -> str:

    # Import Ollama only when it is actually being used.
    # This prevents cloud deployment from requiring
    # a running Ollama server.

    import ollama

    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=messages,
        options={
            "temperature": 0.2
        }
    )

    content = response["message"]["content"]

    if not content:
        raise RuntimeError(
            "Ollama returned an empty response."
        )

    return content.strip()


# ============================================================
# OPENROUTER
# ============================================================

def generate_with_openrouter(
    prompt: str,
    system_prompt: str = ""
) -> str:

    api_key = os.getenv(
        "OPENROUTER_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY environment variable "
            "is not set."
        )

    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 2048
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://acad-ai.vercel.app",
        "X-Title": "AcadAI"
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    if not response.ok:
        raise RuntimeError(
            f"OpenRouter API error "
            f"{response.status_code}: {response.text}"
        )

    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]

    except (
        KeyError,
        IndexError,
        TypeError
    ):
        raise RuntimeError(
            f"Unexpected OpenRouter response: {data}"
        )

    if not content:
        raise RuntimeError(
            "OpenRouter returned an empty response."
        )

    return content.strip()


# ============================================================
# MAIN AI FUNCTION
# ============================================================

def generate_ai_response(
    prompt: str,
    system_prompt: str = ""
) -> str:

    if AI_PROVIDER == "ollama":

        return generate_with_ollama(
            prompt,
            system_prompt
        )

    elif AI_PROVIDER == "openrouter":

        return generate_with_openrouter(
            prompt,
            system_prompt
        )

    else:

        raise RuntimeError(
            f"Unsupported AI_PROVIDER: {AI_PROVIDER}"
        )