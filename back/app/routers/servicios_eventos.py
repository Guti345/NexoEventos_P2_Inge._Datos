from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import InternalError, IntegrityError

from app.database import get_db
from app.models import EventosEntity, ServiciosEventosEntity
from app.schemas import ServicioEventoCreate, ServicioEventoUpdate, ServicioEventoDelete, ServicioEventoResponse

router = APIRouter()


@router.get("/eventos/{evento_id}/servicios", response_model=List[ServicioEventoResponse])
def listar_servicios_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.query(EventosEntity).filter(EventosEntity.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return db.query(ServiciosEventosEntity).filter(ServiciosEventosEntity.evento_id == evento_id).all()


from sqlalchemy.exc import InternalError, IntegrityError

@router.post("/eventos/{evento_id}/servicios", response_model=ServicioEventoResponse, status_code=201)
def agregar_servicio_evento(evento_id: int, datos: ServicioEventoCreate, db: Session = Depends(get_db)):
    evento = db.query(EventosEntity).filter(EventosEntity.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    nuevo = ServiciosEventosEntity(evento_id=evento_id, **datos.model_dump())

    try:
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo

    except InternalError as exc:
        db.rollback()
        mensaje = getattr(getattr(exc.orig, "diag", None), "message_primary", str(exc.orig).splitlines()[0])
        raise HTTPException(status_code=409, detail=mensaje)


@router.put("/eventos/{evento_id}/servicios", response_model=ServicioEventoResponse)
def actualizar_servicio_evento(evento_id: int, datos: ServicioEventoUpdate, db: Session = Depends(get_db)):
    servicio_evento = db.query(ServiciosEventosEntity).filter(ServiciosEventosEntity.evento_id == evento_id, ServiciosEventosEntity.servicio_id == datos.servicio_id).first()
    if not servicio_evento:
        raise HTTPException(status_code=404, detail="Servicio no encontrado en este evento")

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(servicio_evento, campo, valor)

    db.commit()
    db.refresh(servicio_evento)
    return servicio_evento


@router.delete("/eventos/{evento_id}/servicios", status_code=204)
def eliminar_servicio_evento(evento_id: int, datos: ServicioEventoDelete, db: Session = Depends(get_db)):
    servicio_evento = db.query(ServiciosEventosEntity).filter(ServiciosEventosEntity.evento_id == evento_id, ServiciosEventosEntity.servicio_id == datos.servicio_id).first()
    if not servicio_evento:
        raise HTTPException(status_code=404, detail="Servicio no encontrado en este evento")

    db.delete(servicio_evento)
    db.commit()