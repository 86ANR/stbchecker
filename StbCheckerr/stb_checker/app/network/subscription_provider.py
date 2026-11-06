from abc import ABC, abstractmethod
from typing import List
from app.models import UserStatus, ContentItem

class SubscriptionProvider(ABC):
    @abstractmethod
    async def connect(self, portal: str, mac: str) -> UserStatus:
        pass

    @abstractmethod
    async def get_categories(self) -> List[str]:
        pass

    @abstractmethod
    async def get_content(self, category: str) -> List[ContentItem]:
        pass

    @abstractmethod
    async def get_playback_resource(self, content_id: str) -> str:
        pass

    @abstractmethod
    async def disconnect(self):
        pass
