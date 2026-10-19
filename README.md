# NexoEventos

Ingeniería de Datos - Parcial 2 - Universidad del Rosario, Escuela de Ciencias e Ingeniería
Entregable 2: Frontend · Antonio Gutiérrez, David Rodríguez, David Pascagaza, Sara Torres

## Descripción y Finalidad

El Centro de Convenciones Nexo alquila seis salones y un catálogo de servicios (bebidas, refrigerios y audiovisuales) para congresos, ferias, seminarios y eventos corporativos o sociales. Hoy gestiona todo en hojas de cálculo, lo que genera dobles reservas, cotizaciones manuales y ninguna trazabilidad sobre la asistencia real.

**NexoEventos** es el sistema de información que resuelve ese problema de negocio mediante tres garantías que la propia base de datos hace cumplir, incluso si alguien inserta datos por fuera de la API:

1. **Sin dobles reservas**: ningún salón puede tener dos eventos cruzados, respetando 1 hora de montaje entre ellos y la capacidad contratada.
2. **Liquidación automática**: el valor de cada evento (alquiler del salón + servicios contratados con precio congelado) se mantiene siempre correcto, sin que la aplicación lo calcule.
3. **Medición real de asistencia**: cada evento finalizado queda con su tasa de asistencia (check-ins reales sobre inscritos) y con un historial de auditoría de cada cambio de estado, salón u horario.

## Componentes del Sistema

El sistema tiene tres capas; el frontend **nunca** se conecta directo a la base de datos, toda operación pasa por la API.

```
Streamlit (front/)  ->  FastAPI (back/app/)  ->  PostgreSQL (triggers, funciones y vistas en back/sql/)
```

| Componente | Tecnología | Rol |
|---|---|---|
| **Backend** - `back/` | FastAPI + SQLAlchemy + Pydantic | API REST: entidades (`app/models.py`), DTO de entrada/salida (`app/schemas.py`) y un router por recurso (`app/routers/`). |
| **Reglas de negocio** - `back/sql/` | PostgreSQL (PL/pgSQL) | Triggers, funciones y vistas que se aplican después de `Base.metadata.create_all(...)`; incluye la carga de datos de prueba (`datos_prueba.sql`). |
| **Frontend** - `front/` | Streamlit | Interfaz visual que consume la API. Tablero de inicio (eventos por estado, tasa de asistencia, próximos eventos) y 5 módulos: **Eventos** (crear con salones disponibles, cotización, servicios, estado, reprogramación, auditoría), **Asistentes y check-in**, **Disponibilidad de salones**, **Clientes y staff** y **Reportes**. Cuando la base bloquea una operación (HTTP 409), la interfaz muestra el mensaje del trigger con la regla violada (A1-A4). |
| **Documentación** | PDF en la raíz y capturas en `documentacion/` | Manual de rutas, manual de usuario, diccionario de datos, diagrama relacional, reporte de evidencia del Entregable 1 y las capturas que los respaldan (API en `documentacion/documentacion_back/`, frontend en `documentacion/documentacion_front/`). |

### Lógica en base de datos

**Módulo A - Triggers y funciones** (`back/sql/a1_*.sql` a `a5_*.sql`)
| Regla | Función |
|---|---|
| A1 | Disponibilidad y capacidad del salón: bloquea cruces de horario (con hora de montaje) y aforo que supera la capacidad. |
| A2 | Cupos e inscripción: impide inscribir por encima del aforo o en eventos cancelados/finalizados, y controla la ventana y unicidad del check-in. |
| A3 | Liquidación automática: recalcula `valor_total_cotizado` al crear el evento, y al agregar, modificar o quitar servicios; congela el precio del catálogo. |
| A4 | Cierre y auditoría: estados definitivos (`Finalizado`/`Cancelado`), cálculo de `tasa_asistencia` y registro en `trazabilidad`. |
| A5 | Función `fn_salones_disponibles`: dado un horario y un aforo, devuelve los salones habilitados, sin cruces y con capacidad suficiente, ordenados del más pequeño al más grande. |

**Módulo B - Reportes de inteligencia de negocio** (`back/sql/b1_*.sql` a `b4_*.sql`)
| Reporte | Técnica |
|---|---|
| B1 | Organigrama: CTE recursiva con nivel, ruta de mando y personas a cargo. |
| B2 | Cadena de escalamiento: CTE recursiva hasta la dirección general. |
| B3 | Ranking de clientes y Pareto: funciones de ventana (participación y acumulado). |
| B4 | Ocupación de salones y tiempos muertos: `LAG()` con `PARTITION BY` para días libres y horas acumuladas. |

## Base de Datos y Modelo

El esquema (normalizado a 3FN) está compuesto por 9 tablas generadas a partir de las entidades de SQLAlchemy en `back/app/models.py`. El detalle completo de cada campo (tipo, nulabilidad, llaves y restricciones `CHECK`/`UNIQUE`) está documentado en **[Diccionario NexoEvents.pdf](<Diccionario NexoEvents.pdf>)**, y el modelo entidad-relación completo en **[Diagrama_relacional_parcial_2_Ingeniería_de_datos.pdf](<Diagrama_relacional_parcial_2_Ingeniería_de_datos.pdf>)**.

| Tabla | Entidad | Descripción |
|---|---|---|
| `clientes` | `ClientesEntity` | Empresa (NIT) o persona natural (CC) que contrata eventos. Documento único. |
| `salones` | `SalonesEntity` | Los 6 salones del catálogo, con tamaño, capacidad y precio por hora. |
| `eventos` | `EventosEntity` | Evento de un cliente en un salón; ciclo de vida `Cotizado -> Confirmado -> Finalizado/Cancelado`; guarda el precio del salón congelado, el valor total y la tasa de asistencia. |
| `servicios` | `ServiciosEntity` | Catálogo de servicios (bebidas, refrigerios, audiovisuales) cobrados por persona, hora o unidad. |
| `servicios_eventos` | `ServiciosEventosEntity` | Relación N:M entre eventos y servicios; guarda cantidad y precio congelado al momento de la contratación. |
| `asistentes` | `AsistentesEntity` | Personas que se inscriben a eventos. Documento único. |
| `inscripciones` | `InscripcionesEntity` | Relación N:M entre asistentes y eventos; guarda la hora de check-in. |
| `staff` | `StaffEntity` | Empleados del centro, con auto-referencia (`jefe_id`) para la jerarquía organizacional. |
| `trazabilidad` | `TrazabilidadEntity` | Auditoría de cambios de `estado`, `salon_id`, `inicio` o `fin` de un evento (valor anterior, valor nuevo y fecha). El usuario registrado es el de la conexión a la base; el diseño contempla propagar el usuario de la aplicación, pero esa propagación no está implementada en la API. |

Relaciones principales: `eventos` referencia a `clientes`, `salones` y `staff` (coordinador); `servicios_eventos` resuelve eventos↔servicios; `inscripciones` resuelve asistentes↔eventos; `staff.jefe_id` es una auto-referencia; `trazabilidad.evento_id` referencia a `eventos`.

## Endpoints de la API

La API expone las 23 rutas mínimas del enunciado y los 4 reportes; todas las consume el frontend (`front/api_client.py`). El detalle de cada endpoint (método, ruta, parámetros y códigos de respuesta propios de esa ruta, con el mensaje de la regla cuando un trigger bloquea) está en **[Manual Rutas NexoEventos.pdf](<Manual Rutas NexoEventos.pdf>)** y las pruebas/Manual de Usuario en **[Manual Usuario NexoEventos.pdf](<Manual Usuario NexoEventos.pdf>)**. La documentación interactiva está en `/docs` (Swagger) con la API en ejecución, y la evidencia de pruebas del Entregable 1 en **[Reporte Evidencia Funcionamiento.pdf](<Reporte Evidencia Funcionamiento.pdf>)**.

Códigos de respuesta: `200/201/204` en éxito, `404` si el recurso no existe, `409` cuando la operación es rechazada por un trigger o por el router (incluye el mensaje de la regla violada), `422` cuando la validación de FastAPI/Pydantic rechaza los datos de entrada. Cada ruta devuelve solo los códigos que le aplican; el manual de rutas los lista uno por uno.

| Prueba | Método | Ruta | Qué valida |
|---|---|---|---|
| MIN-01/02 | GET/POST | `/clientes/` | Listar/registrar clientes (`UNIQUE`, `CHECK`). |
| MIN-03 | GET | `/clientes/{id}/eventos` | Eventos de un cliente. |
| MIN-04/05 | GET/POST | `/staff/` | Listar/registrar staff (jerarquía, solo el Director sin jefe). |
| MIN-06/07 | GET | `/salones/`, `/servicios/` | Catálogo. |
| MIN-08 | GET | `/salones/disponibles` | Función A5 (disponibilidad por horario y aforo). |
| MIN-09/10 | GET/POST | `/eventos/` | Listar/crear eventos - triggers A1 y A3. |
| MIN-11 | GET | `/eventos/{id}` | Detalle del evento con valores calculados. |
| MIN-12 | PATCH | `/eventos/{id}` | Reprogramar - triggers A1, A3 y A4. |
| MIN-13 | PATCH | `/eventos/{id}/estado` | Confirmar/finalizar/cancelar - trigger A4. |
| MIN-14/15/16 | POST/PUT/DELETE | `/eventos/{id}/servicios` | Configurar servicios del evento - trigger A3. |
| MIN-17 | GET | `/eventos/{id}/cotizacion` | Desglose de costos: salón + servicios = total. |
| MIN-18 | GET | `/eventos/{id}/auditoria` | Historial de cambios - trigger A4. |
| MIN-19/20 | GET/POST | `/asistentes/` | Listar/registrar asistentes (documento único). |
| MIN-21/22 | POST/GET | `/eventos/{id}/inscripciones` | Inscribir/listar inscritos - trigger A2 (cupo). |
| MIN-23 | POST | `/eventos/{id}/checkin` | Registrar check-in - trigger A2 (ventana horaria, único por persona). |
| B1 | GET | `/reportes/organigrama` | Organigrama (CTE recursiva). |
| B2 | GET | `/reportes/escalamiento/{id}` | Cadena de escalamiento (CTE recursiva). |
| B3 | GET | `/reportes/pareto-clientes` | Ranking y Pareto de clientes (funciones de ventana). |
| B4 | GET | `/reportes/ocupacion-salones` | Ocupación y tiempos muertos (`LAG()`). |

## Documentación del entregable

| Documento | Contenido |
|---|---|
| [Manual Rutas NexoEventos.pdf](<Manual Rutas NexoEventos.pdf>) | Manual de rutas de la API: ficha por endpoint (método, ruta, propósito, parámetros y códigos de respuesta propios), con las convenciones de la API y los mensajes de los triggers. |
| [Manual Usuario NexoEventos.pdf](<Manual Usuario NexoEventos.pdf>) | Manual de usuario del frontend: puesta en marcha y recorrido por el tablero y los 5 módulos, ilustrado con las capturas de `documentacion/documentacion_front/`. |
| [Reporte Evidencia Funcionamiento.pdf](<Reporte Evidencia Funcionamiento.pdf>) | Evidencia de las pruebas del Entregable 1: petición, tablas y reglas involucradas en cada prueba MIN y B. |
| [Diccionario NexoEvents.pdf](<Diccionario NexoEvents.pdf>) | Detalle campo por campo de las 9 tablas. |
| [Diagrama_relacional_parcial_2_Ingeniería_de_datos.pdf](<Diagrama_relacional_parcial_2_Ingeniería_de_datos.pdf>) | Modelo entidad-relación. |
| `documentacion/documentacion_back/` | Capturas de evidencia de la API (MIN-01 a MIN-23, A4, A5, B1-B4). |
| `documentacion/documentacion_front/` | Capturas del frontend que ilustran el Manual de usuario. |

## Estructura del repositorio

```
├── back/                  # API FastAPI
│   ├── app/
│   │   ├── models.py      # Entidades SQLAlchemy (9 tablas)
│   │   ├── schemas.py     # DTO Pydantic
│   │   ├── routers/       # 10 routers (uno por recurso)
│   │   └── database.py    # Conexión (lee DATABASE_URL de back/.env)
│   ├── main.py            # Punto de entrada de la API
│   └── sql/               # a1-a5 (triggers/funciones), b1-b4 (reportes), datos_prueba.sql
├── front/                 # Frontend Streamlit
│   ├── app.py             # Tablero de inicio (ejecutar con: streamlit run app.py)
│   ├── api_client.py      # Cliente HTTP de la API y manejo de errores
│   └── pages/             # 5 módulos: Eventos, Asistentes y check-in,
│                          # Disponibilidad de salones, Clientes y staff, Reportes
├── documentacion/
│   ├── documentacion_back/    # Capturas de evidencia de la API
│   └── documentacion_front/   # Capturas del frontend
├── otros/sql_dp/          # Los mismos triggers, funciones y reportes organizados en
│                          # 3 scripts comentados, con referencias a la documentación de PostgreSQL
├── Manual Rutas NexoEventos.pdf
├── Manual Usuario NexoEventos.pdf
├── Reporte Evidencia Funcionamiento.pdf
├── Diccionario NexoEvents.pdf
├── Diagrama_relacional_parcial_2_Ingeniería_de_datos.pdf
├── requirements.txt
└── README.md
```

Nota: las páginas de `front/` importan los DTO desde `back/app/schemas.py`, por lo que el frontend debe ejecutarse con la carpeta `back/` al mismo nivel, tal como está en este repositorio.

## Guía de Instalación y Uso

Requisitos: Python 3.11+ y PostgreSQL en ejecución. Los comandos están escritos para Windows PowerShell (en macOS/Linux solo cambia la activación del entorno). Use **tres terminales**: la API queda en primer plano en una, los scripts SQL se aplican en otra y el frontend en la tercera.

### Preparación (una sola vez, cualquier terminal)

```powershell
git clone https://github.com/Guti345/NexoEventos_P2_Inge._Datos
cd NexoEventos_P2_Inge._Datos
python -m venv .venv
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Configuración (referencial, ajustar a su equipo):

- Cree el archivo `back/.env` con su cadena de conexión local, con este formato:
  `DATABASE_URL=postgresql+psycopg2://SU_USUARIO:SU_CLAVE@localhost:5432/NexoEventos_DB`
  (reemplace `SU_USUARIO` y `SU_CLAVE`; este archivo es local y está excluido del repositorio).
- Cree la base vacía desde psql o pgAdmin: `CREATE DATABASE "NexoEventos_DB";`

### Terminal 1 - API (desde la raíz del repo, entorno activado)

```powershell
cd back
uvicorn main:app --reload
```

Deje esta terminal abierta: la API queda en primer plano en `http://localhost:8000` y crea las tablas automáticamente (`Base.metadata.create_all`). Documentación interactiva: `http://localhost:8000/docs`.

### Terminal 2 - reglas de negocio y datos de prueba (una sola vez)

Desde la raíz del repo (`cd back` primero). Reemplace `SU_USUARIO` por su usuario de PostgreSQL antes de ejecutar:

```powershell
psql -U SU_USUARIO -d NexoEventos_DB -f sql/a1_disponibilidad.sql
psql -U SU_USUARIO -d NexoEventos_DB -f sql/a2_cupos_checkin.sql
psql -U SU_USUARIO -d NexoEventos_DB -f sql/a3_liquidacion.sql
psql -U SU_USUARIO -d NexoEventos_DB -f sql/a4_auditoria.sql
psql -U SU_USUARIO -d NexoEventos_DB -f sql/a5_salones_disponibles.sql
psql -U SU_USUARIO -d NexoEventos_DB -f sql/b1_organigrama.sql
psql -U SU_USUARIO -d NexoEventos_DB -f sql/b2_escalamiento.sql
psql -U SU_USUARIO -d NexoEventos_DB -f sql/b3_pareto_clientes.sql
psql -U SU_USUARIO -d NexoEventos_DB -f sql/b4_ocupacion_salones.sql
psql -U SU_USUARIO -d NexoEventos_DB -f sql/datos_prueba.sql
```

**Advertencia**: aplique estos scripts (y en particular `datos_prueba.sql`) solo sobre una base **nueva o de pruebas**. No los aplique sobre una base de trabajo existente: los scripts reemplazan funciones y triggers, y la carga inserta datos de ejemplo.

### Terminal 3 - Frontend (desde la raíz del repo, entorno activado)

```powershell
cd front
streamlit run app.py
```

Interfaz: `http://localhost:8501`. Por defecto el frontend busca la API en `http://localhost:8000`; si la API corre en otra dirección, defina la variable de entorno `NEXO_API_URL` antes de ejecutar Streamlit.
