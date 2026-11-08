from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import time, date

#day lines up with isoweekday()
class Day(Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

class WeightsGroup(Enum):
    THREE_DAY_A = auto()
    THREE_DAY_B = auto()
    FOUR_DAY = auto()

@dataclass
class Swimmer:
    first_name: str
    last_name: str
    swimmer_id: int
    weights_group: WeightsGroup
    tags: set[str] = field(default_factory=set)

@dataclass
class Practice:
    practice_id: int
    day: Day
    start_time: time
    end_time: time
    practice_title: str = "N/A"
    is_morning: bool = True

    def __post_init__(self):
        if self.start_time >= self.end_time:
            raise ValueError("end time must be after start time")

@dataclass(frozen=True)
class Assignment:
    swimmer_id: int
    practice_id: int


if __name__ == "__main__":

    print("Success")