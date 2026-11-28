from typing import Annotated
from pydantic import BaseModel, Field, model_validator
from datetime import time, date
from app.models import WeightsGroup, Day

class SwimmerCreate(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    weights_group: WeightsGroup
    tags: set[str] = set()

class SwimmerOut(SwimmerCreate):
    swimmer_id: int
    has_schedule: bool

class PracticeCreate(BaseModel):
    day: Day
    start_time: time
    end_time: time
    practice_title: str ="N/A"

    @model_validator(mode="after")
    def check_times(self):
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")
        return self

class PracticeOut(PracticeCreate):
    practice_id: int

class PracticeConflictsOut(BaseModel):
    practice_id: int
    week_start: date
    available: list[int]
    conflict: list[int]
    unknown: list[int]

LANE_COUNT = 8

class LaneUpdate(BaseModel):
    # A lane number from 1 to LANE_COUNT, or None to take the swimmer out of their lane
    lane: Annotated[int, Field(ge=1, le=LANE_COUNT)] | None

class LanePlacementOut(BaseModel):
    swimmer_id: int
    lane: int

class LoginRequest(BaseModel):
    username: str
    password: str

class AdminOut(BaseModel):
    # None when nobody is logged in
    username: str | None
