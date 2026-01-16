from google import genai
from .base import AIPlatform

class Gemini(AIPlatform):
    def __init__(self, api_key: str, system_prompt: str | None = None, summary_prompt: str | None = None, translate_prompt: str | None = None):
        self.system_prompt = system_prompt
        self.summary_prompt = summary_prompt
        self.translate_prompt = translate_prompt
        self.client = genai.Client(api_key=api_key)

    async def _generate(self, contents) -> str:
        response = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=contents
        )
        return response.text

    async def chat(self, prompt: str) -> str:
        if self.system_prompt:
            prompt = f"{self.system_prompt}\n\n{prompt}"
        response = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        return response.text

    async def summarize(self, text: str) -> str:
        if not self.summary_prompt:
            raise ValueError("Summary prompt not set")
        prompt = f"{self.summary_prompt}\n\nText: {text}"
        response = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        return response.text

    async def translate(self, text: str, target_language: str) -> str:
        if not self.translate_prompt:
            raise ValueError("Translate prompt not set")
        prompt = f"{self.translate_prompt}\n\nText: {text}\nTarget language: {target_language}"
        response = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        return response.text

    async def detect_language(self, text: str) -> str:
        detection_prompt = (
            "Detect the primary language of this text and return ONLY the two-letter ISO code "
            "(e.g., 'en' for English, 'tr' for Turkish, 'fr' for French). "
            "Do not add any explanation or extra text. Just the code:\n\n"
            f"{text}"
        )
        response = await self._generate(detection_prompt)
        return response.strip().lower()