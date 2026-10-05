from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import  AsistentesEntity
from app.schemas import AsistenteCreate, AsistenteResponse, AsistenteUpdate

router = APIRouter()


@router.get("/", response_model=List[AsistenteResponse])
def listar_asistentes(db: Session = Depends(get_db)):
    return db.query(AsistentesEntity).all()


@router.get("/{asistente_id}", response_model=AsistenteResponse)
def obtener_asistente(asistente_id: int, db: Session = Depends(get_db)):
    asistente = db.query(AsistentesEntity).filter(AsistentesEntity.id == asistente_id).first()
    if not asistente:
        raise HTTPException(status_code=404, detail="Asistente no encontrado")
    return asistente


@router.post("/", response_model=AsistenteResponse, status_code=201)
def crear_asistente(asistente: AsistenteCreate, db: Session = Depends(get_db)):
    nuevo = AsistentesEntity(**asistente.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.patch("/{asistente_id}", response_model=AsistenteResponse)
def actualizar_asistente(asistente_id: int, datos: AsistenteUpdate, db: Session = Depends(get_db)):
    asistente = db.query(AsistentesEntity).filter(AsistentesEntity.id == asistente_id).first()
    if not asistente:
        raise HTTPException(status_code=404, detail="Asistente no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(asistente, campo, valor)
    db.commit()
    db.refresh(asistente)
    return asistente


@router.delete("/{asistente_id}", status_code=204)
def eliminar_asistente(asistente_id: int, db: Session = Depends(get_db)):
    asistente = db.query(AsistentesEntity).filter(AsistentesEntity.id == asistente_id).first()
    if not asistente:
        raise HTTPException(status_code=404, detail="Asistente no encontrado")
    db.delete(asistente)
    db.commit()