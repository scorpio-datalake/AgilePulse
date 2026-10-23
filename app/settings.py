import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    database_path: Path
    session_secret: str = Field(min_length=1)
    require_admin_setup: bool = False


def load_settings() -> Settings:
    database = os.environ.get("SCALED_ENGINE_DB", "data/scaled_engine.sqlite")
    secret = os.environ.get("SCALED_ENGINE_SESSION_SECRET", "local-dev-session-secret")
    require_setup = os.environ.get("SCALED_ENGINE_REQUIRE_ADMIN_SETUP", "") == "1"
    return Settings(
        database_path=Path(database),
        session_secret=secret,
        require_admin_setup=require_setup,
    )
