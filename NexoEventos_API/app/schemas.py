from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class PacienteBase(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    fecha_nacimiento: date
    contacto: str
    referido_por_id: Optional[int] = None


class PacienteCreate(PacienteBase):
    pass


class PacienteResponse(PacienteBase):
    id: int

    class Config:
        from_attributes = True


class TratamientoBase(BaseModel):
    paciente_id: int
    medico_id: int
    diagnostico: str
    sesiones_estimadas: int = Field(..., gt=0)


class TratamientoCreate(TratamientoBase):
    pass


class TratamientoResponse(TratamientoBase):
    id: int
    estado: str
    eficacia_calculada: Optional[float] = None

    class Config:
        from_attributes = True
