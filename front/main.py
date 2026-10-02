import streamlit as st
import requests
from datetime import date
import sys
import os

# 1. Ajuste de ruta para poder importar los schemas del backend
# Esto permite que el Frontend use las mismas reglas de Pydantic que el Backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.app import schemas
from pydantic import ValidationError

# Configuración de la URL de la API
URL_BASE = "http://localhost:8000"

st.set_page_config(page_title="OrthoConnect - Gestión de Pacientes", layout="wide")
st.title("🦷 OrthoConnect: Panel de Gestión")

# Menú lateral para navegación
menu = st.sidebar.radio("Operaciones", ["Listar Pacientes", "Crear Nuevo Paciente", "Buscar Paciente Específico"])

# ---------------------------------------------------------
# FUNCIÓN PARA LISTAR TODOS
# ---------------------------------------------------------
if menu == "Listar Pacientes":
    st.header("📋 Listado de Pacientes")
    
    try:
        response = requests.get(f"{URL_BASE}/pacientes/")
        if response.status_code == 200:
            pacientes = response.json()
            if pacientes:
                # Mostramos los datos en una tabla estética
                st.table(pacientes)
            else:
                st.info("No hay pacientes registrados aún.")
        else:
            st.error("No se pudo obtener la lista del servidor.")
    except Exception as e:
        st.error(f"Error de conexión: {e}")

# ---------------------------------------------------------
# FUNCIÓN PARA CREAR PACIENTE (Usa Pydantic para pre-validar)
# ---------------------------------------------------------
elif menu == "Crear Nuevo Paciente":
    st.header("👤 Registro de Nuevo Paciente")
    
    with st.form("form_registro"):
        nombre = st.text_input("Nombre Completo")
        fecha_nac = st.date_input("Fecha de Nacimiento", min_value=date(1920, 1, 1))
        contacto = st.text_input("Teléfono / Correo de contacto")
        referido_id = st.number_input("ID del paciente que refiere (Opcional)", min_value=0, value=0)
        
        btn_enviar = st.form_submit_button("Registrar Paciente")
        
        if btn_enviar:
            # Reutilizamos el DTO para validar antes de enviar
            try:
                # Convertimos el 0 de Streamlit a None si es opcional
                ref_id = referido_id if referido_id > 0 else None
                
                # PRE-VALIDACIÓN: Si esto falla, ni siquiera tocamos la red
                datos_paciente = schemas.PacienteCreate(
                    nombre=nombre,
                    fecha_nacimiento=fecha_nac,
                    contacto=contacto,
                    referido_por_id=ref_id
                )
                
                # ENVÍO AL BACKEND
                res = requests.post(f"{URL_BASE}/pacientes/", json=datos_paciente.model_dump(mode='json'))
                
                if res.status_code == 200 or res.status_code == 201:
                    st.success(f"✅ Paciente '{nombre}' creado con éxito (ID: {res.json()['id']})")
                else:
                    st.error(f"❌ Error del servidor: {res.json().get('detail')}")
                    
            except ValidationError as e:
                st.warning(f"⚠️ Datos inválidos según el esquema: {e.errors()[0]['msg']}")

# ---------------------------------------------------------
# FUNCIÓN PARA BUSCAR UNO ESPECÍFICO
# ---------------------------------------------------------
elif menu == "Buscar Paciente Específico":
    st.header("🔍 Detalle del Paciente")
    
    id_busqueda = st.number_input("Ingrese el ID del paciente", min_value=1, step=1)
    
    if st.button("Obtener Información"):
        try:
            response = requests.get(f"{URL_BASE}/pacientes/{id_busqueda}")
            
            if response.status_code == 200:
                p = response.json()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Nombre", p['nombre'])
                    st.write(f"**Contacto:** {p['contacto']}")
                with col2:
                    st.write(f"**Fecha Nacimiento:** {p['fecha_nacimiento']}")
                    st.write(f"**Referido por:** {p['referido_por_id'] or 'Nadie'}")
                
                st.json(p) # Muestra el código JSON "crudo" para que los alumnos lo vean
            else:
                st.error(f"Paciente con ID {id_busqueda} no encontrado.")
        except Exception as e:
            st.error("Asegúrate de que el endpoint GET /pacientes/{id} esté implementado en el backend.")