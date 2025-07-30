import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"

def send_prompt_to_slm(prompt: str, model: str = MODEL_NAME) -> str:
    """
    Send a prompt to the local Ollama server running the specified model.
    Returns the model's response as a string.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except Exception as e:
        return f"Error communicating with SLM: {e}"

