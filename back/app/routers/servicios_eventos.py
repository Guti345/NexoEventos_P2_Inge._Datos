from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import ServiciosEventosEntity
from app.schemas import ServiciosEventoCreate, ServiciosEventoResponse

router = APIRouter()


@router.get("/", response_model=List[ServiciosEventoResponse])
def listar_servicios_eventos(db: Session = Depends(get_db)):
    return db.query(ServiciosEventosEntity).all()


@router.get("/{servicio_evento_id}", response_model=ServiciosEventoResponse)
def obtener_servicio_evento(servicio_evento_id: int, db: Session = Depends(get_db)):
    servicio_evento = db.query(ServiciosEventosEntity).filter(ServiciosEventosEntity.id == servicio_evento_id).first()
    if not servicio_evento:
        raise HTTPException(status_code=404, detail="Servicio-Evento no encontrado")
    return servicio_evento


@router.post("/", response_model=ServiciosEventoResponse, status_code=201)
def crear_servicio_evento(servicio_evento: ServiciosEventoCreate, db: Session = Depends(get_db)):
    nuevo = ServiciosEventosEntity(**servicio_evento.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.put("/{servicio_evento_id}", response_model=ServiciosEventoResponse)
def actualizar_servicio_evento(servicio_evento_id: int, datos: ServiciosEventoCreate, db: Session = Depends(get_db)):
    servicio_evento = db.query(ServiciosEventosEntity).filter(ServiciosEventosEntity.id == servicio_evento_id).first()
    if not servicio_evento:
        raise HTTPException(status_code=404, detail="Servicio-Evento no encontrado")
    for campo, valor in datos.model_dump().items():
        setattr(servicio_evento, campo, valor)
    db.commit()
    db.refresh(servicio_evento)
    return servicio_evento


@router.delete("/{servicio_evento_id}", status_code=204)
def eliminar_servicio_evento(servicio_evento_id: int, db: Session = Depends(get_db)):
    servicio_evento = db.query(ServiciosEventosEntity).filter(ServiciosEventosEntity.id == servicio_evento_id).first()
    if not servicio_evento:
        raise HTTPException(status_code=404, detail="Servicio-Evento no encontrado")
    db.delete(servicio_evento)
    db.commit()