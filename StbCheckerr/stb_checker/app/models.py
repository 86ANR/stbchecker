from dataclasses import dataclass
from typing import Optional

@dataclass
class UserStatus:
    is_valid: bool
    status_code: str # "OK", "BLOCKED", "EXPIRED", "NOT_FOUND", "ERROR"
    message: str
    expiration_date: Optional[str] = None

@dataclass
class ContentItem:
    id: str
    name: str
    type: str # "tv", "movie", "series"
    url: Optional[str] = None
