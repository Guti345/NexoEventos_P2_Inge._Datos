from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


'''class PacienteEntity(Base):
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    contacto = Column(String, nullable=False)
    referido_por_id = Column(Integer, ForeignKey("pacientes.id"), nullable=True)
    tratamientos = relationship("TratamientoEntity", back_populates="paciente")


class TratamientoEntity(Base):
    __tablename__ = "tratamientos"
    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    medico_id = Column(Integer, ForeignKey("personal_medico.id"))
    diagnostico = Column(String, nullable=False)
    sesiones_estimadas = Column(Integer, nullable=False)
    estado = Column(String, default="Activo")
    eficacia_calculada = Column(Float, nullable=True)
    paciente = relationship("PacienteEntity", back_populates="tratamientos")'''


class Clientes(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, nullable=False)
    telefono = Column(String, nullable=False)

class Salones(Base):
    __tablename__ = "salones"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    ubicacion = Column(String, nullable=False)
    capacidad = Column(Integer, nullable=False)

class Eventos(Base):
    __tablename__ = "eventos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)
    salon_id = Column(Integer, ForeignKey("salones.id"))
    salon = relationship("Salones", backref="eventos")

class Servicios(Base):
    __tablename__ = "servicios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    precio = Column(Float, nullable=False)

class ServiciosEventos(Base):
    __tablename__ = "servicios_eventos"
    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey("eventos.id"))
    servicio_id = Column(Integer, ForeignKey("servicios.id"))
    evento = relationship("Eventos", backref="servicios_eventos")
    servicio = relationship("Servicios", backref="servicios_eventos")

class Asistentes(Base):
    __tablename__ = "asistentes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, nullable=False)
    telefono = Column(String, nullable=False)
    evento_id = Column(Integer, ForeignKey("eventos.id"))
    evento = relationship("Eventos", backref="asistentes")

class Staff(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    correo = Column(String, nullable=False)
    telefono = Column(String, nullable=False)
    evento_id = Column(Integer, ForeignKey("eventos.id"))
    evento = relationship("Eventos", backref="staff")

class Auditoria(Base):
    __tablename__ = "auditoria"
    id = Column(Integer, primary_key=True, index=True)
    evento_id = Column(Integer, ForeignKey("eventos.id"))
    accion = Column(String, nullable=False)
    fecha_hora = Column(Date, nullable=False)
    usuario = Column(String, nullable=False)
    evento = relationship("Eventos", backref="auditoria")