from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import  StaffEntity
from app.schemas import StaffCreate, StaffResponse

router = APIRouter()


@router.get("/", response_model=List[StaffResponse])
def listar_staff(db: Session = Depends(get_db)):
    return db.query(StaffEntity).all()


@router.get("/{staff_id}", response_model=StaffResponse)
def obtener_staff(staff_id: int, db: Session = Depends(get_db)):
    staff = db.query(StaffEntity).filter(StaffEntity.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff no encontrado")
    return staff


@router.post("/", response_model=StaffResponse, status_code=201)
def crear_staff(staff: StaffCreate, db: Session = Depends(get_db)):
    nuevo = StaffEntity(**staff.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.put("/{staff_id}", response_model=StaffResponse)
def actualizar_staff(staff_id: int, datos: StaffCreate, db: Session = Depends(get_db)):
    staff = db.query(StaffEntity).filter(StaffEntity.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff no encontrado")
    for campo, valor in datos.model_dump().items():
        setattr(staff, campo, valor)
    db.commit()
    db.refresh(staff)
    return staff


@router.delete("/{staff_id}", status_code=204)
def eliminar_staff(staff_id: int, db: Session = Depends(get_db)):
    staff = db.query(StaffEntity).filter(StaffEntity.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff no encontrado")
    db.delete(staff)
    db.commit()