"""Tests for the data classes in app/models.py."""

from dataclasses import FrozenInstanceError
from datetime import date, time, timedelta

import pytest

from app.models import Assignment, Day, Practice, Swimmer, WeightsGroup


# ---------- helpers ----------

def make_swimmer(swimmer_id=1, **overrides):
    """Build a valid Swimmer so each test only spells out what it cares about."""
    values = dict(
        first_name="Test",
        last_name="Swimmer",
        swimmer_id=swimmer_id,
        weights_group=WeightsGroup.THREE_DAY_A,
    )
    values.update(overrides)
    return Swimmer(**values)


def make_practice(practice_id=1, **overrides):
    """Build a valid Practice (Tuesday 6:00-8:00) unless a test overrides a field."""
    values = dict(
        practice_id=practice_id,
        day=Day.TUESDAY,
        start_time=time(6, 0),
        end_time=time(8, 0),
    )
    values.update(overrides)
    return Practice(**values)


# ---------- Day ----------

@pytest.mark.parametrize("offset", range(7))
def test_day_values_match_isoweekday(offset):
    # 2026-11-09 is a Monday; walk through the whole week.
    # The conflict check will rely on Day(d.isoweekday()) giving the right day.
    d = date(2026, 11, 9) + timedelta(days=offset)
    assert Day(d.isoweekday()).name == d.strftime("%A").upper()


# ---------- Swimmer ----------

def test_swimmer_tags_default_to_empty_set():
    assert make_swimmer().tags == set()


def test_swimmers_do_not_share_a_tags_set():
    # Guards against the shared-mutable-default bug: if tags were "= set()",
    # tagging one swimmer would tag every swimmer.
    a = make_swimmer(1)
    b = make_swimmer(2)
    a.tags.add("Distance")
    assert b.tags == set()


def test_swimmer_tags_ignore_duplicates():
    s = make_swimmer(tags={"IM", "Breast"})
    s.tags.add("IM")
    assert s.tags == {"IM", "Breast"}


# ---------- Practice ----------

def test_valid_practice_is_created():
    p = make_practice()
    assert p.day is Day.TUESDAY
    assert p.start_time < p.end_time


def test_practice_is_morning_by_default():
    assert make_practice().is_morning is True


def test_practice_end_before_start_raises():
    with pytest.raises(ValueError):
        make_practice(start_time=time(8, 0), end_time=time(6, 0))


def test_practice_zero_length_raises():
    with pytest.raises(ValueError):
        make_practice(start_time=time(6, 0), end_time=time(6, 0))


# ---------- Assignment ----------

def test_assignments_with_same_ids_are_equal():
    assert Assignment(1, 2) == Assignment(1, 2)


def test_assignment_argument_order_matters():
    # Swimmer 1 in practice 2 is not swimmer 2 in practice 1.
    # Catches anyone passing the ids in the wrong order.
    assert Assignment(1, 2) != Assignment(2, 1)


def test_duplicate_assignments_collapse_in_a_set():
    # The coach clicking "assign" twice should not create two assignments.
    assignments = {Assignment(1, 2), Assignment(1, 2), Assignment(3, 2)}
    assert len(assignments) == 2


def test_assignment_is_read_only():
    a = Assignment(1, 2)
    with pytest.raises(FrozenInstanceError):
        a.swimmer_id = 5


def test_find_assignments_both_directions():
    # The reason Assignment exists: one collection answers both questions.
    assignments = {Assignment(12, 4), Assignment(12, 7), Assignment(15, 4)}

    in_practice_4 = {a.swimmer_id for a in assignments if a.practice_id == 4}
    swimmer_12_practices = {a.practice_id for a in assignments if a.swimmer_id == 12}

    assert in_practice_4 == {12, 15}
    assert swimmer_12_practices == {4, 7}
