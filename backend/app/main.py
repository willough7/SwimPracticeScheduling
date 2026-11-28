from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import Response
from datetime import date
from app.schemas import (SwimmerCreate, SwimmerOut, PracticeCreate, PracticeOut, PracticeConflictsOut,
                         LaneUpdate, LanePlacementOut)
from app.storage import swimmers, _ids, practices, _practice_ids, assignments, lanes
from app.models import Swimmer, Practice, Day, Assignment
from app.ics_parser import parse_calendar, monday_of
from app.conflicts import get_swimmers_status_for_practice
from app.export import build_week_workbook

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

# PUT replaces the swimmer's details with the ones sent. The id stays the same,
# so their assignments still point at them, and their uploaded calendar is kept
# (calendars are changed through PUT /swimmers/{swimmer_id}/schedule instead).
@app.put("/swimmers/{swimmer_id}", response_model=SwimmerOut)
def update_swimmer(swimmer_id: int, data: SwimmerCreate):
    swimmer = swimmers.get(swimmer_id)
    if(swimmer is None):
        raise HTTPException(status_code=404, detail="Swimmer not found")

    swimmer.first_name = data.first_name
    swimmer.last_name = data.last_name
    swimmer.weights_group = data.weights_group
    swimmer.tags = data.tags

    return swimmer_to_swimmerout(swimmer)

@app.delete("/swimmers/{swimmer_id}", status_code=204)
def delete_swimmer(swimmer_id: int):
    if swimmers.get(swimmer_id) is None:
        raise HTTPException(status_code=404, detail="Swimmer not found")
    swimmers.pop(swimmer_id)
    # Remove this swimmer's assignments (and their lane spots) too, so none point at a swimmer that no longer exists.
    removed = {a for a in assignments if a.swimmer_id == swimmer_id}
    assignments.difference_update(removed)
    for assignment in removed:
        lanes.pop(assignment, None)

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

# PUT replaces every field of the practice. The id stays the same, so its
# swimmer assignments carry over to the new day and times.
@app.put("/practices/{practice_id}", response_model=PracticeOut)
def update_practice(practice_id: int, data: PracticeCreate):
    if(practices.get(practice_id) is None):
        raise HTTPException(status_code=404, detail="Practice not found")

    practice = Practice(practice_id=practice_id, **data.model_dump())
    practices[practice_id] = practice
    return practice

@app.delete("/practices/{practice_id}", status_code=204)
def delete_practice(practice_id: int):
    if practices.get(practice_id) is None:
        raise HTTPException(status_code=404, detail="Practice not found")
    practices.pop(practice_id)
    # Remove this practice's assignments (and their lane spots) too, so none point at a practice that no longer exists.
    removed = {a for a in assignments if a.practice_id == practice_id}
    assignments.difference_update(removed)
    for assignment in removed:
        lanes.pop(assignment, None)

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
    lanes.pop(assignment, None)   # an unassigned swimmer can't keep a lane


@app.get("/swimmers/{swimmer_id}/practices", response_model=list[PracticeOut])
def get_swimmer_practices(swimmer_id: int):
    if (swimmers.get(swimmer_id) is None):
        raise HTTPException(status_code=404, detail="Swimmer not found")

    assigned = [practices[a.practice_id] for a in assignments if a.swimmer_id == swimmer_id]
    assigned.sort(key=lambda practice: practice.practice_id)

    return assigned

#lanes

# Lanes repeat every week, like assignments. Only assigned swimmers can be
# placed in a lane; sending {"lane": null} takes a swimmer out of their lane
# but keeps them assigned to the practice.
@app.put("/practices/{practice_id}/swimmers/{swimmer_id}/lane", status_code=204)
def set_swimmer_lane(practice_id: int, swimmer_id: int, data: LaneUpdate):
    if (practices.get(practice_id) is None):
        raise HTTPException(status_code=404, detail="Practice not found")
    if (swimmers.get(swimmer_id) is None):
        raise HTTPException(status_code=404, detail="Swimmer not found")

    assignment = Assignment(swimmer_id=swimmer_id, practice_id=practice_id)
    if (assignment not in assignments):
        raise HTTPException(status_code=404, detail="Swimmer is not assigned to this practice")

    if (data.lane is None):
        lanes.pop(assignment, None)
    else:
        lanes[assignment] = data.lane


@app.get("/practices/{practice_id}/lanes", response_model=list[LanePlacementOut])
def get_practice_lanes(practice_id: int):
    if (practices.get(practice_id) is None):
        raise HTTPException(status_code=404, detail="Practice not found")

    placements = [LanePlacementOut(swimmer_id=a.swimmer_id, lane=lane)
                  for a, lane in lanes.items() if a.practice_id == practice_id]
    placements.sort(key=lambda placement: (placement.lane, placement.swimmer_id))
    return placements

#export

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# The whole week as an Excel file: one sheet per day, each practice laid out
# with lanes 1-8 as columns. Content-Disposition "attachment" tells the browser
# to download it (with that file name) instead of trying to open it in the tab.
# ?day=1-7 picks the sheet that's showing when the file opens (default Monday).
@app.get("/export/week.xlsx")
def export_week(day: Day = Day.MONDAY):
    content = build_week_workbook(practices.values(), swimmers, assignments, lanes, open_on=day)
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": 'attachment; filename="practice-schedule.xlsx"'},
    )
