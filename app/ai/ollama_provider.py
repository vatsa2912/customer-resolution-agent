import json
import requests
from typing import List, Dict, Any, Optional
from app.ai.base_provider import BaseAIProvider

class OllamaProvider(BaseAIProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3"):
        super().__init__(model_name)
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "ollama"

    def health_check(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if resp.status_code == 200:
                return {
                    "provider": self.provider_name,
                    "model": self.model_name,
                    "status": "ready",
                    "message": "Local Ollama server is running and reachable."
                }
        except Exception:
            pass
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "status": "offline",
            "message": f"Cannot connect to Ollama at {self.base_url}."
        }

    def complete(self, messages: List[Dict[str, str]], system_prompt: str, response_format_json: bool = True) -> Dict[str, Any]:
        formatted = [{"role": "system", "content": system_prompt}]
        for m in messages:
            role = "assistant" if (m.get("role") or m.get("sender")) in ("agent", "assistant") else "user"
            content = m.get("content") or m.get("message") or ""
            formatted.append({"role": role, "content": content})

        payload = {
            "model": self.model_name,
            "messages": formatted,
            "stream": False,
            "options": {"temperature": 0.1}
        }
        if response_format_json:
            payload["format"] = "json"

        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=15)
            if resp.status_code != 200:
                return {
                    "raw_content": "",
                    "parsed_json": None,
                    "provider": self.provider_name,
                    "model": self.model_name,
                    "success": False,
                    "error": f"Ollama HTTP {resp.status_code}"
                }

            data = resp.json()
            content = data.get("message", {}).get("content", "")

            parsed_json = None
            if response_format_json and content:
                try:
                    parsed_json = json.loads(content)
                except Exception:
                    pass

            return {
                "raw_content": content,
                "parsed_json": parsed_json,
                "provider": self.provider_name,
                "model": self.model_name,
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "raw_content": "",
                "parsed_json": None,
                "provider": self.provider_name,
                "model": self.model_name,
                "success": False,
                "error": str(e)
            }
