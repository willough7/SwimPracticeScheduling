from datetime import time
from app.models import Swimmer, Practice, PracticeType, Day, Session, WeightsGroup, SwimGroup
from app.intervals import overlapChecker, mergeBlocks

MORNING_BOUNDARY = time(9)

def practices_for_swimmer(athlete: Swimmer, todays_practices: list[Practice]) -> list[Practice]:
    weight_group = athlete.weights_group

    assigned_practices = []
    lift_today = False
    afternoon_swim = False


    #first scan for weights and afternon since its used to determin coming peices.
    for practice in todays_practices:
        if practice.practice_type is PracticeType.WEIGHTS and weight_group in practice.weights_groups:
            lift_today = True
            assigned_practices.append(practice)

        if practice.practice_type is PracticeType.SWIM and not practice.is_morning:
            afternoon_swim = True


    for practice in todays_practices:
        practice_type = practice.practice_type

        if practice_type is PracticeType.DRYLAND and athlete.dry_land:
            assigned_practices.append(practice)

        if practice_type is PracticeType.SWIM:
            if afternoon_swim is False:
                assigned_practices.append(practice)
            elif not lift_today and practice.is_morning:
                assigned_practices.append(practice)
            elif not practice.is_morning:
                assigned_practices.append(practice)

    return assigned_practices

def session_selection(athlete: Swimmer, class_blocks, assigned_practices: list[Practice]) -> list[(Practice, int)]:

    selected_sessions = []
    for practice in assigned_practices:
        if len(practice.sessions) < 1:
            selected_sessions.append((practice, 0))
            continue
        
        overlap = False
        i = 0
        for session in practice.sessions:
            for start, end in class_blocks:
                if overlapChecker((session.start_time, session.end_time), (start, end)):
                    overlap = True

            if not overlap:
                selected_sessions.append(practice, i)

            i += 1

        


def make_swimmer(weights_group: WeightsGroup, dry_land: bool = True) -> Swimmer:
    """Build a test swimmer where only the weights group and dryland matter."""
    return Swimmer(first_name="Test",
                    last_name="Swimmer",
                    weights_group=weights_group,
                    swim_group=SwimGroup.DISTANCE,
                    dry_land=dry_land)


def assert_same_practices(result: list[Practice], expected: list[Practice], label: str) -> None:
    """Check two practice lists hold the same practices, ignoring order."""
    assert len(result) == len(expected), f"{label}: expected {len(expected)} practices, got {len(result)}"
    for practice in expected:
        assert practice in result, f"{label}: missing {practice.practice_type.name} practice"


if __name__ == "__main__":
    three_day_a = make_swimmer(WeightsGroup.THREE_DAY_A)
    three_day_b = make_swimmer(WeightsGroup.THREE_DAY_B)
    four_day = make_swimmer(WeightsGroup.FOUR_DAY)
    no_dryland_b = make_swimmer(WeightsGroup.THREE_DAY_B, dry_land=False)

    # --- Monday: 3-day A lifts; there is a morning AND an afternoon swim ---

    monday_weights = Practice(day=Day.MONDAY,
                              practice_type=PracticeType.WEIGHTS,
                              weights_groups=[WeightsGroup.THREE_DAY_A],
                              sessions=[Session(start_time=time(6), end_time=time(7))])
    monday_morning_swim = Practice(day=Day.MONDAY,
                                   practice_type=PracticeType.SWIM,
                                   weights_groups=[],
                                   sessions=[Session(start_time=time(7, 15), end_time=time(8, 45))],
                                   is_morning=True)
    monday_afternoon_swim = Practice(day=Day.MONDAY,
                                     practice_type=PracticeType.SWIM,
                                     weights_groups=[],
                                     sessions=[Session(start_time=time(15), end_time=time(17))],
                                     is_morning=False)
    monday_dryland = Practice(day=Day.MONDAY,
                              practice_type=PracticeType.DRYLAND,
                              weights_groups=[],
                              sessions=[Session(start_time=time(17), end_time=time(17, 45))])

    monday = [monday_weights, monday_morning_swim, monday_afternoon_swim, monday_dryland]

    # 3-day A lifts, so skips the morning swim (an afternoon swim exists)
    result = practices_for_swimmer(three_day_a, monday)
    assert_same_practices(result, [monday_weights, monday_afternoon_swim, monday_dryland], "Monday 3-day A")
    assert monday_morning_swim not in result, "Monday 3-day A should skip the morning swim"

    # 3-day B doesn't lift Monday, so gets both swims and no weights
    result = practices_for_swimmer(three_day_b, monday)
    assert_same_practices(result, [monday_morning_swim, monday_afternoon_swim, monday_dryland], "Monday 3-day B")
    assert monday_weights not in result, "Monday 3-day B should not get 3-day A's weights"

    # Order of the coach's list must not change the answer
    result = practices_for_swimmer(three_day_a, list(reversed(monday)))
    assert_same_practices(result, [monday_weights, monday_afternoon_swim, monday_dryland], "Monday 3-day A reversed")

    # --- Dryland: only swimmers with dry_land=True get it ---

    result = practices_for_swimmer(no_dryland_b, monday)
    assert_same_practices(result, [monday_morning_swim, monday_afternoon_swim], "Monday no-dryland")
    assert monday_dryland not in result, "swimmer with dry_land=False should not get dryland"

    # --- Friday: nobody lifts, one non-morning swim, everyone gets it ---

    friday_swim = Practice(day=Day.FRIDAY,
                           practice_type=PracticeType.SWIM,
                           weights_groups=[],
                           sessions=[Session(start_time=time(9), end_time=time(11))],
                           is_morning=False)

    friday = [friday_swim]

    for swimmer, label in [(three_day_a, "Friday 3-day A"),
                           (three_day_b, "Friday 3-day B"),
                           (four_day, "Friday 4-day")]:
        result = practices_for_swimmer(swimmer, friday)
        assert_same_practices(result, [friday_swim], label)

    # --- Saturday: everyone lifts, ONE swim with two sessions, no afternoon swim ---

    saturday_early_weights = Practice(day=Day.SATURDAY,
                                      practice_type=PracticeType.WEIGHTS,
                                      weights_groups=[WeightsGroup.THREE_DAY_B, WeightsGroup.FOUR_DAY],
                                      sessions=[Session(start_time=time(8), end_time=time(9))])
    saturday_late_weights = Practice(day=Day.SATURDAY,
                                     practice_type=PracticeType.WEIGHTS,
                                     weights_groups=[WeightsGroup.THREE_DAY_A],
                                     sessions=[Session(start_time=time(9), end_time=time(10))])
    saturday_swim = Practice(day=Day.SATURDAY,
                             practice_type=PracticeType.SWIM,
                             weights_groups=[],
                             sessions=[Session(start_time=time(7), end_time=time(8, 45)),
                                       Session(start_time=time(9, 15), end_time=time(11))],
                             is_morning=True)

    saturday = [saturday_early_weights, saturday_late_weights, saturday_swim]

    # Lifters keep the morning swim because it's the only swim of the day
    result = practices_for_swimmer(three_day_a, saturday)
    assert_same_practices(result, [saturday_late_weights, saturday_swim], "Saturday 3-day A")
    assert saturday_early_weights not in result, "3-day A should not get the early weights practice"

    result = practices_for_swimmer(three_day_b, saturday)
    assert_same_practices(result, [saturday_early_weights, saturday_swim], "Saturday 3-day B")
