from fastapi import FastAPI, HTTPException
from app.schemas import SwimmerCreate, SwimmerOut
from app.storage import swimmers, _ids
from app.models import Swimmer

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