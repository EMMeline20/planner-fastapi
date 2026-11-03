from typing import List, Optional

from beanie import Document
from pydantic import BaseModel


class Event(Document):
    title: str
    image: str
    description: str
    tags: List[str]
    location: str

    class Settings:
        name = "events"

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Python Meetup Ufa",
                "image": "https://linktomyimage.com/image.png",
                "description": "Встреча по FastAPI и MongoDB. Ведущая — Чубараева А.",
                "tags": ["python", "fastapi", "mongodb"],
                "location": "Google Meet",
            }
        }
    }


class EventUpdate(BaseModel):
    title: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None