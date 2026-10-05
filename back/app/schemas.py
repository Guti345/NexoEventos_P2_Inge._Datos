from pydantic import BaseModel, Field, EmailStr, model_validator
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Literal

#Defino Categorias Literales presentes en la logica de negocio 
TipoDocumento = Literal["CC", "NIT"]
TamanoSalon = Literal["Pequeño", "Mediano", "Grande"]
TipoEvento = Literal["Congreso", "Conferencia", "Taller", "Feria", "Seminario", "Exposición", "Corporativo", "Social", "Otro"]
EstadoEvento = Literal["Cotizado", "Confirmado", "Finalizado", "Cancelado"]
UnidadCobro = Literal["Hora", "Unidad", "Persona"]
AreaStaff = Literal["Dirección", "Operaciones", "Comercial", "Logística", "Alimentos y Bebidas", "Audiovisuales"]
CargoStaff = Literal["Director", "Gerente", "Jefe", "Coordinador", "Auxiliar", "Técnico"]

#DTO - Rules para Clientes
class ClienteBase(BaseModel):
    tipo_documento: TipoDocumento = Field(..., description="Tipo de documento del cliente (CC o NIT)")
    numero_documento: str = Field(..., min_length=1, max_length=10, pattern=r"^[0-9]+$", description="Número de documento del cliente")
    nombre: str = Field(..., min_length=1, max_length=60, description="Nombre del cliente")
    email: EmailStr = Field(..., description="email electrónico del cliente")
    telefono: str = Field(..., min_length=7, max_length=10, pattern=r"^[0-9]+$", description="Número de teléfono del cliente")

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    tipo_documento: Optional[TipoDocumento] = None
    numero_documento: Optional[str] = Field(None, min_length=1, max_length=10, pattern=r"^[0-9]+$", description="Número de documento del cliente")
    nombre: Optional[str] = Field(None, min_length=1, max_length=60, description="Nombre del cliente")
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, min_length=7, max_length=10, pattern=r"^[0-9]+$", description="Número de teléfono del cliente")

class ClienteResponse(ClienteBase):
    id: int
    fecha_registro: datetime

    class Config:
        from_attributes = True

#DTO - Rules para Salon
class SalonBase(BaseModel):
    nombre_salon: str = Field(..., min_length=1, max_length=40, description="Nombre del salón")
    tamano: TamanoSalon = Field(..., description="Tamaño del salón (Pequeño, Mediano o Grande)")
    capacidad: int = Field(..., gt=0, description="Capacidad del salón")
    precio_hora: Decimal = Field(..., ge=0, max_digits=12, decimal_places=2, description="Precio por hora del salón")

class SalonCreate(SalonBase):
    pass

class SalonUpdate(BaseModel):
    nombre_salon: Optional[str] = Field(None, min_length=1, max_length=40, description="Nombre del salón")
    tamano: Optional[TamanoSalon] = None
    capacidad: Optional[int] = Field(None, gt=0, description="Capacidad del salón")
    precio_hora: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2, description="Precio por hora del salón")
class SalonResponse(SalonBase):
    id: int
    habilitado: bool

    class Config:
        from_attributes = True

#DTO - Rules para Staff
class StaffBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=60, description="Nombre del staff")
    cargo: CargoStaff = Field(..., description="Cargo del staff (Director, Gerente, Jefe, Coordinador, Auxiliar o Técnico)")
    area: AreaStaff = Field(..., description="Área del staff (Dirección, Operaciones, Comercial, Logística, Alimentos y Bebidas, Audiovisuales)")
    email: EmailStr = Field(..., description="email electrónico del staff")
    fecha_ingreso: date = Field(..., description="Fecha de ingreso del staff")
    jefe_id: Optional[int] = Field(None, gt=0, description="ID del jefe del staff (si aplica)")

class StaffCreate(StaffBase):
    @model_validator(mode="after")
    def validar_jefe(self):
        if self.cargo == "Director" and self.jefe_id is not None:
            raise ValueError("El director no puede tener jefe asignado.")
        if self.cargo != "Director" and self.jefe_id is None:
            raise ValueError("El miembro del Staff debe tener un jefe asignado.")
        return self

class StaffUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=60, description="Nombre del staff")
    cargo: Optional[CargoStaff] = None
    area: Optional[AreaStaff] = None
    email: Optional[EmailStr] = None
    fecha_ingreso: Optional[date] = None
    jefe_id: Optional[int] = Field(None, gt=0, description="ID del jefe del staff (si aplica)")

class StaffResponse(StaffBase):
    id: int

    class Config:
        from_attributes = True

#DTO - Rules para Eventos
class EventoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del evento")
    tipo: TipoEvento = Field(..., description="Tipo de evento (Congreso, Conferencia, Taller, Feria, Seminario, Exposición, Corporativo, Social u Otro)")
    inicio: datetime = Field(..., description="Fecha y hora de inicio del evento")
    fin: datetime = Field(..., description="Fecha y hora de fin del evento")
    aforo_esperado: int = Field(..., gt=0, description="Aforo esperado del evento")
    salon_id: int = Field(..., gt=0, description="ID del salón donde se realizará el evento")
    cliente_id: int = Field(..., gt=0, description="ID del cliente que organiza el evento")
    coordinador_id: int = Field(..., gt=0, description="ID del staff que coordina el evento")
    @model_validator(mode="after")
    def validar_fechas(self):
        if self.inicio >= self.fin:
            raise ValueError("La fecha y hora de fin debe ser posterior al inicio.")
        return self

class EventoCreate(EventoBase):
    pass

class EventoUpdate(BaseModel):
    inicio: Optional[datetime] = None
    fin: Optional[datetime] = None
    aforo_esperado: Optional[int] = Field(None, gt=0, description="Aforo esperado del evento")
    salon_id: Optional[int] = Field(None, gt=0, description="ID del salón donde se realizará el evento")
    @model_validator(mode="after")
    def validar_fechas(self):
        if self.inicio is not None and self.fin is not None and self.inicio >= self.fin:
            raise ValueError("La fecha y hora de fin debe ser posterior al inicio.")
        return self

class EventoResponse(EventoBase):
    id: int
    estado: EstadoEvento
    precio_hora_salon_cotizado: Decimal
    valor_total_cotizado: Decimal
    tasa_asistencia: Optional[Decimal] = None

    class Config:
        from_attributes = True

#DTO - Rules para EventosEstado
class EventoEstadoUpdate(BaseModel):
    estado: EstadoEvento = Field(..., description="Nuevo estado del evento (Cotizado, Confirmado, Finalizado o Cancelado)")

#DTO - Rules para Servicios
class ServicioBase(BaseModel):
    nombre_servicio: str = Field(..., min_length=1, max_length=30, description="Nombre del servicio")
    descripcion: str = Field(..., min_length=1, max_length=200, description="Descripción del servicio")
    unidad_cobro: UnidadCobro = Field(..., description="Unidad de cobro del servicio (Hora, Unidad o Persona)")
    precio: Decimal = Field(..., ge=0, max_digits=12, decimal_places=2, description="Precio del servicio")

class ServicioCreate(ServicioBase):
    pass

class ServicioUpdate(BaseModel):
    nombre_servicio: Optional[str] = Field(None, min_length=1, max_length=30, description="Nombre del servicio")
    descripcion: Optional[str] = Field(None, min_length=1, max_length=200, description="Descripción del servicio")
    unidad_cobro: Optional[UnidadCobro] = None
    precio: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2, description="Precio del servicio")

class ServicioResponse(ServicioBase):
    id: int

    class Config:
        from_attributes = True

#DTO - Rules para ServicioEvento
class ServicioEventoBase(BaseModel):
    servicio_id: int = Field(..., gt=0, description="ID del servicio")
    cantidad: Optional[int] = Field(None, gt=0, description="Cantidad del servicio")

class ServicioEventoCreate(ServicioEventoBase):
    pass

class ServicioEventoUpdate(BaseModel):
    servicio_id: Optional[int] = Field(None, gt=0, description="ID del servicio")
    cantidad: Optional[int] = Field(None, gt=0, description="Cantidad del servicio")

class ServicioEventoDelete(BaseModel):
    servicio_id: int = Field(..., gt=0, description="ID del servicio a eliminar del evento")

class ServicioEventoResponse(ServicioEventoBase):
    id: int
    evento_id: int
    servicio_id: int
    precio_unidad_cotizado: Decimal
    cantidad: int

    class Config:
        from_attributes = True

#DTO - Rules para Asistentes
class AsistenteBase(BaseModel):
    documento_identidad: str = Field(..., min_length=1, max_length=10, pattern=r"^[0-9]+$", description="Número de documento del asistente")
    nombre: str = Field(..., min_length=2, max_length=60, description="Nombre del asistente")
    email: EmailStr = Field(..., description="email electrónico del asistente")
    empresa: str = Field(..., min_length=1, max_length=100, description="Empresa del asistente")


class AsistenteCreate(AsistenteBase):
    pass

class AsistenteUpdate(BaseModel):
    documento_identidad: Optional[str] = Field(None, min_length=1, max_length=10, pattern=r"^[0-9]+$", description="Número de documento del asistente")
    nombre: Optional[str] = Field(None, min_length=2, max_length=60, description="Nombre del asistente")
    email: Optional[EmailStr] = None
    empresa: Optional[str] = Field(None, min_length=1, max_length=100, description="Empresa del asistente")

class AsistenteResponse(AsistenteBase):
    id: int

    class Config:
        from_attributes = True

#DTO - Rules para Inscripciones
class InscripcionBase(BaseModel):
    asistente_id: int = Field(..., gt=0, description="ID del asistente")

class InscripcionCreate(InscripcionBase):
    pass

class InscripcionResponse(InscripcionBase):
    id: int
    asistente_id: int
    evento_id: int
    fecha_checkin: Optional[datetime] = None

    class Config:
        from_attributes = True

#DTO - Rules para Trazabilidadidad
class TrazabilidadBase(BaseModel):
    evento_id: int = Field(..., gt=0, description="ID del evento")
    campo_modificado: str = Field(..., description="Campo modificado")
    valor_anterior: str = Field(..., description="Valor anterior del campo modificado")
    valor_nuevo: str = Field(..., description="Valor nuevo del campo modificado")
    fecha_hora: datetime = Field(..., description="Fecha y hora de la acción")
    usuario: str = Field(..., description="Usuario que realizó la acción")

class TrazabilidadResponse(TrazabilidadBase):
    id: int

    class Config:
        from_attributes = True

##DTOs - Diferentes de las tablas generadas

#DTO - Rules para Checkin
class CheckinBase(BaseModel):
    documento_identidad: str = Field(..., min_length=1, max_length=10, pattern=r"^[0-9]+$", description="Número de documento del asistente")

class CheckinCreate(CheckinBase):
    pass

#DTO - Rules para Cotización
class CotizacionServicioResponse(BaseModel):
    nombre_servicio: str
    unidad_cobro: UnidadCobro
    precio_unidad_cotizado: Decimal
    cantidad: int
    valor_total_cotizado: Decimal

class CotizacionResponse(BaseModel):
    evento_id: int
    hora_salon: int
    precio_hora_salon: Decimal
    valor_total_salon: Decimal
    servicios: list[CotizacionServicioResponse]
    total_servicios: Decimal
    valor_total_cotizado: Decimal

#DTO - Rules para Asistencia
class AsistenciaResumenResponse(BaseModel):
    inscritos: int
    asistentes_reales: int
    tasa_asistencia: Optional[Decimal] = None

class EventoDetalleResponse(BaseModel):
    servicios: list[ServicioEventoResponse] = Field(default_factory=list)
    asistencia: AsistenciaResumenResponse

#DTO - Rules para Salon Disponible
class SalonDisponibleResponse(BaseModel):
    salon_id: int
    nombre_salon: str
    tamano: TamanoSalon
    capacidad: int
    precio_hora: Decimal
    costo_estimado: Decimal

#DTOs - Reportes
#DTO - B1 Organigrama
class OrganigramaResponse(BaseModel):
    staff_id: int
    nombre: str
    cargo: str
    area: str
    jefe_id: Optional[int] = None
    nivel: int
    ruta_mando: str
    personas_a_cargo: int

#DTO - B2 Cadena de escalamiento
class EscalamientoResponse(BaseModel):
    orden: int
    staff_id: int
    nombre: str
    cargo: str
    area: str
    email: EmailStr

#DTO - B3 Pareto clientes
class ParetoClienteResponse(BaseModel):
    cliente_id: int
    cliente: str
    eventos: int
    total_facturado: Decimal
    posicion: int
    participacion: Decimal
    acumulado: Decimal
    segmento_pareto: str

#DTO - B4 Ocupación de salones
class OcupacionSalonResponse(BaseModel):
    salon_id: int
    salon: str
    evento_id: int
    evento: str
    inicio: datetime
    fin: datetime
    numero_en_salon: int
    evento_anterior: Optional[str] = None
    dias_libres: Optional[Decimal] = None
    horas_acumuladas: Decimal