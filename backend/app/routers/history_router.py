from fastapi import APIRouter, HTTPException
from app.repositories import history as repo
from app.schemas.estimate import VoidRequest

router = APIRouter()

@router.get("/runs")
def runs(limit: int = 50, include_voided: bool = False):
    count, area = repo.active_totals()
    return {
        "items": repo.list_runs(limit, include_voided=include_voided),
        "active_count": count,
        "active_area_m2": area,
    }

@router.get("/runs/{run_id}")
def get_run(run_id: int):
    run = repo.get_run(run_id)
    if run is None:
        raise HTTPException(404, "run not found")
    return run

@router.post("/runs/{run_id}/void")
def void_run(run_id: int, body: VoidRequest):
    try:
        return repo.void_run(run_id, body.reason)
    except repo.VoidError as e:
        raise HTTPException(e.code, e.detail)
