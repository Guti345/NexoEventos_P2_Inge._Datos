from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from math import ceil
from decimal import Decimal
from sqlalchemy.exc import InternalError

from app.database import get_db
from app.models import EventosEntity, InscripcionesEntity
from app.schemas import EventoCreate, EventoResponse, EventoUpdate, EventoEstadoUpdate, EventoDetalleResponse, ServicioEventoResponse, AsistenciaResumenResponse, CotizacionResponse, CotizacionServicioResponse

router = APIRouter()


@router.get("/", response_model=List[EventoResponse])
def listar_eventos(estado: Optional[str] = None, cliente_id: Optional[int] = None, salon_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(EventosEntity)
    if estado:
        query = query.filter(EventosEntity.estado == estado)
    if cliente_id:
        query = query.filter(EventosEntity.cliente_id == cliente_id)
    if salon_id:
        query = query.filter(EventosEntity.salon_id == salon_id)
    return query.all()

@router.get("/{evento_id}/cotizacion", response_model=CotizacionResponse)
def obtener_cotizacion(evento_id: int, db: Session = Depends(get_db)):
    evento = db.query(EventosEntity).filter(EventosEntity.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    horas_salon = ceil((evento.fin - evento.inicio).total_seconds() / 3600)
    valor_total_salon = horas_salon * evento.precio_hora_salon_cotizado

    servicios = []
    total_servicios = Decimal("0.00")

    for servicio_evento in evento.servicios_eventos:
        subtotal = servicio_evento.cantidad * servicio_evento.precio_unidad_cotizado
        total_servicios += subtotal

        servicios.append(
            CotizacionServicioResponse(
                nombre_servicio=servicio_evento.servicio.nombre_servicio,
                unidad_cobro=servicio_evento.servicio.unidad_cobro,
                precio_unidad_cotizado=servicio_evento.precio_unidad_cotizado,
                cantidad=servicio_evento.cantidad,
                valor_total_cotizado=subtotal
            )
        )

    return CotizacionResponse(
        evento_id=evento.id,
        hora_salon=horas_salon,
        precio_hora_salon=evento.precio_hora_salon_cotizado,
        valor_total_salon=valor_total_salon,
        servicios=servicios,
        total_servicios=total_servicios,
        valor_total_cotizado=evento.valor_total_cotizado
    )


@router.get("/{evento_id}", response_model=EventoResponse)
def obtener_evento(evento_id: int, db: Session = Depends(get_db)):
    evento = db.query(EventosEntity).filter(EventosEntity.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    inscritos = db.query(InscripcionesEntity).filter(InscripcionesEntity.evento_id == evento_id).count()
    asistentes_reales = db.query(InscripcionesEntity).filter(InscripcionesEntity.evento_id == evento_id, InscripcionesEntity.fecha_checkin.isnot(None)).count()
    asistencia = AsistenciaResumenResponse(inscritos=inscritos, asistentes_reales=asistentes_reales, tasa_asistecia=evento.tasa_asistencia)
    evento_data = EventoResponse.model_validate(evento).model_dump()
    return EventoDetalleResponse(**evento_data, servicios=[ServicioEventoResponse.model_validate(servicio) for servicio in evento.servicios_eventos], asistencia=asistencia)


@router.post("/", response_model=EventoResponse, status_code=201)
def crear_evento(evento: EventoCreate, db: Session = Depends(get_db)):
    nuevo = EventosEntity(**evento.model_dump())
    db.add(nuevo)

    try:
        db.commit()
        db.refresh(nuevo)
        return nuevo
    
    except InternalError as exc:
        db.rollback()
        
        mensaje = getattr(
            getattr(exc.orig, "diag", None),
            "mensaje_primary",
            str(exc.orig).splitlines()[0]
        )
        raise HTTPException(status_code=409, detail=mensaje)


@router.patch("/{evento_id}", response_model=EventoResponse)
def actualizar_evento(evento_id: int, datos: EventoUpdate, db: Session = Depends(get_db)):
    evento = db.query(EventosEntity).filter(EventosEntity.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(evento, campo, valor)

    try:
        db.commit()
        db.refresh(evento)
    except InternalError as exc:
        db.rollback()
        mensaje=getattr(getattr(exc.orig, "diag", None), "message_primary", str(exc.orig).splitlines()[0])
        raise HTTPException(status_code=409, detail=mensaje)
    return evento


@router.patch("/{evento_id}/estado", response_model=EventoResponse)
def actualizar_estado_evento(evento_id: int, datos: EventoEstadoUpdate, db: Session = Depends(get_db)):
    evento = db.query(EventosEntity).filter(EventosEntity.id == evento_id).first()
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    evento.estado = datos.estado
    db.commit()
    db.refresh(evento)
    return evento

@router.delete("/{evento_id}", status_code=204)
def eliminar_evento(evento_id: int, db: Session = Depends(get_db)):

    evento = db.query(EventosEntity).filter(
        EventosEntity.id == evento_id
    ).first()

    if not evento:
        raise HTTPException(
            status_code=404,
            detail="Evento no encontrado"
        )

    db.delete(evento)
    db.commit()


