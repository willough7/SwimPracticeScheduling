from fastapi import FastAPI, HTTPException, UploadFile
from datetime import date
from app.schemas import SwimmerCreate, SwimmerOut, PracticeCreate, PracticeOut, PracticeConflictsOut
from app.storage import swimmers, _ids, practices, _practice_ids, assignments
from app.models import Swimmer, Practice, Day, Assignment
from app.ics_parser import parse_calendar, monday_of
from app.conflicts import get_swimmers_status_for_practice

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
    # Remove this swimmer's assignments too, so none point at a swimmer that no longer exists.
    assignments.difference_update({a for a in assignments if a.swimmer_id == swimmer_id})

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
    # Remove this practice's assignments too, so none point at a practice that no longer exists.
    assignments.difference_update({a for a in assignments if a.practice_id == practice_id})

@app.get("/practices/{practice_id}/conflicts", response_model=PracticeConflictsOut)
def get_practice_conflicts(practice_id: int, week: date):
    practice = practices.get(practice_id)
    if (practice is None):
        raise HTTPException(status_code=404, detail="Practice not found")

    result = get_swimmers_status_for_practice(practice=practice, day=week, swimmers=swimmers.values())
    return PracticeConflictsOut(
        practice_id=practice_id,
        week_start=monday_of(week),
        available=result.available,
        conflict=result.conflict,
        unknown=result.unknown,
    )

#assignments

# No conflict check on purpose: the coach can assign anyone,
# the gray-out in the UI is only a warning.
@app.put("/practices/{practice_id}/swimmers/{swimmer_id}", status_code=204)
def make_practice_assignment(practice_id: int, swimmer_id: int):
    if (practices.get(practice_id) is None):
        raise HTTPException(status_code=404, detail="Practice not found")
    if (swimmers.get(swimmer_id) is None):
        raise HTTPException(status_code=404, detail="Swimmer not found")
    
    assignments.add(Assignment(swimmer_id=swimmer_id, practice_id=practice_id))


@app.get("/practices/{practice_id}/swimmers", response_model=list[SwimmerOut])
def get_practice_swimmers(practice_id: int):
    if (practices.get(practice_id) is None):
        raise HTTPException(status_code=404, detail="Practice not found")

    assigned = [swimmers[a.swimmer_id] for a in assignments if a.practice_id == practice_id]
    assigned.sort(key=lambda swimmer: swimmer.swimmer_id)

    return [swimmer_to_swimmerout(swimmer) for swimmer in assigned]


@app.delete("/practices/{practice_id}/swimmers/{swimmer_id}", status_code=204)
def remove_practice_assignment(practice_id: int, swimmer_id: int):
    if (practices.get(practice_id) is None):
        raise HTTPException(status_code=404, detail="Practice not found")
    if (swimmers.get(swimmer_id) is None):
        raise HTTPException(status_code=404, detail="Swimmer not found")

    assignment = Assignment(swimmer_id=swimmer_id, practice_id=practice_id)
    if (assignment not in assignments):
        raise HTTPException(status_code=404, detail="Swimmer is not assigned to this practice")

    assignments.remove(assignment)


@app.get("/swimmers/{swimmer_id}/practices", response_model=list[PracticeOut])
def get_swimmer_practices(swimmer_id: int):
    if (swimmers.get(swimmer_id) is None):
        raise HTTPException(status_code=404, detail="Swimmer not found")

    assigned = [practices[a.practice_id] for a in assignments if a.swimmer_id == swimmer_id]
    assigned.sort(key=lambda practice: practice.practice_id)

    return assigned
