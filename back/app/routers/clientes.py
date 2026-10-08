from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from typing import List, Optional

from app.database import get_db
from app.models import ClientesEntity, EventosEntity
from app.schemas import ClienteCreate, ClienteUpdate, ClienteResponse, EventoResponse

router = APIRouter()


@router.get("/", response_model=List[ClienteResponse])
def listar_clientes(buscar: Optional[str] = Query(None), tipo_documento: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(ClientesEntity)
    #busqueda general
    if buscar:
        query = query.filter(or_(
            ClientesEntity.nombre.ilike(f"%{buscar}%"),
            ClientesEntity.numero_documento.ilike(f"%{buscar}%"),
            ClientesEntity.email.ilike(f"%{buscar}%")
        ))
    #filtro especifico por tipo de documento
    if tipo_documento:
        query = query.filter(ClientesEntity.tipo_documento == tipo_documento)

    return query.all()


@router.get("/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(ClientesEntity).filter(ClientesEntity.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.get("/{cliente_id}/eventos", response_model=List[EventoResponse])
def obtener_eventos_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(ClientesEntity).filter(ClientesEntity.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return db.query(EventosEntity).filter(EventosEntity.cliente_id == cliente_id).all()


@router.post("/", response_model=ClienteResponse, status_code=201)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    nuevo = ClientesEntity(**cliente.model_dump())
    db.add(nuevo)
    try:
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese número de documento.")


@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(cliente_id: int, datos: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.query(ClientesEntity).filter(ClientesEntity.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}", status_code=204)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(ClientesEntity).filter(ClientesEntity.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    db.delete(cliente)
    db.commit()