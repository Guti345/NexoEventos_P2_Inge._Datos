from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import TratamientoEntity
from app.schemas import TratamientoCreate, TratamientoResponse

router = APIRouter()


@router.get("/", response_model=List[TratamientoResponse])
def listar_tratamientos(db: Session = Depends(get_db)):
    return db.query(TratamientoEntity).all()


@router.get("/{tratamiento_id}", response_model=TratamientoResponse)
def obtener_tratamiento(tratamiento_id: int, db: Session = Depends(get_db)):
    tratamiento = db.query(TratamientoEntity).filter(TratamientoEntity.id == tratamiento_id).first()
    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return tratamiento


@router.post("/", response_model=TratamientoResponse, status_code=201)
def crear_tratamiento(tratamiento: TratamientoCreate, db: Session = Depends(get_db)):
    nuevo = TratamientoEntity(**tratamiento.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.put("/{tratamiento_id}", response_model=TratamientoResponse)
def actualizar_tratamiento(tratamiento_id: int, datos: TratamientoCreate, db: Session = Depends(get_db)):
    tratamiento = db.query(TratamientoEntity).filter(TratamientoEntity.id == tratamiento_id).first()
    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    for campo, valor in datos.model_dump().items():
        setattr(tratamiento, campo, valor)
    db.commit()
    db.refresh(tratamiento)
    return tratamiento


@router.delete("/{tratamiento_id}", status_code=204)
def eliminar_tratamiento(tratamiento_id: int, db: Session = Depends(get_db)):
    tratamiento = db.query(TratamientoEntity).filter(TratamientoEntity.id == tratamiento_id).first()
    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    db.delete(tratamiento)
    db.commit()
