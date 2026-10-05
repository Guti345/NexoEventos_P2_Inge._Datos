from sqlalchemy import Column, Integer, Numeric, String, Date, DateTime, Float, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import relationship
from .database import Base

class ClientesEntity(Base):
    __tablename__ = "clientes"
    __table_args__ = (
        CheckConstraint("tipo_documento IN ('CC', 'NIT')", name='check_tipo_documento'),
        CheckConstraint("email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'", name='check_email_valido'),
        CheckConstraint("LENGTH(telefono) <= 10 AND telefono ~ '^[0-9]+$'", name='check_telefono_valido'),
        CheckConstraint("LENGTH(numero_documento) <= 10 AND numero_documento ~ '^[0-9]+$'", name='check_numero_documento_positivo'),
    )
    id = Column(Integer, primary_key=True, index=True)
    tipo_documento = Column(String(3), nullable=False)
    numero_documento = Column(String(10), nullable=False, unique=True)
    nombre = Column(String(60), nullable=False)
    email = Column(String(100), nullable=False)
    telefono = Column(String(10), nullable=False)
    fecha_registro = Column(DateTime, nullable=False, default=func.now())
    eventos = relationship("EventosEntity", back_populates="cliente")

class SalonesEntity(Base):
    __tablename__ = "salones"
    __table_args__ = (
        CheckConstraint("tamano IN ('Pequeño', 'Mediano', 'Grande')", name='check_tamaño_valido'),
        CheckConstraint("capacidad > 0", name='check_capacidad_positiva'),
        CheckConstraint("precio_hora >= 0", name='check_precio_hora_no_negativo'),
    )
    id = Column(Integer, primary_key=True, index=True)
    nombre_salon = Column(String(40), nullable=False)
    tamano = Column(String(15), nullable=False)
    capacidad = Column(Integer, nullable=False)
    habilitado = Column(Boolean, nullable=False, default=True)
    precio_hora = Column(Numeric(12, 2), nullable=False)
    eventos = relationship("EventosEntity", back_populates="salon")

class EventosEntity(Base):
    __tablename__ = "eventos"
    __table_args__ = (
        CheckConstraint("inicio < fin", name='check_inicio_menor_fin'),
        CheckConstraint("aforo_esperado > 0", name='check_aforo_esperado_positivo'),
        CheckConstraint("estado IN ('Cotizado', 'Confirmado', 'Finalizado', 'Cancelado')", name='check_estado_evento_valido'),
        CheckConstraint("tipo IN ('Congreso', 'Conferencia', 'Taller', 'Feria', 'Seminario', 'Exposición', 'Corporativo', 'Social', 'Otro')", name='check_tipo_evento_valido'),
        CheckConstraint("precio_hora_salon_cotizado >= 0", name='check_precio_no_negativo'),
        CheckConstraint("valor_total_cotizado >= 0", name='check_valor_total_no_negativo'),
        CheckConstraint("tasa_asistencia >= 0 AND tasa_asistencia <= 100", name='check_tasa_asistencia_valida'),
    )
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    inicio = Column(DateTime, nullable=False)
    fin = Column(DateTime, nullable=False)
    tipo = Column(String(30), nullable=False)
    aforo_esperado = Column(Integer, nullable=False)
    coordinador_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    estado = Column(String(20), nullable=False, default="Cotizado")
    salon_id = Column(Integer, ForeignKey("salones.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    cliente = relationship("ClientesEntity", back_populates="eventos")
    salon = relationship("SalonesEntity", back_populates="eventos")
    coordinador = relationship("StaffEntity", back_populates="eventos")
    precio_hora_salon_cotizado = Column(Numeric(12, 2), nullable=False)
    tasa_asistencia = Column(Numeric(5, 2), nullable=True)
    valor_total_cotizado = Column(Numeric(12, 2), nullable=False)
    inscripciones = relationship("InscripcionesEntity", back_populates="evento")
    trazabilidad = relationship("TrazabilidadEntity", back_populates="evento")
    servicios_eventos = relationship("ServiciosEventosEntity", back_populates="evento")

class ServiciosEntity(Base):
    __tablename__ = "servicios"
    __table_args__ = (
        CheckConstraint("precio >= 0", name='check_precio_no_negativo'),
        CheckConstraint("unidad_cobro IN ('Hora', 'Unidad', 'Persona')", name='check_unidad_cobro_valida'),
    )
    id = Column(Integer, primary_key=True, index=True)
    nombre_servicio = Column(String(100), nullable=False)
    descripcion = Column(String(200), nullable=False)
    unidad_cobro = Column(String(20), nullable=False)
    precio = Column(Numeric(12, 2), nullable=False)
    servicios_eventos = relationship("ServiciosEventosEntity", back_populates="servicio")

class ServiciosEventosEntity(Base):
    __table_args__ = (
            CheckConstraint("precio_unidad_cotizado >= 0", name='check_precio_no_negativo'),
            CheckConstraint("cantidad > 0", name='check_cantidad_positiva'),
            UniqueConstraint("evento_id", "servicio_id", name="unique_evento_servicio"),
        )
    __tablename__ = "servicios_eventos"
    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False)
    servicio_id = Column(Integer, ForeignKey("servicios.id"), nullable=False)
    evento = relationship("EventosEntity", back_populates="servicios_eventos")
    servicio = relationship("ServiciosEntity", back_populates="servicios_eventos")
    cantidad = Column(Integer, nullable=False)
    precio_unidad_cotizado = Column(Numeric(12, 2), nullable=False)
    cantidad_manual = Column(Boolean, nullable=False, default=False)

class AsistentesEntity(Base):
    __tablename__ = "asistentes"
    __table_args__ = (
        CheckConstraint("LENGTH(documento_identidad) <= 10 AND documento_identidad ~ '^[0-9]+$'", name='check_documento_identidad_positivo'),
        CheckConstraint("email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'", name='check_email_valido'),
    )
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(60), nullable=False)
    documento_identidad = Column(String(10), nullable=False, unique=True)
    email = Column(String(100), nullable=False)
    empresa = Column(String(100), nullable=False)
    inscripciones = relationship("InscripcionesEntity", back_populates="asistente")

class InscripcionesEntity(Base):
    __tablename__ = "inscripciones"
    __table_args__ = (
        CheckConstraint("fecha_checkin <= NOW()", name='check_fecha_checkin_no_futura'),
        UniqueConstraint("asistente_id", "evento_id", name="unique_asistente_evento"),
    )
    id = Column(Integer, primary_key=True, index=True)
    fecha_checkin = Column(DateTime, nullable=True)
    asistente_id = Column(Integer, ForeignKey("asistentes.id"), nullable=False)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False)
    asistente = relationship("AsistentesEntity", back_populates="inscripciones")
    evento = relationship("EventosEntity", back_populates="inscripciones")

class StaffEntity(Base):
    __tablename__ = "staff"
    __table_args__ = (
        CheckConstraint("email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'", name='check_email_valido'),
        CheckConstraint("area IN ('Dirección', 'Operaciones', 'Comercial', 'Logística', 'Alimentos y Bebidas', 'Audiovisuales')", name='check_area_valida'),
        CheckConstraint("cargo IN ('Director', 'Gerente', 'Jefe', 'Coordinador', 'Auxiliar', 'Técnico')", name='check_cargo_valido'),
        CheckConstraint("jefe_id IS NULL OR jefe_id <> id", name='check_jefe_no_autoreferencia'),
        CheckConstraint("(cargo='Director' AND jefe_id IS NULL) OR (cargo<>'Director' AND jefe_id IS NOT NULL)", name='check_jefe_segun_cargo'),
    )
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(60), nullable=False)
    email = Column(String(100), nullable=False)
    area = Column(String(20), nullable=False)
    cargo = Column(String(20), nullable=False)
    fecha_ingreso = Column(Date, nullable=False)
    jefe_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    jefe = relationship("StaffEntity", remote_side=[id], back_populates="subordinados")
    subordinados = relationship("StaffEntity", back_populates="jefe")
    eventos = relationship("EventosEntity", back_populates="coordinador")

class TrazabilidadEntity(Base):
    __tablename__ = "trazabilidad"
    __table_args__ = (
        CheckConstraint("campo_modificado IN ('estado', 'salon_id', 'inicio', 'fin')", name='check_campo_auditado'),
    )
    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False)
    campo_modificado = Column(String(20), nullable=False)
    valor_anterior = Column(String(100), nullable=False)
    valor_nuevo = Column(String(100), nullable=False)
    fecha_hora = Column(DateTime, nullable=False)
    usuario = Column(String(60), nullable=False)
    evento = relationship("EventosEntity", back_populates="trazabilidad")