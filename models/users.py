from typing import List, Optional

from beanie import Document, Link
from pydantic import BaseModel, EmailStr

from models.events import Event


class User(Document):
    email: EmailStr
    password: str
    events: Optional[List[Link[Event]]] = None

    class Settings:
        name = "users"

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "amalia@planner.ru",
                "password": "strong!!!",
                "events": [],
            }
        }
    }


class UserSignIn(BaseModel):
    email: EmailStr
    password: str