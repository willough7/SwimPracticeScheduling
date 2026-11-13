from pydantic import BaseModel, Field
from app.models import WeightsGroup

class SwimmerCreate(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    weights_group: WeightsGroup
    tags: set[str] = set()

class SwimmerOut(SwimmerCreate):
    swimmer_id: int