import streamlit as st
import api_client  # Importamos nuestro puente

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from back.app import schemas # Reusamos DTOs
from pydantic import ValidationError

st.header("📋 Gestión de Pacientes")

tab1, tab2 = st.tabs(["Listar", "Registrar"])

with tab1:
    if st.button("Actualizar Lista"):
        datos = api_client.get_all_pacientes()
        st.table(datos)

with tab2:
    with st.form("crear_paciente"):
        nombre = st.text_input("Nombre")
        # ... resto de campos
        if st.form_submit_button("Guardar"):
            # Lógica de validación con DTO y envío a api_client
            pass