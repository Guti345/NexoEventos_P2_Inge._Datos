import os
from datetime import datetime
from decimal import Decimal

import requests
import streamlit as st

URL_BASE = os.getenv("NEXO_API_URL", "http://localhost:8000")


class ApiError(Exception):
    def __init__(self, status, mensaje):
        super().__init__(mensaje)
        self.status = status
        self.mensaje = mensaje

def _mensaje_de_error(respuesta):
    if respuesta.status_code >= 500:
        return "Error interno del servidor."
    try:
        detalle = respuesta.json().get("detail")
    except ValueError:
        return f"Error {respuesta.status_code}"
    if isinstance(detalle, list):
        return "\n".join(f"- **{err['loc'][-1]}**: {err['msg']}" for err in detalle)
    if "duplicate key" in str(detalle):
        return "Ya existe un registro con ese documento."
    return str(detalle)

def _peticion(metodo, ruta, **kwargs):
    headers = {"X-Usuario": st.session_state.get("usuario", "streamlit")}
    try:
        respuesta = requests.request(metodo, f"{URL_BASE}{ruta}", headers=headers, timeout=15, **kwargs)
    except requests.exceptions.RequestException:
        raise ApiError(0, f"No se pudo conectar con la API en {URL_BASE}. Verifique que esté corriendo.")
    if respuesta.status_code >= 400:
        raise ApiError(respuesta.status_code, _mensaje_de_error(respuesta))
    return respuesta.json() if respuesta.content else None

# Salones y servicios
def get_salones():
    return _peticion("GET", "/salones/")

def get_salones_disponibles(inicio, fin, aforo):
    params = {"fecha_inicio": inicio.isoformat(), "fecha_fin": fin.isoformat(), "aforo": aforo}
    return _peticion("GET", "/salones/disponibles", params=params)

def get_servicios():
    return _peticion("GET", "/servicios/")

# Clientes
def get_clientes(buscar=None):
    return _peticion("GET", "/clientes/", params={"buscar": buscar} if buscar else {})

def get_eventos_cliente(cliente_id):
    return _peticion("GET", f"/clientes/{cliente_id}/eventos")

def crear_cliente(payload):
    return _peticion("POST", "/clientes/", json=payload)

# Staff
def get_staff():
    return _peticion("GET", "/staff/")

def crear_staff(payload):
    return _peticion("POST", "/staff/", json=payload)

# Eventos
def get_eventos(estado=None):
    return _peticion("GET", "/eventos/", params={"estado": estado} if estado else {})

def get_evento(evento_id):
    return _peticion("GET", f"/eventos/{evento_id}")

def crear_evento(payload):
    return _peticion("POST", "/eventos/", json=payload)

def reprogramar_evento(evento_id, payload):
    return _peticion("PATCH", f"/eventos/{evento_id}", json=payload)

def cambiar_estado(evento_id, estado):
    return _peticion("PATCH", f"/eventos/{evento_id}/estado", json={"estado": estado})

def get_cotizacion(evento_id):
    return _peticion("GET", f"/eventos/{evento_id}/cotizacion")

def get_auditoria(evento_id):
    return _peticion("GET", f"/eventos/{evento_id}/auditoria")

def agregar_servicio(evento_id, servicio_id, cantidad):
    return _peticion("POST", f"/eventos/{evento_id}/servicios", json={"servicio_id": servicio_id, "cantidad": cantidad})

def modificar_servicio(evento_id, servicio_id, cantidad):
    return _peticion("PUT", f"/eventos/{evento_id}/servicios", json={"servicio_id": servicio_id, "cantidad": cantidad})

def quitar_servicio(evento_id, servicio_id):
    return _peticion("DELETE", f"/eventos/{evento_id}/servicios", json={"servicio_id": servicio_id})

# Asistentes, inscripciones y check-in
def get_asistentes():
    return _peticion("GET", "/asistentes/")

def crear_asistente(payload):
    return _peticion("POST", "/asistentes/", json=payload)

def get_inscripciones(evento_id):
    return _peticion("GET", f"/eventos/{evento_id}/inscripciones")

def inscribir(evento_id, asistente_id):
    return _peticion("POST", f"/eventos/{evento_id}/inscripciones", json={"asistente_id": asistente_id})

def checkin(evento_id, documento):
    return _peticion("POST", f"/eventos/{evento_id}/checkin", json={"documento_identidad": documento})

# Reportes
def reporte_organigrama(staff_id=None):
    return _peticion("GET", "/reportes/organigrama", params={"staff_id": staff_id} if staff_id else {})

def reporte_escalamiento(staff_id):
    return _peticion("GET", f"/reportes/escalamiento/{staff_id}")

def reporte_pareto():
    return _peticion("GET", "/reportes/pareto-clientes")

def reporte_ocupacion():
    return _peticion("GET", "/reportes/ocupacion-salones")

# Listas para los formularios
ESTADOS = ["Cotizado", "Confirmado", "Finalizado", "Cancelado"]
TIPOS_EVENTO = ["Congreso", "Conferencia", "Taller", "Feria", "Seminario", "Exposición", "Corporativo", "Social", "Otro"]
AREAS = ["Dirección", "Operaciones", "Comercial", "Logística", "Alimentos y Bebidas", "Audiovisuales"]
CARGOS = ["Director", "Gerente", "Jefe", "Coordinador", "Auxiliar", "Técnico"]

REGLAS = {
    "SALON INACTIVO": "A1", "CAPACIDAD": "A1", "DISPONIBILIDAD": "A1",
    "CUPO": "A2", "INSCRIPCION": "A2", "CHECK-IN": "A2",
    "SERVICIOS": "A3",
    "ESTADO": "A4", "CIERRE": "A4",
}

# Pantalla y mensajes
def _guardar_usuario():
    st.session_state["usuario"] = st.session_state["campo_usuario"] or "recepcion"

def configurar_pagina(titulo):
    st.set_page_config(page_title="NexoEventos", layout="wide")
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = "recepcion"
    st.sidebar.text_input("Usuario de la aplicación", value=st.session_state["usuario"],
                          key="campo_usuario", on_change=_guardar_usuario)
    st.header(titulo)
    mensaje = st.session_state.pop("mensaje_exito", None)
    if mensaje:
        st.success(mensaje)

def exito(mensaje):
    st.session_state["mensaje_exito"] = mensaje
    st.rerun()

def mostrar_error(e):
    if e.status == 0:
        st.error(f"API no disponible. {e.mensaje}")
    elif e.status == 409:
        prefijo, _, resto = e.mensaje.partition(":")
        regla = REGLAS.get(prefijo.strip())
        if regla:
            st.error(f"Operación bloqueada por la regla {regla}: {resto.strip()}")
        else:
            st.error(f"Operación rechazada por la base de datos: {e.mensaje}")
    elif e.status == 422:
        st.warning(f"Datos inválidos:\n\n{e.mensaje}")
    else:
        st.warning(f"Error {e.status}: {e.mensaje}")

def mostrar_validacion(e):
    errores = "\n".join(f"- **{err['loc'][-1] if err['loc'] else 'datos'}**: {err['msg'].replace('Value error, ', '')}"
                        for err in e.errors())
    st.warning(f"Datos inválidos:\n\n{errores}")

def cargar(funcion, *args):
    try:
        return funcion(*args)
    except ApiError as e:
        mostrar_error(e)
        if e.status == 0:
            st.stop()
        return []

# Formatos
def dinero(valor):
    if valor is None:
        return "-"
    return "$ " + f"{Decimal(str(valor)):,.0f}".replace(",", ".")

def fecha_hora(valor):
    if not valor:
        return "-"
    return datetime.fromisoformat(str(valor)).strftime("%d/%m/%Y %H:%M")
