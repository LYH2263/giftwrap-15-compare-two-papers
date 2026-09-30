from pydantic import BaseModel, Field

class EstimateRequest(BaseModel):
    box_id: int
    overlap: float | None = None
    wrap_style: str = "cross"
    save: bool = False
    note: str = ""

class VoidRequest(BaseModel):
    reason: str = Field(min_length=1)
