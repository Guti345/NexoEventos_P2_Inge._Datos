from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import InternalError, IntegrityError
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models import EventosEntity, InscripcionesEntity, AsistentesEntity
from app.schemas import InscripcionCreate, InscripcionResponse, CheckinCreate

router = APIRouter()


@router.get("/eventos/{evento_id}/inscripciones", response_model=List[InscripcionResponse])
def listar_inscripciones_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.query(EventosEntity).filter(EventosEntity.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    return db.query(InscripcionesEntity).filter(InscripcionesEntity.evento_id == evento_id).all()


@router.get("/eventos/{evento_id}/inscripciones/{inscripcion_id}", response_model=InscripcionResponse)
def obtener_inscripcion(evento_id: int, inscripcion_id: int, db: Session = Depends(get_db)):
    inscripcion = db.query(InscripcionesEntity).filter(InscripcionesEntity.id == inscripcion_id, InscripcionesEntity.evento_id == evento_id).first()
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada en este evento")

    return inscripcion


@router.post("/eventos/{evento_id}/inscripciones", response_model=InscripcionResponse, status_code=201)
def crear_inscripcion(evento_id: int, datos: InscripcionCreate, db: Session = Depends(get_db)):
    evento = db.query(EventosEntity).filter(EventosEntity.id == evento_id).first()

    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    existente = db.query(InscripcionesEntity).filter(InscripcionesEntity.evento_id == evento_id, InscripcionesEntity.asistente_id == datos.asistente_id).first()

    if existente:
        raise HTTPException(status_code=409, detail="El asistente ya está inscrito en este evento")

    nueva = InscripcionesEntity(evento_id=evento_id, **datos.model_dump())
    db.add(nueva)

    try:
        db.commit()
        db.refresh(nueva)
        return nueva

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El asistente ya está inscrito en este evento")

    except InternalError as exc:
        db.rollback()
        mensaje = getattr(getattr(exc.orig, "diag", None), "message_primary", str(exc.orig).splitlines()[0])
        raise HTTPException(status_code=409, detail=mensaje)


@router.delete("/eventos/{evento_id}/inscripciones/{inscripcion_id}", status_code=204)
def eliminar_inscripcion(evento_id: int, inscripcion_id: int, db: Session = Depends(get_db)):
    inscripcion = db.query(InscripcionesEntity).filter(InscripcionesEntity.id == inscripcion_id, InscripcionesEntity.evento_id == evento_id).first()
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada en este evento")

    db.delete(inscripcion)
    db.commit()

@router.post("/eventos/{evento_id}/checkin", response_model=InscripcionResponse)
def registrar_checkin(evento_id: int, datos: CheckinCreate, db: Session = Depends(get_db)):
    evento = db.query(EventosEntity).filter(EventosEntity.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    asistente = db.query(AsistentesEntity).filter(AsistentesEntity.documento_identidad == datos.documento_identidad).first()
    if not asistente:
        raise HTTPException(status_code=404, detail="Asistente no encontrado")

    inscripcion = db.query(InscripcionesEntity).filter(InscripcionesEntity.evento_id == evento_id, InscripcionesEntity.asistente_id == asistente.id).first()
    if not inscripcion:
        raise HTTPException(status_code=404, detail="El asistente no está inscrito en este evento")

    inscripcion.fecha_checkin = func.now()

    db.commit()
    db.refresh(inscripcion)
    return inscripcion