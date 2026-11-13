from pydantic import BaseModel, Field, model_validator
from datetime import time
from app.models import WeightsGroup, Day

class SwimmerCreate(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    weights_group: WeightsGroup
    tags: set[str] = set()

class SwimmerOut(SwimmerCreate):
    swimmer_id: int

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