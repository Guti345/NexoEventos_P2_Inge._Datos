import pandas as pd
import streamlit as st

import api_client

st.set_page_config(
    page_title="NexoEventos",
    layout="wide"
)

st.title("Bienvenido a NexoEventos")
st.markdown("""
Plataforma de gestión del Centro de Convenciones Nexo.
Utilice el **menú lateral** para navegar entre los diferentes módulos:
- **Eventos:** creación, servicios, cotización, estados, reprogramación y auditoría.
- **Asistentes y check-in:** registro, inscripciones y asistencia real.
- **Disponibilidad de salones:** consulta por fecha, horario y número de personas.
- **Clientes y staff:** registro y consulta.
- **Reportes:** organigrama, escalamiento, ranking de clientes y ocupación de salones.
""")

st.info("Seleccione un módulo para comenzar.")

eventos = api_client.cargar(api_client.get_eventos)
salones = {s["id"]: s["nombre_salon"] for s in api_client.cargar(api_client.get_salones)}

if eventos:
    df = pd.DataFrame(eventos)
    df["inicio"] = pd.to_datetime(df["inicio"], format="ISO8601")
    df["tasa_asistencia"] = pd.to_numeric(df["tasa_asistencia"])

    st.subheader("Eventos por estado")
    columnas = st.columns(4)
    for columna, estado in zip(columnas, api_client.ESTADOS):
        columna.metric(estado, int((df["estado"] == estado).sum()))
    st.bar_chart(df["estado"].value_counts())

    st.subheader("Tasa de asistencia promedio")
    tasas = df.loc[df["estado"] == "Finalizado", "tasa_asistencia"].dropna()
    st.metric("Eventos finalizados", f"{tasas.mean():.2f} %" if len(tasas) else "-")

    st.subheader("Próximos eventos")
    proximos = df[(df["inicio"] >= pd.Timestamp.now()) & df["estado"].isin(["Cotizado", "Confirmado"])]
    proximos = proximos.sort_values("inicio")
    st.dataframe(pd.DataFrame({
        "Fecha": proximos["inicio"].dt.strftime("%d/%m/%Y %H:%M"),
        "Evento": proximos["nombre"],
        "Estado": proximos["estado"],
        "Salón": proximos["salon_id"].map(salones),
        "Aforo": proximos["aforo_esperado"],
        "Valor total": proximos["valor_total_cotizado"].map(api_client.dinero),
    }), hide_index=True)
