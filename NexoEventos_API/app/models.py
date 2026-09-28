from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class PacienteEntity(Base):
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
    paciente = relationship("PacienteEntity", back_populates="tratamientos")
