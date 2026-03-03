from abc import ABC, abstractmethod

class AIPlatform(ABC):
    @abstractmethod
    async def chat(self, prompt: str) -> str:
        pass

    @abstractmethod
    async def summarize(self, text: str) -> str:
        pass

    @abstractmethod
    async def translate(self, text: str, target_language: str) -> str:
        pass
