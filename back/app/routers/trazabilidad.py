from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import  TrazabilidadEntity
from app.schemas import TrazabilidadCreate, TrazabilidadResponse
router = APIRouter()


@router.get("/", response_model=List[TrazabilidadResponse])
def listar_trazabilidad(db: Session = Depends(get_db)):
    return db.query(TrazabilidadEntity).all()


@router.get("/{trazabilidad_id}", response_model=TrazabilidadResponse)
def obtener_trazabilidad(trazabilidad_id: int, db: Session = Depends(get_db)):
    trazabilidad = db.query(TrazabilidadEntity).filter(TrazabilidadEntity.id == trazabilidad_id).first()
    if not trazabilidad:
        raise HTTPException(status_code=404, detail="Trazabilidad no encontrada")
    return trazabilidad


@router.post("/", response_model=TrazabilidadResponse, status_code=201)
def crear_trazabilidad(trazabilidad: TrazabilidadCreate, db: Session = Depends(get_db)):
    nuevo = TrazabilidadEntity(**trazabilidad.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.put("/{trazabilidad_id}", response_model=TrazabilidadResponse)
def actualizar_trazabilidad(trazabilidad_id: int, datos: TrazabilidadCreate, db: Session = Depends(get_db)):
    trazabilidad = db.query(TrazabilidadEntity).filter(TrazabilidadEntity.id == trazabilidad_id).first()
    if not trazabilidad:
        raise HTTPException(status_code=404, detail="Trazabilidad no encontrada")
    for campo, valor in datos.model_dump().items():
        setattr(trazabilidad, campo, valor)
    db.commit()
    db.refresh(trazabilidad)
    return trazabilidad


@router.delete("/{trazabilidad_id}", status_code=204)
def eliminar_trazabilidad(trazabilidad_id: int, db: Session = Depends(get_db)):
    trazabilidad = db.query(TrazabilidadEntity).filter(TrazabilidadEntity.id == trazabilidad_id).first()
    if not trazabilidad:
        raise HTTPException(status_code=404, detail="Trazabilidad no encontrada")
    db.delete(trazabilidad)
    db.commit()