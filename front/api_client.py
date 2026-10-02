import requests

URL_BASE = "http://localhost:8000"

def get_all_pacientes():
    return requests.get(f"{URL_BASE}/pacientes/").json()

def get_paciente_by_id(paciente_id):
    return requests.get(f"{URL_BASE}/pacientes/{paciente_id}")

def create_paciente(payload):
    return requests.post(f"{URL_BASE}/pacientes/", json=payload)

# Aquí los estudiantes agregarán las funciones para tratamientos, etc.
def get_tratamientos():
    return requests.get(f"{URL_BASE}/tratamientos/").json()