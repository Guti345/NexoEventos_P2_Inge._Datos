import pandas as pd
import streamlit as st

import api_client

api_client.configurar_pagina("Reportes")

staff = api_client.cargar(api_client.get_staff)
nombres_staff = {s["id"]: f"{s['nombre']} ({s['cargo']})" for s in staff}

tab_b1, tab_b2, tab_b3, tab_b4 = st.tabs(
    ["B1 Organigrama", "B2 Cadena de escalamiento", "B3 Ranking de clientes", "B4 Ocupación de salones"]
)

# B1 Organigrama (CTE recursiva)
with tab_b1:
    staff_id = st.selectbox("Desde", [None] + list(nombres_staff),
                            format_func=lambda i: "Toda la organización" if i is None else nombres_staff[i])
    organigrama = api_client.cargar(api_client.reporte_organigrama, staff_id)
    if organigrama:
        df = pd.DataFrame(organigrama)
        st.dataframe(df[["nivel", "nombre", "cargo", "area", "personas_a_cargo", "ruta_mando"]], hide_index=True)
        st.bar_chart(df[df["personas_a_cargo"] > 0], x="nombre", y="personas_a_cargo", horizontal=True)

# B2 Cadena de escalamiento (CTE recursiva)
with tab_b2:
    con_jefe = [s["id"] for s in staff if s["jefe_id"] is not None]
    staff_id = st.selectbox("Miembro del staff", con_jefe, format_func=nombres_staff.get)
    cadena = api_client.cargar(api_client.reporte_escalamiento, staff_id) if staff_id else []
    if cadena:
        st.dataframe(pd.DataFrame(cadena)[["orden", "nombre", "cargo", "area", "email"]], hide_index=True)

# B3 Ranking de clientes y Pareto (funciones de ventana)
with tab_b3:
    pareto = api_client.cargar(api_client.reporte_pareto)
    if pareto:
        df = pd.DataFrame(pareto)
        df["total_facturado"] = df["total_facturado"].astype(float)
        df["acumulado"] = df["acumulado"].astype(float)
        df["cliente_en_orden"] = df["posicion"].map("{:02d}".format) + ". " + df["cliente"]
        st.dataframe(df[["posicion", "cliente", "eventos", "total_facturado", "participacion", "acumulado", "segmento_pareto"]],
                     hide_index=True)
        st.write("Total facturado por cliente")
        st.bar_chart(df, x="cliente_en_orden", y="total_facturado")
        st.write("Porcentaje acumulado")
        st.line_chart(df, x="cliente_en_orden", y="acumulado")

# B4 Ocupación de salones y tiempos muertos (funciones de ventana)
with tab_b4:
    ocupacion = api_client.cargar(api_client.reporte_ocupacion)
    if ocupacion:
        df = pd.DataFrame(ocupacion)
        df["horas_acumuladas"] = df["horas_acumuladas"].astype(float)
        st.dataframe(df[["salon", "numero_en_salon", "evento", "inicio", "fin", "evento_anterior", "dias_libres",
                         "horas_acumuladas"]], hide_index=True)
        st.write("Horas reservadas por salón")
        st.bar_chart(df.groupby("salon")["horas_acumuladas"].max())