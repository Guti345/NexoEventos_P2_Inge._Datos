import os
import sys
from datetime import date

import pandas as pd
import streamlit as st
from pydantic import ValidationError

import api_client
from api_client import ApiError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from back.app import schemas

api_client.configurar_pagina("Clientes y staff")

tab_clientes, tab_staff = st.tabs(["Clientes", "Staff"])

# Clientes
with tab_clientes:
    buscar = st.text_input("Buscar por nombre, documento o correo")
    clientes = api_client.cargar(api_client.get_clientes, buscar)
    if clientes:
        st.dataframe(pd.DataFrame(clientes), hide_index=True)

        st.subheader("Eventos del cliente")
        nombres_clientes = {c["id"]: c["nombre"] for c in clientes}
        cliente_id = st.selectbox("Cliente", list(nombres_clientes), format_func=nombres_clientes.get)
        eventos = api_client.cargar(api_client.get_eventos_cliente, cliente_id)
        if eventos:
            st.dataframe(pd.DataFrame([{
                "ID": e["id"],
                "Evento": e["nombre"],
                "Estado": e["estado"],
                "Inicio": api_client.fecha_hora(e["inicio"]),
                "Valor total": api_client.dinero(e["valor_total_cotizado"]),
            } for e in eventos]), hide_index=True)
        else:
            st.info("Este cliente no tiene eventos.")

    st.subheader("Registrar cliente")
    with st.form("registrar_cliente", clear_on_submit=True):
        tipo_documento = st.selectbox("Tipo de documento", ["NIT", "CC"])
        numero_documento = st.text_input("Número de documento")
        nombre = st.text_input("Nombre o razón social")
        email = st.text_input("Correo")
        telefono = st.text_input("Teléfono")
        if st.form_submit_button("Registrar cliente"):
            try:
                datos = schemas.ClienteCreate(tipo_documento=tipo_documento, numero_documento=numero_documento.strip(),
                                              nombre=nombre.strip(), email=email.strip(), telefono=telefono.strip())
                nuevo = api_client.crear_cliente(datos.model_dump(mode="json"))
                api_client.exito(f"Cliente {nuevo['nombre']} registrado con ID {nuevo['id']}.")
            except ValidationError as e:
                api_client.mostrar_validacion(e)
            except ApiError as e:
                api_client.mostrar_error(e)

# Staff
with tab_staff:
    staff = api_client.cargar(api_client.get_staff)
    nombres_staff = {s["id"]: f"{s['nombre']} ({s['cargo']})" for s in staff}
    if staff:
        st.dataframe(pd.DataFrame([{
            "ID": s["id"],
            "Nombre": s["nombre"],
            "Cargo": s["cargo"],
            "Área": s["area"],
            "Jefe inmediato": nombres_staff.get(s["jefe_id"], "-"),
            "Correo": s["email"],
        } for s in staff]), hide_index=True)

    st.subheader("Registrar staff")
    with st.form("registrar_staff", clear_on_submit=True):
        nombre = st.text_input("Nombre completo")
        email = st.text_input("Correo")
        cargo = st.selectbox("Cargo", api_client.CARGOS)
        area = st.selectbox("Área", api_client.AREAS)
        fecha_ingreso = st.date_input("Fecha de ingreso", value=date.today())
        jefe_id = st.selectbox("Jefe inmediato", [None] + list(nombres_staff),
                               format_func=lambda i: "Sin jefe (solo el Director)" if i is None else nombres_staff[i])
        if st.form_submit_button("Registrar staff"):
            try:
                datos = schemas.StaffCreate(nombre=nombre.strip(), cargo=cargo, area=area, email=email.strip(),
                                            fecha_ingreso=fecha_ingreso, jefe_id=jefe_id)
                nuevo = api_client.crear_staff(datos.model_dump(mode="json"))
                api_client.exito(f"{nuevo['nombre']} registrado(a) como {nuevo['cargo']}.")
            except ValidationError as e:
                api_client.mostrar_validacion(e)
            except ApiError as e:
                api_client.mostrar_error(e)