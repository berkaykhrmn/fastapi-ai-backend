from abc import ABC, abstractmethod

class AIPlatform(ABC):
    @abstractmethod
    async def chat(self, prompt: str) -> str:
        """Send a prompt to the AI platform and return its response"""
        pass

    @abstractmethod
    async def summarize(self, text: str) -> str:
        """Summarize the given text according to platform rules"""
        pass

    @abstractmethod
    async def translate(self, text: str, target_language: str) -> str:
        """
        Translate the given text into the target language.
        Must follow the platform-specific translation rules.
        """
        pass