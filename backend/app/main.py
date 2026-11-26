from fastapi import FastAPI, HTTPException, UploadFile
from app.schemas import SwimmerCreate, SwimmerOut, PracticeCreate, PracticeOut
from app.storage import swimmers, _ids, practices, _practice_ids
from app.models import Swimmer, Practice, Day
from app.ics_parser import parse_calendar

app = FastAPI(title="Swim Practice Scheduler")

def swimmer_to_swimmerout(swimmer: Swimmer) -> SwimmerOut:
    return SwimmerOut(
        first_name=swimmer.first_name,
        last_name=swimmer.last_name,
        weights_group=swimmer.weights_group,
        tags=swimmer.tags,
        swimmer_id=swimmer.swimmer_id,
        has_schedule=swimmer.ics_data is not None
        )


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/swimmers", status_code=201, response_model=SwimmerOut)
def create_swimmer(data: SwimmerCreate):
    new_id = next(_ids)
    swimmer = Swimmer(swimmer_id=new_id, **data.model_dump())
    swimmers[new_id] = swimmer
    return swimmer_to_swimmerout(swimmer)

@app.get("/swimmers", response_model=list[SwimmerOut])
def get_swimmers():
    return [swimmer_to_swimmerout(s) for s in swimmers.values()]

@app.get("/swimmers/{swimmer_id}", response_model=SwimmerOut)
def get_swimmer(swimmer_id: int):
    swimmer = swimmers.get(swimmer_id)
    if swimmer is None:
        raise HTTPException(status_code=404, detail="Swimmer not found")
    return swimmer_to_swimmerout(swimmer)

@app.delete("/swimmers/{swimmer_id}", status_code=204)
def delete_swimmer(swimmer_id: int):
    if swimmers.get(swimmer_id) is None:
        raise HTTPException(status_code=404, detail="Swimmer not found")
    swimmers.pop(swimmer_id)

@app.put("/swimmers/{swimmer_id}/schedule", response_model=SwimmerOut)
async def upload_schedule(swimmer_id: int, file: UploadFile):
    swimmer = swimmers.get(swimmer_id)
    if(swimmer is None):
        raise HTTPException(status_code=404, detail="Swimmer not found")

    ics = await file.read()

    try:
        parsed_ics = parse_calendar(ics)
    except ValueError:
        raise HTTPException(status_code=400, detail="File is not a valid .ics calendar")

    swimmer.ics_data = ics

    return swimmer_to_swimmerout(swimmer)

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