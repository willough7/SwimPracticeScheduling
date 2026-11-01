from enum import Enum, auto
from dataclasses import dataclass
from datetime import time

class WeightsGroup(Enum):
    THREE_DAY_A = auto()
    THREE_DAY_B = auto()
    FOUR_DAY = auto()

class SwimGroup(Enum):
    SPRINT_100s = auto()
    SPRINT_200s = auto()
    DISTANCE = auto()
    IM = auto()

@dataclass
class Swimmer:

    first_name: str
    last_name: str
    weights_group: WeightsGroup
    swim_group: SwimGroup
    dry_land: bool

@dataclass
class Session:
    start_time: time
    end_time: time

    def __post_init__(self):
        if self.start_time >= self.end_time:
            raise ValueError("end time must be after start time")


if __name__ == "__main__":
    steve = Swimmer(first_name="Jhon", 
                    last_name="Minecraft", 
                    weights_group=WeightsGroup.THREE_DAY_A, 
                    swim_group=SwimGroup.SPRINT_100s, 
                    dry_land=True)

    assert steve.first_name == "Jhon"
    assert steve.last_name == "Minecraft"
    assert steve.weights_group == WeightsGroup.THREE_DAY_A
    assert steve.swim_group == SwimGroup.SPRINT_100s
    assert steve.dry_land

    session = Session(start_time=time(17), end_time=time(19))

    assert session.start_time == time(17)
    assert session.end_time == time(19)

    try:
        Session(start_time=time(21), end_time=time(19))

    except ValueError:
        pass

    else:
        assert False, "inverted session time was not rejected"

    try:
        Session(start_time=time(19), end_time=time(19))

    except ValueError:
        pass

    else:
        assert False, "equal start and end time was not rejected"
    

    print("Success")