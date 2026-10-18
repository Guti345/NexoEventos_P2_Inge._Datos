import os
import sys
from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st
from pydantic import ValidationError

import api_client
from api_client import ApiError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from back.app import schemas

api_client.configurar_pagina("Eventos")

salones = {s["id"]: s["nombre_salon"] for s in api_client.cargar(api_client.get_salones)}
servicios = {s["id"]: s["nombre_servicio"] for s in api_client.cargar(api_client.get_servicios)}
clientes = {c["id"]: c["nombre"] for c in api_client.cargar(api_client.get_clientes)}
staff = {s["id"]: f"{s['nombre']} ({s['cargo']})" for s in api_client.cargar(api_client.get_staff)}


def fecha_y_hora(etiqueta, valor, clave):
    c1, c2 = st.columns(2)
    dia = c1.date_input(f"{etiqueta} - fecha", value=valor.date(), key=f"{clave}_dia")
    hora = c2.time_input(f"{etiqueta} - hora", value=valor.time(), key=f"{clave}_hora")
    return datetime.combine(dia, hora)


tab_listar, tab_crear, tab_gestionar = st.tabs(["Listar", "Crear evento", "Gestionar evento"])

# Listar
with tab_listar:
    estado = st.selectbox("Filtrar por estado", ["Todos"] + api_client.ESTADOS)
    eventos = api_client.cargar(api_client.get_eventos, None if estado == "Todos" else estado)
    if eventos:
        st.dataframe(pd.DataFrame([{
            "ID": e["id"],
            "Evento": e["nombre"],
            "Estado": e["estado"],
            "Inicio": api_client.fecha_hora(e["inicio"]),
            "Fin": api_client.fecha_hora(e["fin"]),
            "Salón": salones.get(e["salon_id"]),
            "Cliente": clientes.get(e["cliente_id"]),
            "Aforo": e["aforo_esperado"],
            "Valor total": api_client.dinero(e["valor_total_cotizado"]),
        } for e in eventos]), hide_index=True)

# Crear evento
with tab_crear:
    st.write("Indique el horario y el aforo. Solo se muestran los salones disponibles (función A5).")
    sugerido = datetime.combine(date.today() + timedelta(days=7), time(8, 0))
    inicio = fecha_y_hora("Inicio", sugerido, "crear_inicio")
    fin = fecha_y_hora("Fin", sugerido + timedelta(hours=4), "crear_fin")
    aforo = st.number_input("Aforo esperado", min_value=1, value=50)

    if fin <= inicio:
        st.warning("La hora de fin debe ser posterior al inicio.")
    else:
        disponibles = api_client.cargar(api_client.get_salones_disponibles, inicio, fin, aforo)
        if not disponibles:
            st.warning("No hay salones disponibles para ese horario y aforo.")
        else:
            opciones_salon = {s["salon_id"]: f"{s['nombre_salon']} (capacidad {s['capacidad']}, "
                                             f"costo {api_client.dinero(s['costo_estimado'])})" for s in disponibles}
            with st.form("crear_evento"):
                salon_id = st.selectbox("Salón disponible", list(opciones_salon), format_func=opciones_salon.get)
                nombre = st.text_input("Nombre del evento")
                tipo = st.selectbox("Tipo", api_client.TIPOS_EVENTO)
                cliente_id = st.selectbox("Cliente", list(clientes), format_func=clientes.get)
                coordinador_id = st.selectbox("Coordinador", list(staff), format_func=staff.get)
                if st.form_submit_button("Crear evento"):
                    try:
                        datos = schemas.EventoCreate(
                            nombre=nombre, tipo=tipo, inicio=inicio, fin=fin, aforo_esperado=aforo,
                            salon_id=salon_id, cliente_id=cliente_id, coordinador_id=coordinador_id,
                        )
                        nuevo = api_client.crear_evento(datos.model_dump(mode="json"))
                        api_client.exito(f"Evento {nuevo['id']} creado. Valor total: {api_client.dinero(nuevo['valor_total_cotizado'])}")
                    except ValidationError as e:
                        api_client.mostrar_validacion(e)
                    except ApiError as e:
                        api_client.mostrar_error(e)

# Gestionar evento
with tab_gestionar:
    todos = sorted(api_client.cargar(api_client.get_eventos), key=lambda e: e["id"], reverse=True)
    opciones_evento = {e["id"]: f"{e['id']} - {e['nombre']} ({e['estado']})" for e in todos}
    evento_id = st.selectbox("Evento", list(opciones_evento), format_func=opciones_evento.get)
    evento = api_client.cargar(api_client.get_evento, evento_id) if evento_id else None

    if evento:
        st.write(f"**Estado:** {evento['estado']}  |  **Salón:** {salones.get(evento['salon_id'])}  |  "
                 f"**Horario:** {api_client.fecha_hora(evento['inicio'])} a {api_client.fecha_hora(evento['fin'])}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Inscritos / aforo", f"{evento['asistencia']['inscritos']} / {evento['aforo_esperado']}")
        c2.metric("Valor total", api_client.dinero(evento["valor_total_cotizado"]))
        c3.metric("Tasa de asistencia", f"{evento['tasa_asistencia']} %" if evento["tasa_asistencia"] else "-")

        t_cotizacion, t_servicios, t_estado, t_reprogramar, t_auditoria = st.tabs(
            ["Cotización", "Servicios", "Estado", "Reprogramar", "Auditoría"]
        )

        with t_cotizacion:
            cotizacion = api_client.cargar(api_client.get_cotizacion, evento_id)
            if cotizacion:
                filas = [{
                    "Concepto": "Alquiler del salón",
                    "Cantidad": cotizacion["hora_salon"],
                    "Precio unitario": api_client.dinero(cotizacion["precio_hora_salon"]),
                    "Subtotal": api_client.dinero(cotizacion["valor_total_salon"]),
                }]
                for s in cotizacion["servicios"]:
                    filas.append({
                        "Concepto": s["nombre_servicio"],
                        "Cantidad": s["cantidad"],
                        "Precio unitario": api_client.dinero(s["precio_unidad_cotizado"]),
                        "Subtotal": api_client.dinero(s["valor_total_cotizado"]),
                    })
                st.dataframe(pd.DataFrame(filas), hide_index=True)
                st.metric("Total (salón + servicios)", api_client.dinero(cotizacion["valor_total_cotizado"]))

        with t_servicios:
            contratados = evento["servicios"]
            if contratados:
                st.dataframe(pd.DataFrame([{
                    "Servicio": servicios.get(s["servicio_id"]),
                    "Cantidad": s["cantidad"],
                    "Precio congelado": api_client.dinero(s["precio_unidad_cotizado"]),
                } for s in contratados]), hide_index=True)

            with st.form("agregar_servicio"):
                servicio_id = st.selectbox("Servicio", list(servicios), format_func=servicios.get)
                cantidad = st.number_input("Cantidad (0 = automática según aforo u horas)", min_value=0, value=0)
                if st.form_submit_button("Agregar servicio"):
                    try:
                        api_client.agregar_servicio(evento_id, servicio_id, int(cantidad) or None)
                        api_client.exito("Servicio agregado. El total se recalculó en la base.")
                    except ApiError as e:
                        api_client.mostrar_error(e)

            if contratados:
                with st.form("modificar_servicio"):
                    servicio_id = st.selectbox("Servicio contratado", [s["servicio_id"] for s in contratados],
                                               format_func=servicios.get)
                    cantidad = st.number_input("Nueva cantidad", min_value=1, value=1)
                    c1, c2 = st.columns(2)
                    modificar = c1.form_submit_button("Modificar cantidad")
                    quitar = c2.form_submit_button("Quitar servicio")
                try:
                    if modificar:
                        api_client.modificar_servicio(evento_id, servicio_id, int(cantidad))
                        api_client.exito("Cantidad modificada. El total se recalculó en la base.")
                    if quitar:
                        api_client.quitar_servicio(evento_id, servicio_id)
                        api_client.exito("Servicio quitado. El total se recalculó en la base.")
                except ApiError as e:
                    api_client.mostrar_error(e)

        with t_estado:
            nuevo_estado = st.selectbox("Nuevo estado", ["Confirmado", "Finalizado", "Cancelado"])
            if st.button("Cambiar estado"):
                try:
                    respuesta = api_client.cambiar_estado(evento_id, nuevo_estado)
                    api_client.exito(f"El evento ahora está {respuesta['estado']}.")
                except ApiError as e:
                    api_client.mostrar_error(e)

        with t_reprogramar:
            nuevo_inicio = fecha_y_hora("Inicio", datetime.fromisoformat(evento["inicio"]), f"rep_inicio_{evento_id}")
            nuevo_fin = fecha_y_hora("Fin", datetime.fromisoformat(evento["fin"]), f"rep_fin_{evento_id}")
            nuevo_aforo = st.number_input("Aforo esperado", min_value=1, value=evento["aforo_esperado"],
                                          key=f"rep_aforo_{evento_id}")
            nuevo_salon = st.selectbox("Salón", list(salones), index=list(salones).index(evento["salon_id"]),
                                       format_func=salones.get, key=f"rep_salon_{evento_id}")
            if st.button("Reprogramar"):
                try:
                    api_client.reprogramar_evento(evento_id, {
                        "inicio": nuevo_inicio.isoformat(), "fin": nuevo_fin.isoformat(),
                        "aforo_esperado": int(nuevo_aforo), "salon_id": nuevo_salon,
                    })
                    api_client.exito("Evento reprogramado. El cambio quedó en la auditoría.")
                except ApiError as e:
                    api_client.mostrar_error(e)

        with t_auditoria:
            auditoria = api_client.cargar(api_client.get_auditoria, evento_id)
            if auditoria:
                st.dataframe(pd.DataFrame([{
                    "Fecha": api_client.fecha_hora(a["fecha_hora"]),
                    "Usuario": a["usuario"],
                    "Campo": a["campo_modificado"],
                    "Antes": a["valor_anterior"],
                    "Después": a["valor_nuevo"],
                } for a in auditoria]), hide_index=True)
            else:
                st.info("Este evento no tiene cambios registrados.")
