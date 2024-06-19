from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class Summary(BaseSchema):
    date: int = Field(alias="date")
    gained_xp: int = Field(alias="gainedXp")
    num_sessions: int = Field(alias="numSessions")
    total_session_time: int = Field(alias="totalSessionTime")

    @staticmethod
    def create_default(date: int) -> "Summary":
        return Summary(
            date=date,
            gainedXp=0,
            numSessions=0,
            totalSessionTime=0,
        )


class User(BaseSchema):
    site_streak: int = Field(alias="siteStreak")

    @staticmethod
    def to_user(data: dict[str, Any]) -> "User":
        return User(**data)


class DatabaseEntry(BaseSchema):
    date: str
    xp_today: int
    number_of_sessions: int
    session_time: int
    streak: int

    @staticmethod
    def to_dict(entry: "DatabaseEntry") -> dict[str, str | int]:
        return entry.model_dump()

    @staticmethod
    def create(summary: Summary, date: str, streak: int) -> "DatabaseEntry":
        return DatabaseEntry(
            date=date,
            xp_today=summary.gained_xp,
            number_of_sessions=summary.num_sessions,
            session_time=summary.total_session_time,
            streak=streak,
        )

    @staticmethod
    def create_now(summary: Summary, current_streak: int) -> "DatabaseEntry":
        processed_date = datetime.now().strftime("%Y/%m/%d")

        return DatabaseEntry.create(summary, processed_date, current_streak)

    @staticmethod
    def create_default(date: str, streak: int) -> "DatabaseEntry":
        return DatabaseEntry(
            date=date,
            xp_today=0,
            number_of_sessions=0,
            session_time=0,
            streak=streak,
        )


class Statistics(BaseSchema):
    datetime: dict[str, str]

    @staticmethod
    def to_dict(entry: "Statistics") -> dict[str, dict[str, str]]:
        return entry.model_dump()

    @staticmethod
    def create_datetime_now() -> dict[str, str]:
        current_date = datetime.now().strftime("%Y/%m/%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        return {current_date: current_time}
