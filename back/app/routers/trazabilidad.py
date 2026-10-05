from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import EventosEntity, TrazabilidadEntity
from app.schemas import TrazabilidadResponse

router = APIRouter()


@router.get("/eventos/{evento_id}/auditoria", response_model=List[TrazabilidadResponse])
def obtener_auditoria_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.query(EventosEntity).filter(EventosEntity.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    return db.query(TrazabilidadEntity).filter(TrazabilidadEntity.evento_id == evento_id).order_by(TrazabilidadEntity.fecha_hora.asc()).all()