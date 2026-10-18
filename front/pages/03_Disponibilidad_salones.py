from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st

import api_client
from api_client import ApiError

api_client.configurar_pagina("Disponibilidad de salones")

c1, c2, c3, c4 = st.columns(4)
dia = c1.date_input("Fecha", value=date.today() + timedelta(days=7))
hora_inicio = c2.time_input("Hora de inicio", value=time(8, 0))
hora_fin = c3.time_input("Hora de fin", value=time(12, 0))
personas = c4.number_input("Personas", min_value=1, value=100)
dia_siguiente = st.checkbox("Termina al día siguiente (después de medianoche)")

inicio = datetime.combine(dia, hora_inicio)
fin = datetime.combine(dia + timedelta(days=1) if dia_siguiente else dia, hora_fin)

if st.button("Consultar"):
    try:
        disponibles = api_client.get_salones_disponibles(inicio, fin, personas)
        if disponibles:
            st.dataframe(pd.DataFrame([{
                "Salón": s["nombre_salon"],
                "Tamaño": s["tamano"],
                "Capacidad": s["capacidad"],
                "Precio por hora": api_client.dinero(s["precio_hora"]),
                "Costo para ese horario": api_client.dinero(s["costo_estimado"]),
            } for s in disponibles]), hide_index=True)
        else:
            st.warning("No hay salones disponibles para ese horario y número de personas.")
    except ApiError as e:
        api_client.mostrar_error(e)