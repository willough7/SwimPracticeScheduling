from enum import Enum, auto
from dataclasses import dataclass

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
    print("Succsses")