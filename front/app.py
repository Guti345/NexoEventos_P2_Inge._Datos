import streamlit as st

st.set_page_config(
    page_title="OrthoConnect Pro",
    page_icon="🦷",
    layout="wide"
)

st.title("Bienvenido a OrthoConnect Pro")
st.markdown("""
Esta es la plataforma central de gestión clínica. 
Utilice el **menú lateral** para navegar entre los diferentes módulos:
- **Pacientes:** Registro y consulta.
- **Tratamientos:** Gestión de procedimientos activos.
- **Reportes:** Estadísticas de eficacia y atención.
""")

st.info("Seleccione un módulo para comenzar.")