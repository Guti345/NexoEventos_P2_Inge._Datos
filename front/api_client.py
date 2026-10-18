
import os
import re

import requests
import streamlit as st

API_URL = os.getenv("NEXO_API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 15


class ApiError(Exception):
    def __init__(self, status: int, mensaje: str):
        super().__init__(mensaje)
        self.status = status
        self.mensaje = mensaje


# ---------------------------------------------------------------------------
# Errores
# ---------------------------------------------------------------------------
def _traducir_postgres(mensaje: str) -> str:
    dup = re.search(r"Key \((.+?)\)=\((.+?)\) already exists", mensaje)
    if "duplicate key" in mensaje:
        if dup:
            return f"Ya existe un registro con {dup.group(1).replace('_', ' ')} = {dup.group(2)}."
        return "Ya existe un registro con esos datos (valor único repetido)."
    if "foreign key" in mensaje:
        return "El registro relacionado no existe o todavía tiene datos que dependen de él."
    return mensaje


def _extraer_mensaje(respuesta: requests.Response) -> str:
    try:
        cuerpo = respuesta.json()
    except ValueError:
        return f"Error {respuesta.status_code} del servidor."

    detalle = cuerpo.get("detail", cuerpo) if isinstance(cuerpo, dict) else cuerpo

    if isinstance(detalle, list):
        partes = []
        for err in detalle:
            campo = " → ".join(str(x) for x in err.get("loc", []) if x not in ("body", "query", "path"))
            msg = str(err.get("msg", "")).replace("Value error, ", "")
            partes.append(f"**{campo}**: {msg}" if campo else msg)
        return "\n".join(f"- {p}" for p in partes)

    return _traducir_postgres(str(detalle))


def _request(metodo: str, ruta: str, **kwargs):
    headers = {"X-Usuario": st.session_state.get("usuario") or "streamlit"}
    try:
        respuesta = requests.request(metodo, f"{API_URL}{ruta}", headers=headers, timeout=TIMEOUT, **kwargs)
    except requests.exceptions.ConnectionError:
        raise ApiError(0, f"No se pudo conectar con la API en {API_URL}. "
                          "Verifique que esté corriendo (`uvicorn main:app --reload` dentro de back/).")
    except requests.exceptions.Timeout:
        raise ApiError(0, "La API tardó demasiado en responder. Intente de nuevo.")

    if respuesta.status_code >= 400:
        if respuesta.status_code >= 500:
            raise ApiError(respuesta.status_code, "Error interno del servidor. Revise la consola de la API.")
        raise ApiError(respuesta.status_code, _extraer_mensaje(respuesta))

    if respuesta.status_code == 204 or not respuesta.content:
        return None
    return respuesta.json()


def api_disponible() -> bool:
    try:
        return requests.get(f"{API_URL}/", timeout=3).ok
    except requests.exceptions.RequestException:
        return False


def limpiar_cache():
    st.cache_data.clear()


# ---------------------------------------------------------------------------
# Salones y servicios
# ---------------------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def get_salones():
    return _request("GET", "/salones/")


@st.cache_data(ttl=30, show_spinner=False)
def get_servicios():
    return _request("GET", "/servicios/")


def get_salones_disponibles(inicio, fin, aforo: int):
    params = {"fecha_inicio": inicio.isoformat(), "fecha_fin": fin.isoformat(), "aforo": aforo}
    return _request("GET", "/salones/disponibles", params=params)


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def get_clientes(buscar: str | None = None, tipo_documento: str | None = None):
    params = {k: v for k, v in {"buscar": buscar, "tipo_documento": tipo_documento}.items() if v}
    return _request("GET", "/clientes/", params=params)


def get_eventos_cliente(cliente_id: int):
    return _request("GET", f"/clientes/{cliente_id}/eventos")


def crear_cliente(payload: dict):
    return _request("POST", "/clientes/", json=payload)


# ---------------------------------------------------------------------------
# Staff
# ---------------------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def get_staff():
    return _request("GET", "/staff/")


def crear_staff(payload: dict):
    return _request("POST", "/staff/", json=payload)


# ---------------------------------------------------------------------------
# Eventos
# ---------------------------------------------------------------------------
@st.cache_data(ttl=15, show_spinner=False)
def get_eventos(estado: str | None = None, cliente_id: int | None = None, salon_id: int | None = None):
    params = {k: v for k, v in {"estado": estado, "cliente_id": cliente_id, "salon_id": salon_id}.items() if v}
    return _request("GET", "/eventos/", params=params)


def get_evento(evento_id: int):
    return _request("GET", f"/eventos/{evento_id}")


def crear_evento(payload: dict):
    return _request("POST", "/eventos/", json=payload)


def reprogramar_evento(evento_id: int, payload: dict):
    return _request("PATCH", f"/eventos/{evento_id}", json=payload)


def cambiar_estado_evento(evento_id: int, estado: str):
    return _request("PATCH", f"/eventos/{evento_id}/estado", json={"estado": estado})


def get_cotizacion(evento_id: int):
    return _request("GET", f"/eventos/{evento_id}/cotizacion")


def get_auditoria(evento_id: int):
    return _request("GET", f"/eventos/{evento_id}/auditoria")


def agregar_servicio_evento(evento_id: int, servicio_id: int, cantidad: int | None):
    return _request("POST", f"/eventos/{evento_id}/servicios", json={"servicio_id": servicio_id, "cantidad": cantidad})


def actualizar_servicio_evento(evento_id: int, servicio_id: int, cantidad: int):
    return _request("PUT", f"/eventos/{evento_id}/servicios", json={"servicio_id": servicio_id, "cantidad": cantidad})


def quitar_servicio_evento(evento_id: int, servicio_id: int):
    return _request("DELETE", f"/eventos/{evento_id}/servicios", json={"servicio_id": servicio_id})


# ---------------------------------------------------------------------------
# Asistentes, inscripciones y check-in
# ---------------------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def get_asistentes():
    return _request("GET", "/asistentes/")


def crear_asistente(payload: dict):
    return _request("POST", "/asistentes/", json=payload)


def get_inscripciones(evento_id: int):
    return _request("GET", f"/eventos/{evento_id}/inscripciones")


def inscribir(evento_id: int, asistente_id: int):
    return _request("POST", f"/eventos/{evento_id}/inscripciones", json={"asistente_id": asistente_id})


def checkin(evento_id: int, documento: str):
    return _request("POST", f"/eventos/{evento_id}/checkin", json={"documento_identidad": documento})


# ---------------------------------------------------------------------------
# Reportes
# ---------------------------------------------------------------------------
def reporte_organigrama(staff_id: int | None = None):
    return _request("GET", "/reportes/organigrama", params={"staff_id": staff_id} if staff_id else {})


def reporte_escalamiento(staff_id: int):
    return _request("GET", f"/reportes/escalamiento/{staff_id}")


def reporte_pareto():
    return _request("GET", "/reportes/pareto-clientes")


def reporte_ocupacion(salon_id: int | None = None):
    return _request("GET", "/reportes/ocupacion-salones", params={"salon_id": salon_id} if salon_id else {})
