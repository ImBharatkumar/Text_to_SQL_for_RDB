import os
from typing import Optional

class LLMPlugin:
    """Wrapper for LLM providers (Gemini, open models, etc.)."""
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def generate(self, prompt: str) -> str:
        """Generates text from prompt using Gemini API."""
        if not self.api_key or self.api_key == "your-google-api-key-here":
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        from google import genai
        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        text = response.text.strip()
        
        # Clean up markdown code fences if wrapped
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2:
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text
