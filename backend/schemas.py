from typing import Annotated, Literal
from pydantic import BaseModel, Field, StrictInt

class CrearSimulacion(BaseModel):
    numero_trabajos: Annotated[StrictInt, Field(gt=0)]
    seed: StrictInt | None = None

class AccionSimulacion(BaseModel):
    accion: Literal["interrupt", "error", "pause", "continue"]