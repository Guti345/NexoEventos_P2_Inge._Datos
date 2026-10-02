from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import  SalonesEntity
from app.schemas import SalonCreate, SalonResponse

router = APIRouter()


@router.get("/", response_model=List[SalonResponse])
def listar_salones(db: Session = Depends(get_db)):
    return db.query(SalonesEntity).all()


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


@router.put("/{salon_id}", response_model=SalonResponse)
def actualizar_salon(salon_id: int, datos: SalonCreate, db: Session = Depends(get_db)):
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