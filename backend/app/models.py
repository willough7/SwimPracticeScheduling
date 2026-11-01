from enum import Enum, auto
from dataclasses import dataclass
from datetime import time, date

class WeightsGroup(Enum):
    THREE_DAY_A = auto()
    THREE_DAY_B = auto()
    FOUR_DAY = auto()

class SwimGroup(Enum):
    SPRINT_100s = auto()
    SPRINT_200s = auto()
    DISTANCE = auto()
    IM = auto()

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
    weights_group: WeightsGroup  #used to determin what days you lift and there for what days you have morning swims
    swim_group: SwimGroup  #used to asign lane
    dry_land: bool

@dataclass
class Session:
    start_time: time
    end_time: time

    def __post_init__(self):
        if self.start_time >= self.end_time:
            raise ValueError("end time must be after start time")

@dataclass
class Practice:
    day: Day
    practice_type: PracticeType
    weights_groups: list[WeightsGroup]
    sessions: list[Session]
    is_morning: bool = True

    def __post_init__(self):
        if self.practice_type == PracticeType.WEIGHTS and self.weights_groups == []:
            raise ValueError("during a lift, weights groups must be given")
        if self.practice_type == PracticeType.SWIM and self.weights_groups != []:
            raise ValueError("weight groups are not needed for a swim practice")
        if self.practice_type == PracticeType.DRYLAND and self.weights_groups != []:
            raise ValueError("weight groups are not needed for a dryland practice")
        if self.sessions == []:
            raise ValueError("Every practice must have at least one session")

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

    # --- Valid afternoon swim practice ---

    practice = Practice(day=Day.MONDAY,
                        practice_type=PracticeType.SWIM,
                        weights_groups=[],
                        sessions=[Session(start_time=time(13), end_time=time(15)),
                                  Session(start_time=time(15), end_time=time(17))],
                        is_morning=False)

    assert practice.day == Day.MONDAY
    assert practice.practice_type == PracticeType.SWIM
    assert not practice.is_morning
    assert practice.weights_groups == []
    assert practice.sessions == [Session(start_time=time(13), end_time=time(15)),
                                 Session(start_time=time(15), end_time=time(17))]

    # --- is_morning defaults to True when not given ---

    default_practice = Practice(day=Day.MONDAY,
                                practice_type=PracticeType.SWIM,
                                weights_groups=[],
                                sessions=[Session(start_time=time(6), end_time=time(7, 30))])

    assert default_practice.is_morning, "is_morning should default to True"

    # --- Valid practices of the other two types (rely on the default) ---

    weights_practice = Practice(day=Day.MONDAY,
                                practice_type=PracticeType.WEIGHTS,
                                weights_groups=[WeightsGroup.THREE_DAY_A, WeightsGroup.FOUR_DAY],
                                sessions=[Session(start_time=time(6), end_time=time(7))])

    assert weights_practice.practice_type == PracticeType.WEIGHTS
    assert weights_practice.weights_groups == [WeightsGroup.THREE_DAY_A, WeightsGroup.FOUR_DAY]

    dryland_practice = Practice(day=Day.MONDAY,
                                practice_type=PracticeType.DRYLAND,
                                weights_groups=[],
                                sessions=[Session(start_time=time(7), end_time=time(7, 45))])

    assert dryland_practice.practice_type == PracticeType.DRYLAND
    assert dryland_practice.weights_groups == []

    # --- Weights practice with no weights groups must be rejected ---

    try:
        Practice(day=Day.MONDAY,
                 practice_type=PracticeType.WEIGHTS,
                 weights_groups=[],
                 sessions=[Session(start_time=time(6), end_time=time(7))])
    except ValueError:
        pass
    else:
        assert False, "weights practice with no weights groups was not rejected"

    # --- Swim practice with weights groups must be rejected ---

    try:
        Practice(day=Day.MONDAY,
                 practice_type=PracticeType.SWIM,
                 weights_groups=[WeightsGroup.FOUR_DAY],
                 sessions=[Session(start_time=time(13), end_time=time(15))],
                 is_morning=False)
    except ValueError:
        pass
    else:
        assert False, "swim practice with weights groups was not rejected"

    # --- Dryland practice with weights groups must be rejected ---

    try:
        Practice(day=Day.MONDAY,
                 practice_type=PracticeType.DRYLAND,
                 weights_groups=[WeightsGroup.THREE_DAY_B],
                 sessions=[Session(start_time=time(7), end_time=time(7, 45))])
    except ValueError:
        pass
    else:
        assert False, "dryland practice with weights groups was not rejected"

    # --- Practice with no sessions must be rejected ---

    try:
        Practice(day=Day.MONDAY,
                 practice_type=PracticeType.SWIM,
                 weights_groups=[],
                 sessions=[],
                 is_morning=False)
    except ValueError:
        pass
    else:
        assert False, "practice with no sessions was not rejected"

    # --- Day values must line up with date.isoweekday() ---

    # Nov 2, 2026 is a Monday and Nov 1, 2026 is a Sunday: the two ends of the range
    assert Day(date(2026, 11, 2).isoweekday()) == Day.MONDAY
    assert Day(date(2026, 11, 1).isoweekday()) == Day.SUNDAY

    print("Success")