from pydantic import BaseModel, Field

MAX_ABS_INT = 1_000_000

class AddArgs(BaseModel):
    a: int = Field(..., ge=-MAX_ABS_INT, le=MAX_ABS_INT)
    b: int = Field(..., ge=-MAX_ABS_INT, le=MAX_ABS_INT)

class MultiplyArgs(BaseModel):
    a: int = Field(..., ge=-MAX_ABS_INT, le=MAX_ABS_INT)
    b: int = Field(..., ge=-MAX_ABS_INT, le=MAX_ABS_INT)