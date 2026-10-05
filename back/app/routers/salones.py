from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from datetime import datetime

from app.database import get_db
from app.models import  SalonesEntity
from app.schemas import SalonCreate, SalonResponse, SalonUpdate, SalonDisponibleResponse

router = APIRouter()


@router.get("/", response_model=List[SalonResponse])
def listar_salones(db: Session = Depends(get_db)):
    return db.query(SalonesEntity).all()

@router.get("/disponibles", response_model=List[SalonDisponibleResponse])
def listar_salones_disponibles(fecha_inicio: datetime, fecha_fin: datetime, aforo: int= Query(..., gt=0), db: Session = Depends(get_db)):
    if fecha_fin <= fecha_inicio:
        raise HTTPException(status_code=422, detail="La fecha y hora de fin debe ser posterior al inicio")

    consulta = text("""
        select * from fn_salones_disponibles(:fecha_inicio, :fecha_fin, :aforo)
    """)

    resultado = db.execute(consulta, {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin, "aforo": aforo}).mappings().all()

    return resultado


@router.get("/{salon_id}", response_model=SalonResponse)
def obtener_salon(salon_id: int, db: Session = Depends(get_db)):
    salon = db.query(SalonesEntity).filter(SalonesEntity.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salón no encontrado")
    return salon


@router.post("/", response_model=SalonResponse, status_code=201)
def crear_salon(salon: SalonCreate, db: Session = Depends(get_db)):
    nuevo = SalonesEntity(**salon.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.patch("/{salon_id}", response_model=SalonResponse)
def actualizar_salon(salon_id: int, datos: SalonUpdate, db: Session = Depends(get_db)):
    salon = db.query(SalonesEntity).filter(SalonesEntity.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salón no encontrado")
    for campo, valor in datos.model_dump().items():
        setattr(salon, campo, valor)
    db.commit()
    db.refresh(salon)
    return salon


@router.delete("/{salon_id}", status_code=204)
def eliminar_salon(salon_id: int, db: Session = Depends(get_db)):
    salon = db.query(SalonesEntity).filter(SalonesEntity.id == salon_id).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salón no encontrado")
    db.delete(salon)
    db.commit()