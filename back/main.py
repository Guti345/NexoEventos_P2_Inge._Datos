from fastapi import FastAPI
from app.database import engine, Base
from app.routers import pacientes, tratamientos

# 1. Crear las tablas en la base de datos
# En un entorno real se usa Alembic para migraciones, 
# pero para la clase, esto creará las tablas automáticamente al iniciar.
Base.metadata.create_all(bind=engine)

# 2. Instancia principal de la API
app = FastAPI(
    title="OrthoConnect API",
    description="Sistema de gestión para clínica odontológica con arquitectura desacoplada",
    version="1.0.0"
)

# 3. Incluir los Routers (Controladores)
# Esto mantiene el main.py limpio y delega la lógica a cada archivo en /routers
app.include_router(pacientes.router, prefix="/pacientes", tags=["Pacientes"])
app.include_router(tratamientos.router, prefix="/tratamientos", tags=["Tratamientos"])

# 4. Ruta de bienvenida (Root)
@app.get("/", tags=["General"])
def read_root():
    return {
        "message": "Bienvenido a OrthoConnect API",
        "docs": "/docs",
        "status": "online"
    }