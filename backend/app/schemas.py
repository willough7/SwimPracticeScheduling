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
    is_morning: bool = True

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