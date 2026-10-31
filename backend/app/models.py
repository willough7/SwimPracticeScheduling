from enum import Enum, auto
from dataclasses import dataclass

class WeightsGroup(Enum):
    three_day_a = auto()
    Three_day_b = auto()
    four_day = auto()

class SwimGroup(Enum):
    sprint_100s = auto()
    sprint_200s = auto()
    distance = auto()
    im = auto()

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
                    weights_group=WeightsGroup.Three_Day_A, 
                    swim_group=SwimGroup.Sprint_100s, 
                    dry_land=True)

    assert steve.first_name == "Jhon"
    assert steve.last_name == "Minecraft"
    assert steve.weights_group == WeightsGroup.Three_Day_A
    assert steve.swim_group == SwimGroup.Sprint_100s
    assert steve.dry_land
    print("Succsses")