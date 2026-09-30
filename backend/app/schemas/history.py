from pydantic import BaseModel, field_validator


class VoidRunRequest(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("作废原因不能为空")
        return v.strip()
