from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import ServiciosEntity
from app.schemas import ServicioCreate, ServicioResponse, ServicioUpdate

router = APIRouter()


@router.get("/", response_model=List[ServicioResponse])
def listar_servicios(db: Session = Depends(get_db)):
    return db.query(ServiciosEntity).all()


@router.get("/{servicio_id}", response_model=ServicioResponse)
def obtener_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = db.query(ServiciosEntity).filter(ServiciosEntity.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return servicio


@router.post("/", response_model=ServicioResponse, status_code=201)
def crear_servicio(servicio: ServicioCreate, db: Session = Depends(get_db)):
    nuevo = ServiciosEntity(**servicio.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.patch("/{servicio_id}", response_model=ServicioResponse)
def actualizar_servicio(servicio_id: int, datos: ServicioUpdate, db: Session = Depends(get_db)):
    servicio = db.query(ServiciosEntity).filter(ServiciosEntity.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(servicio, campo, valor)
    db.commit()
    db.refresh(servicio)
    return servicio


@router.delete("/{servicio_id}", status_code=204)
def eliminar_servicio(servicio_id: int, db: Session = Depends(get_db)):
    servicio = db.query(ServiciosEntity).filter(ServiciosEntity.id == servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    db.delete(servicio)
    db.commit()