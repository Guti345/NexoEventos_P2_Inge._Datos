from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional

from app.database import get_db
from app.schemas import OrganigramaResponse, EscalamientoResponse, ParetoClienteResponse, OcupacionSalonResponse

router = APIRouter()


@router.get("/organigrama", response_model=List[OrganigramaResponse])
def reporte_organigrama(staff_id: Optional[int] = Query(None, gt=0), db: Session = Depends(get_db)):
    consulta = text("SELECT * FROM fn_organigrama(:staff_id)")
    return db.execute(consulta, {"staff_id": staff_id}).mappings().all()


@router.get("/escalamiento/{staff_id}", response_model=List[EscalamientoResponse])
def reporte_escalamiento(staff_id: int, db: Session = Depends(get_db)):
    consulta = text("SELECT * FROM fn_cadena_escalamiento(:staff_id)")
    resultado = db.execute(consulta, {"staff_id": staff_id}).mappings().all()

    if not resultado:
        raise HTTPException(status_code=404, detail="No se encontró cadena de escalamiento para este miembro del staff")

    return resultado


@router.get("/pareto-clientes", response_model=List[ParetoClienteResponse])
def reporte_pareto_clientes(db: Session = Depends(get_db)):
    consulta = text("SELECT * FROM vista_ranking_clientes ORDER BY posicion")
    return db.execute(consulta).mappings().all()


@router.get("/ocupacion-salones", response_model=List[OcupacionSalonResponse])
def reporte_ocupacion_salones(salon_id: Optional[int] = Query(None, gt=0), db: Session = Depends(get_db)):
    if salon_id is None:
        consulta = text("SELECT * FROM vista_ocupacion_salones ORDER BY salon_id, numero_en_salon")
        parametros = {}
    else:
        consulta = text("SELECT * FROM vista_ocupacion_salones WHERE salon_id = :salon_id ORDER BY numero_en_salon")
        parametros = {"salon_id": salon_id}

    return db.execute(consulta, parametros).mappings().all()