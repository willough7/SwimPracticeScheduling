from enum import Enum, auto
from dataclasses import dataclass
from datetime import time, date

class PracticeType(Enum):
    WEIGHTS = auto()
    SWIM = auto()
    DRYLAND = auto()

#day lines up with isoweekday()
class Day(Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

@dataclass
class Swimmer:
    first_name: str
    last_name: str
    weights_group: list[str]
    swim_groups: list[str]
    dry_land: bool

@dataclass
class Practice:
    day: Day
    start_time: time
    end_time: time
    practice_type: PracticeType
    is_morning: bool = True

    def __post_init__(self):
        if self.start_time >= self.end_time:
            raise ValueError("end time must be after start time")

if __name__ == "__main__":

    print("Success")