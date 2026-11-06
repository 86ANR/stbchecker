import asyncio
from typing import List
from app.network.subscription_provider import SubscriptionProvider
from app.models import UserStatus, ContentItem

class MockSubscriptionProvider(SubscriptionProvider):
    def __init__(self):
        self.portal = None
        self.mac = None
        self.connected = False

    async def connect(self, portal: str, mac: str) -> UserStatus:
        self.portal = portal
        self.mac = mac
        
        # Simular timeout HTTP y retardo de red
        await asyncio.sleep(1.5) 
        
        mac_lower = mac.lower()
        if mac_lower.endswith("01"):
            self.connected = True
            return UserStatus(is_valid=True, status_code="OK", message="Conectado correctamente", expiration_date="15/12/2026")
        elif mac_lower.endswith("02"):
            self.connected = False
            return UserStatus(is_valid=False, status_code="BLOCKED", message="Your STB is blocked")
        elif mac_lower.endswith("03"):
            self.connected = False
            return UserStatus(is_valid=False, status_code="EXPIRED", message="Subscription Expired")
        elif mac_lower.endswith("timeout"):
            # Simular timeout
            await asyncio.sleep(8)
            return UserStatus(is_valid=False, status_code="ERROR", message="Timeout de 8 segundos alcanzado")
        else:
            self.connected = False
            return UserStatus(is_valid=False, status_code="NOT_FOUND", message="MAC no encontrada")

    async def get_categories(self) -> List[str]:
        if not self.connected:
            return []
        await asyncio.sleep(0.5)
        return ["TV", "Películas", "Series", "Favoritos"]

    async def get_content(self, category: str) -> List[ContentItem]:
        if not self.connected:
            return []
        await asyncio.sleep(0.5)
        if category == "TV":
            return [
                ContentItem("tv1", "Canal 1 (Test Video BigBuckBunny)", "tv"),
                ContentItem("tv2", "Canal 2 (Test Video ElephantsDream)", "tv"),
            ]
        return [ContentItem(f"{category}_1", f"Item 1 de {category}", category)]

    async def get_playback_resource(self, content_id: str) -> str:
        await asyncio.sleep(0.5)
        # Devolver streams públicos de prueba legales
        if content_id == "tv1":
            return "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        return "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"

    async def disconnect(self):
        self.connected = False
        self.portal = None
        self.mac = None
        await asyncio.sleep(0.2)
