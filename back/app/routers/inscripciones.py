from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import  InscripcionesEntity
from app.schemas import InscripcionCreate, InscripcionResponse

router = APIRouter()


@router.get("/", response_model=List[InscripcionResponse])
def listar_inscripciones(db: Session = Depends(get_db)):
    return db.query(InscripcionesEntity).all()


@router.get("/{inscripcion_id}", response_model=InscripcionResponse)
def obtener_inscripcion(inscripcion_id: int, db: Session = Depends(get_db)):
    inscripcion = db.query(InscripcionesEntity).filter(InscripcionesEntity.id == inscripcion_id).first()
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    return inscripcion


@router.post("/", response_model=InscripcionResponse, status_code=201)
def crear_inscripcion(inscripcion: InscripcionCreate, db: Session = Depends(get_db)):
    nueva = InscripcionesEntity(**inscripcion.model_dump())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.put("/{inscripcion_id}", response_model=InscripcionResponse)
def actualizar_inscripcion(inscripcion_id: int, datos: InscripcionCreate, db: Session = Depends(get_db)):
    inscripcion = db.query(InscripcionesEntity).filter(InscripcionesEntity.id == inscripcion_id).first()
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    for campo, valor in datos.model_dump().items():
        setattr(inscripcion, campo, valor)
    db.commit()
    db.refresh(inscripcion)
    return inscripcion


@router.delete("/{inscripcion_id}", status_code=204)
def eliminar_inscripcion(inscripcion_id: int, db: Session = Depends(get_db)):
    inscripcion = db.query(InscripcionesEntity).filter(InscripcionesEntity.id == inscripcion_id).first()
    if not inscripcion:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    db.delete(inscripcion)
    db.commit()