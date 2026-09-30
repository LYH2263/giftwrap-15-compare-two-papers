from fastapi import APIRouter, HTTPException
from app.repositories import history as repo
from app.schemas.history import VoidRunRequest

router = APIRouter()


@router.get("/runs")
def runs(limit: int = 50, include_voided: bool = False):
    return {
        "items": repo.list_runs(limit, include_voided=include_voided),
        "summary": repo.active_summary(),
    }


@router.get("/runs/{run_id}")
def get_run(run_id: int):
    run = repo.get_run(run_id)
    if run is None:
        raise HTTPException(404, "用纸单不存在")
    return run


@router.post("/runs/{run_id}/void")
def void_run(run_id: int, body: VoidRunRequest):
    try:
        return repo.void_run(run_id, body.reason)
    except repo.RunNotFound:
        raise HTTPException(404, "用纸单不存在")
    except repo.RunAlreadyVoided:
        raise HTTPException(409, "该用纸单已作废，不能再次作废")
