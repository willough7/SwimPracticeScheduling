from itertools import count
from app.models import Swimmer

swimmers: dict[int, Swimmer] = {}
_ids = count(1)