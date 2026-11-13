from fastapi import FastAPI, HTTPException
from app.schemas import SwimmerCreate, SwimmerOut, PracticeCreate, PracticeOut
from app.storage import swimmers, _ids, practices, _practice_ids
from app.models import Swimmer, Practice, Day

app = FastAPI(title="Swim Practice Scheduler")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/swimmers", status_code=201, response_model=SwimmerOut)
def create_swimmer(data: SwimmerCreate):
    new_id = next(_ids)
    swimmer = Swimmer(swimmer_id=new_id, **data.model_dump())
    swimmers[new_id] = swimmer
    return swimmer

@app.get("/swimmers", response_model=list[SwimmerOut])
def get_swimmers():
    return list(swimmers.values())

@app.get("/swimmers/{swimmer_id}", response_model=SwimmerOut)
def get_swimmer(swimmer_id: int):
    if swimmers.get(swimmer_id) is None:
        raise HTTPException(status_code=404, detail="Swimmer not found")
    return swimmers.get(swimmer_id)

@app.delete("/swimmers/{swimmer_id}", status_code=204)
def delete_swimmer(swimmer_id: int):
    if swimmers.get(swimmer_id) is None:
        raise HTTPException(status_code=404, detail="Swimmer not found")
    swimmers.pop(swimmer_id)

@app.post("/practices", status_code=201, response_model=PracticeOut)
def create_practice(data: PracticeCreate):
    new_id = next(_practice_ids)
    practice = Practice(practice_id=new_id, **data.model_dump())
    practices[new_id] = practice
    return practice

@app.get("/practices", response_model=list[PracticeOut])
def get_practices(day: Day | None = None):
    if day is None:
        return list(practices.values())
    return [practice for practice in practices.values() if practice.day == day]

@app.get("/practices/{practice_id}", response_model=PracticeOut)
def get_practice(practice_id: int):
    if practices.get(practice_id) is None:
        raise HTTPException(status_code=404, detail="Practice not found")
    return practices.get(practice_id)

@app.delete("/practices/{practice_id}", status_code=204)
def delete_practice(practice_id: int):
    if practices.get(practice_id) is None:
        raise HTTPException(status_code=404, detail="Practice not found")
    practices.pop(practice_id)