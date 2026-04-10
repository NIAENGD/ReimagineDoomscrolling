from datetime import datetime

from pydantic import BaseModel


class SourceCreate(BaseModel):
    url: str
    title: str = ""
    cadence_minutes: int = 60
    discovery_mode: str = "latest_n"
    max_videos: int = 10


class SourceOut(SourceCreate):
    id: int
    state: str
    next_run_at: datetime | None = None
    last_success_at: datetime | None = None

    class Config:
        from_attributes = True
