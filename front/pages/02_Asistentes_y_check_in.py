import os
import sys

import pandas as pd
import streamlit as st
from pydantic import ValidationError

import api_client
from api_client import ApiError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from back.app import schemas

api_client.configurar_pagina("Asistentes y check-in")

eventos = sorted(api_client.cargar(api_client.get_eventos), key=lambda e: e["inicio"], reverse=True)
opciones_evento = {e["id"]: f"{e['id']} - {e['nombre']} ({e['estado']})" for e in eventos}
asistentes = {a["id"]: a for a in api_client.cargar(api_client.get_asistentes)}

tab_checkin, tab_inscritos, tab_inscribir, tab_registrar = st.tabs(
    ["Check-in", "Inscritos y llegadas", "Inscribir", "Registrar asistente"]
)

# Check-in en puerta
with tab_checkin:
    evento_id = st.selectbox("Evento", list(opciones_evento), format_func=opciones_evento.get, key="evento_checkin")
    with st.form("checkin", clear_on_submit=True):
        documento = st.text_input("Documento del asistente")
        if st.form_submit_button("Registrar llegada"):
            try:
                inscripcion = api_client.checkin(evento_id, documento.strip())
                nombre = asistentes.get(inscripcion["asistente_id"], {}).get("nombre", documento)
                api_client.exito(f"Llegada de {nombre} registrada a las {api_client.fecha_hora(inscripcion['fecha_checkin'])}.")
            except ApiError as e:
                api_client.mostrar_error(e)

# Inscritos y quiénes llegaron
with tab_inscritos:
    evento_id = st.selectbox("Evento", list(opciones_evento), format_func=opciones_evento.get, key="evento_inscritos")
    inscripciones = api_client.cargar(api_client.get_inscripciones, evento_id)
    llegaron = sum(1 for i in inscripciones if i["fecha_checkin"])
    c1, c2 = st.columns(2)
    c1.metric("Inscritos", len(inscripciones))
    c2.metric("Llegaron", llegaron)
    if inscripciones:
        st.dataframe(pd.DataFrame([{
            "Documento": asistentes.get(i["asistente_id"], {}).get("documento_identidad"),
            "Nombre": asistentes.get(i["asistente_id"], {}).get("nombre"),
            "Empresa": asistentes.get(i["asistente_id"], {}).get("empresa"),
            "Llegó": "Sí" if i["fecha_checkin"] else "No",
            "Hora de llegada": api_client.fecha_hora(i["fecha_checkin"]),
        } for i in inscripciones]), hide_index=True)

# Inscribir a un evento
with tab_inscribir:
    evento_id = st.selectbox("Evento", list(opciones_evento), format_func=opciones_evento.get, key="evento_inscribir")
    asistente_id = st.selectbox("Asistente", list(asistentes),
                                format_func=lambda i: f"{asistentes[i]['nombre']} - {asistentes[i]['documento_identidad']}")
    if st.button("Inscribir"):
        try:
            api_client.inscribir(evento_id, asistente_id)
            api_client.exito(f"{asistentes[asistente_id]['nombre']} quedó inscrito(a).")
        except ApiError as e:
            api_client.mostrar_error(e)

# Registrar asistente
with tab_registrar:
    with st.form("registrar_asistente", clear_on_submit=True):
        documento = st.text_input("Documento de identidad")
        nombre = st.text_input("Nombre completo")
        email = st.text_input("Correo")
        empresa = st.text_input("Empresa")
        if st.form_submit_button("Registrar"):
            try:
                datos = schemas.AsistenteCreate(documento_identidad=documento.strip(), nombre=nombre.strip(),
                                                email=email.strip(), empresa=empresa.strip())
                nuevo = api_client.crear_asistente(datos.model_dump(mode="json"))
                api_client.exito(f"Asistente {nuevo['nombre']} registrado con ID {nuevo['id']}.")
            except ValidationError as e:
                api_client.mostrar_validacion(e)
            except ApiError as e:
                api_client.mostrar_error(e)

    st.subheader("Asistentes registrados")
    st.dataframe(pd.DataFrame(list(asistentes.values())), hide_index=True)
