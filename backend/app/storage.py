from itertools import count
from app.models import Swimmer, Practice

swimmers: dict[int, Swimmer] = {}
_ids = count(1)

practices: dict[int, Practice] = {}
_practice_ids = count(1)