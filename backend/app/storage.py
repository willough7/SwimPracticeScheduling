from itertools import count
from app.models import Swimmer, Practice, Assignment

swimmers: dict[int, Swimmer] = {}
_ids = count(1)

practices: dict[int, Practice] = {}
_practice_ids = count(1)

assignments: set[Assignment] = set()

# Which lane (1-8) an assigned swimmer is in for that practice. An assignment
# with no entry here hasn't been placed in a lane yet. Kept separate from
# `assignments` so an Assignment stays a simple (swimmer_id, practice_id) pair.
lanes: dict[Assignment, int] = {}