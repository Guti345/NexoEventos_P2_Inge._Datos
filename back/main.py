from fastapi import FastAPI
from app.database import engine, Base
from app.routers import clientes, salones, eventos, servicios, servicios_eventos, asistentes, inscripciones, staff, trazabilidad

# 1. Crear las tablas en la base de datos
# En un entorno real se usa Alembic para migraciones, 
# pero para la clase, esto creará las tablas automáticamente al iniciar.
Base.metadata.create_all(bind=engine)

# 2. Instancia principal de la API
app = FastAPI(
    title="NexoEventos API",
    description="Sistema de gestión para clínica odontológica con arquitectura desacoplada",
    version="1.0.0"
)

# 3. Incluir los Routers (Controladores)
# Esto mantiene el main.py limpio y delega la lógica a cada archivo en /routers
app.include_router(clientes.router, prefix="/clientes", tags=["Clientes"])
app.include_router(salones.router, prefix="/salones", tags=["Salones"])
app.include_router(eventos.router, prefix="/eventos", tags=["Eventos"])
app.include_router(servicios.router, prefix="/servicios", tags=["Servicios"])
app.include_router(servicios_eventos.router, prefix="/servicios_eventos", tags=["ServiciosEventos"])
app.include_router(asistentes.router, prefix="/asistentes", tags=["Asistentes"])
app.include_router(inscripciones.router, prefix="/inscripciones", tags=["Inscripciones"])
app.include_router(staff.router, prefix="/staff", tags=["Staff"])
app.include_router(trazabilidad.router, prefix="/trazabilidad", tags=["Trazabilidad"])

# 4. Ruta de bienvenida (Root)
@app.get("/", tags=["General"])
def read_root():
    return {
        "message": "Bienvenido a NexoEventos API",
        "docs": "/docs",
        "status": "online"
    }