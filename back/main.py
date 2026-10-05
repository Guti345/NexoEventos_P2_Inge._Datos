from fastapi import FastAPI

from app.database import engine, Base
from app import models
from app.routers import clientes, salones, eventos, servicios, servicios_eventos, asistentes, inscripciones, staff, trazabilidad, reportes

# 1. Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# 2. Instancia principal de la API
app = FastAPI(
    title="NexoEventos API",
    description="Sistema de gestión de eventos para el Centro de Convenciones Nexo",
    version="1.0.0"
)

# 3. Incluir los Routers (Controladores)
# Routers principales
app.include_router(clientes.router, prefix="/clientes", tags=["Clientes"])
app.include_router(salones.router, prefix="/salones", tags=["Salones"])
app.include_router(eventos.router, prefix="/eventos", tags=["Eventos"])
app.include_router(servicios.router, prefix="/servicios", tags=["Servicios"])
app.include_router(asistentes.router, prefix="/asistentes", tags=["Asistentes"])
app.include_router(staff.router, prefix="/staff", tags=["Staff"])
app.include_router(servicios_eventos.router, tags=["Servicios por Evento"])
app.include_router(inscripciones.router, tags=["Inscripciones"])
app.include_router(trazabilidad.router, tags=["Auditoría"])
app.include_router(reportes.router, prefix="/reportes", tags=["Reportes"])

# 4. Ruta de bienvenida (Root)
@app.get("/", tags=["General"])
def read_root():
    return {
        "message": "Bienvenido a NexoEventos API",
        "docs": "/docs",
        "status": "online"
    }