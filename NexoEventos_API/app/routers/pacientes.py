from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import PacienteEntity
from app.schemas import PacienteCreate, PacienteResponse

router = APIRouter()


@router.get("/", response_model=List[PacienteResponse])
def listar_pacientes(db: Session = Depends(get_db)):
    return db.query(PacienteEntity).all()


@router.get("/{paciente_id}", response_model=PacienteResponse)
def obtener_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.query(PacienteEntity).filter(PacienteEntity.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente


@router.post("/", response_model=PacienteResponse, status_code=201)
def crear_paciente(paciente: PacienteCreate, db: Session = Depends(get_db)):
    nuevo = PacienteEntity(**paciente.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.put("/{paciente_id}", response_model=PacienteResponse)
def actualizar_paciente(paciente_id: int, datos: PacienteCreate, db: Session = Depends(get_db)):
    paciente = db.query(PacienteEntity).filter(PacienteEntity.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    for campo, valor in datos.model_dump().items():
        setattr(paciente, campo, valor)
    db.commit()
    db.refresh(paciente)
    return paciente


@router.delete("/{paciente_id}", status_code=204)
def eliminar_paciente(paciente_id: int, db: Session = Depends(get_db)):
    paciente = db.query(PacienteEntity).filter(PacienteEntity.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    db.delete(paciente)
    db.commit()
