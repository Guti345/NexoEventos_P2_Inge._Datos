from datetime import datetime

import pandas as pd
import streamlit as st

import api_client as api
import ui
from api_client import ApiError

ui.preparar_pagina()

st.title("Asistentes y check-in")
ui.mostrar_flash()

eventos = sorted(ui.cargar(api.get_eventos), key=lambda e: e["inicio"], reverse=True)
asistentes = ui.cargar(api.get_asistentes)
por_evento = {e["id"]: e for e in eventos}
por_asistente = {a["id"]: a for a in asistentes}

if not eventos:
    st.stop()


def elegir_evento(clave: str):
    return st.selectbox("Evento", list(por_evento), key=clave, format_func=lambda i: ui.etiqueta_evento(por_evento[i]))


tab_puerta, tab_inscritos, tab_inscribir, tab_registrar = st.tabs(
    ["Check-in en puerta", "Inscritos y llegadas", "Inscribir a un evento", "Registrar asistente"]
)

# Check-in en puerta
with tab_puerta:
    st.markdown(
        "Registre la llegada real con el **documento** del asistente. El trigger A2 solo lo acepta "
        "desde 1 hora antes del inicio hasta la hora de fin, y una sola vez por persona."
    )
    evento_id = elegir_evento("ev_checkin")
    ev = por_evento[evento_id]
    st.caption(f"Ventana de ingreso: {ui.fecha_hora(datetime.fromisoformat(ev['inicio']) - pd.Timedelta(hours=1))} → {ui.fecha_hora(ev['fin'])} · Ahora: {datetime.now():%d/%m/%Y %H:%M}")
    with st.form("form_checkin", clear_on_submit=True):
        documento = st.text_input("Documento del asistente", max_chars=10, placeholder="Ej: 2000000001")
        if st.form_submit_button("Registrar llegada", type="primary"):
            try:
                r = api.checkin(evento_id, documento.strip())
                nombre = por_asistente.get(r["asistente_id"], {}).get("nombre", documento)
                ui.exito(f"Bienvenido(a) **{nombre}**. Llegada registrada a las {ui.fecha_hora(r['fecha_checkin'])}.")
            except ApiError as e:
                ui.mostrar_error(e)

# Inscritos y llegadas
with tab_inscritos:
    evento_id = elegir_evento("ev_inscritos")
    ev = por_evento[evento_id]
    inscripciones = ui.cargar(api.get_inscripciones, evento_id)

    llegaron = sum(1 for i in inscripciones if i["fecha_checkin"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aforo contratado", ev["aforo_esperado"])
    c2.metric("Inscritos", len(inscripciones))
    c3.metric("Llegaron", llegaron)
    c4.metric(
        "Tasa de asistencia",
        ui.porcentaje(ev["tasa_asistencia"]) if ev["tasa_asistencia"] is not None
        else (f"{llegaron * 100 / len(inscripciones):.2f} % (parcial)" if inscripciones else "—"),
        help="La tasa oficial la guarda el trigger A4 al finalizar el evento.",
    )
    if inscripciones:
        st.progress(min(len(inscripciones) / ev["aforo_esperado"], 1.0), text=f"Cupo usado: {len(inscripciones)} de {ev['aforo_esperado']}")
        filtro = st.radio("Mostrar", ["Todos", "Solo los que llegaron", "Solo los que no han llegado"], horizontal=True)
        filas = []
        for i in inscripciones:
            a = por_asistente.get(i["asistente_id"], {})
            if filtro == "Solo los que llegaron" and not i["fecha_checkin"]:
                continue
            if filtro == "Solo los que no han llegado" and i["fecha_checkin"]:
                continue
            filas.append({
                "Documento": a.get("documento_identidad"),
                "Nombre": a.get("nombre"),
                "Empresa": a.get("empresa"),
                "Llegó": "Sí" if i["fecha_checkin"] else "No",
                "Hora de llegada": ui.fecha_hora(i["fecha_checkin"]) if i["fecha_checkin"] else "",
            })
        ui.tabla(filas)
    else:
        st.info("Este evento no tiene inscritos.")

# Inscribir a un evento
with tab_inscribir:
    st.markdown("El trigger A2 rechaza inscripciones en eventos cancelados o finalizados, o por encima del aforo contratado.")
    evento_id = elegir_evento("ev_inscribir")
    ev = por_evento[evento_id]
    inscritos_ids = {i["asistente_id"] for i in ui.cargar(api.get_inscripciones, evento_id)}
    st.caption(f"Cupo: {len(inscritos_ids)} de {ev['aforo_esperado']} · Estado: {ev['estado']}")

    buscar = st.text_input("Buscar asistente por nombre, documento o empresa", key="buscar_insc")
    candidatos = [
        a for a in asistentes
        if a["id"] not in inscritos_ids
        and (not buscar or buscar.lower() in f"{a['nombre']} {a['documento_identidad']} {a['empresa']}".lower())
    ]
    if candidatos:
        asistente_id = st.selectbox(
            "Asistente", [a["id"] for a in candidatos],
            format_func=lambda i: f"{por_asistente[i]['nombre']} · {por_asistente[i]['documento_identidad']} · {por_asistente[i]['empresa']}",
        )
        if st.button("Inscribir", type="primary"):
            try:
                api.inscribir(evento_id, asistente_id)
                ui.exito(f"{por_asistente[asistente_id]['nombre']} quedó inscrito(a) en «{ev['nombre']}».")
            except ApiError as e:
                ui.mostrar_error(e)
    else:
        st.info("No hay asistentes sin inscribir que coincidan con la búsqueda. Regístrelo en la pestaña «Registrar asistente».")

# Registrar asistente
with tab_registrar:
    with st.form("form_asistente", clear_on_submit=True):
        c1, c2 = st.columns(2)
        doc = c1.text_input("Documento de identidad", max_chars=10)
        nombre = c2.text_input("Nombre completo", max_chars=60)
        email = c1.text_input("Correo")
        empresa = c2.text_input("Empresa", max_chars=100)
        if st.form_submit_button("Registrar asistente", type="primary"):
            try:
                nuevo = api.crear_asistente({
                    "documento_identidad": doc.strip(), "nombre": nombre.strip(),
                    "email": email.strip(), "empresa": empresa.strip(),
                })
                ui.exito(f"Asistente **{nuevo['nombre']}** registrado (ID {nuevo['id']}). Ya puede inscribirlo a un evento.")
            except ApiError as e:
                ui.mostrar_error(e)

    st.subheader("Directorio de asistentes")
    filtro_dir = st.text_input("Buscar", key="buscar_dir")
    ui.tabla(
        [a for a in asistentes if not filtro_dir or filtro_dir.lower() in f"{a['nombre']} {a['documento_identidad']} {a['empresa']}".lower()],
        {"documento_identidad": "Documento", "nombre": "Nombre", "email": "Correo", "empresa": "Empresa"},
    )