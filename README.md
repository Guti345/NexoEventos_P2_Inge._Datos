# NexoEventos

Ingeniería de Datos — Parcial 2 — Universidad del Rosario, Escuela de Ciencias e Ingeniería
Entregable 1: Backend · Antonio Gutiérrez, David Rodríguez, David Pascagaza, Sara Torres

## Descripción y Finalidad

El Centro de Convenciones Nexo alquila seis salones y un catálogo de servicios (bebidas, refrigerios y audiovisuales) para congresos, ferias, seminarios y eventos corporativos o sociales. Hoy gestiona todo en hojas de cálculo, lo que genera dobles reservas, cotizaciones manuales y ninguna trazabilidad sobre la asistencia real.

**NexoEventos** es el sistema de información que resuelve ese problema de negocio mediante tres garantías que la propia base de datos hace cumplir, incluso si alguien inserta datos por fuera de la API:

1. **Sin dobles reservas**: ningún salón puede tener dos eventos cruzados, respetando 1 hora de montaje entre ellos y la capacidad contratada.
2. **Liquidación automática**: el valor de cada evento (alquiler del salón + servicios contratados con precio congelado) se mantiene siempre correcto, sin que la aplicación lo calcule.
3. **Medición real de asistencia**: cada evento finalizado queda con su tasa de asistencia (check-ins reales sobre inscritos) y con un historial de auditoría de cada cambio de estado, salón u horario.

## Componentes del Sistema

El sistema tiene tres capas; el frontend **nunca** se conecta directo a la base de datos, toda operación pasa por la API.

```
Streamlit (front/)  →  FastAPI (back/app/)  →  PostgreSQL (triggers, funciones y vistas en back/sql/)
```

| Componente | Tecnología | Rol |
|---|---|---|
| **Backend** — `back/` | FastAPI + SQLAlchemy + Pydantic | API REST: entidades (`app/models.py`), DTO de entrada/salida (`app/schemas.py`) y un router por recurso (`app/routers/`). |
| **Reglas de negocio** — `back/sql/` | PostgreSQL (PL/pgSQL) | Triggers, funciones y vistas que se aplican después de `Base.metadata.create_all(...)`; incluye la carga de datos de prueba (`datos_prueba.sql`). |
| **Frontend** — `front/` | Streamlit | Interfaz visual que consume la API para gestionar eventos, asistentes, disponibilidad de salones y reportes. *(en desarrollo; actualmente conserva el ejemplo base de la materia, pendiente de adaptar a los módulos de NexoEventos)*. |
| **Documentación** — `documentacion/` | — | Evidencia en capturas (Postman/Swagger + Streamlit) de cada regla de negocio y reporte. |

### Lógica en base de datos

**Módulo A — Triggers y funciones** (`back/sql/a1_*.sql` a `a5_*.sql`)
| Regla | Función |
|---|---|
| A1 | Disponibilidad y capacidad del salón: bloquea cruces de horario (con hora de montaje) y aforo que supera la capacidad. |
| A2 | Cupos e inscripción: impide inscribir por encima del aforo o en eventos cancelados/finalizados, y controla la ventana y unicidad del check-in. |
| A3 | Liquidación automática: recalcula `valor_total_cotizado` al crear el evento, y al agregar, modificar o quitar servicios; congela el precio del catálogo. |
| A4 | Cierre y auditoría: estados definitivos (`Finalizado`/`Cancelado`), cálculo de `tasa_asistencia` y registro en `trazabilidad`. |
| A5 | Función `fn_salones_disponibles`: dado un horario y un aforo, devuelve los salones habilitados, sin cruces y con capacidad suficiente, ordenados del más pequeño al más grande. |

**Módulo B — Reportes de inteligencia de negocio** (`back/sql/b1_*.sql` a `b4_*.sql`)
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
| `eventos` | `EventosEntity` | Evento de un cliente en un salón; ciclo de vida `Cotizado → Confirmado → Finalizado/Cancelado`; guarda el precio del salón congelado, el valor total y la tasa de asistencia. |
| `servicios` | `ServiciosEntity` | Catálogo de servicios (bebidas, refrigerios, audiovisuales) cobrados por persona, hora o unidad. |
| `servicios_eventos` | `ServiciosEventosEntity` | Relación N:M entre eventos y servicios; guarda cantidad y precio congelado al momento de la contratación. |
| `asistentes` | `AsistentesEntity` | Personas que se inscriben a eventos. Documento único. |
| `inscripciones` | `InscripcionesEntity` | Relación N:M entre asistentes y eventos; guarda la hora de check-in. |
| `staff` | `StaffEntity` | Empleados del centro, con auto-referencia (`jefe_id`) para la jerarquía organizacional. |
| `trazabilidad` | `TrazabilidadEntity` | Auditoría de cambios de `estado`, `salon_id`, `inicio` o `fin` de un evento (valor anterior, nuevo, fecha y usuario). |

Relaciones principales: `eventos` referencia a `clientes`, `salones` y `staff` (coordinador); `servicios_eventos` resuelve eventos↔servicios; `inscripciones` resuelve asistentes↔eventos; `staff.jefe_id` es una auto-referencia; `trazabilidad.evento_id` referencia a `eventos`.

## Endpoints y Pruebas

La API expone 23 endpoints mínimos documentados y probados contra la base cargada con `back/sql/datos_prueba.sql`. El detalle de cada prueba (petición, tablas y reglas involucradas, y evidencia en Postman) está en **[Lista de EndPoints.pdf](<Lista de EndPoints.pdf>)**.

Códigos de respuesta: `200/201/204` en éxito, `404` si el recurso no existe, `409` cuando un trigger rechaza la operación (incluye el mensaje de la regla violada), `422` cuando el DTO de Pydantic rechaza los datos de entrada.

| Prueba | Método | Ruta | Qué valida |
|---|---|---|---|
| MIN-01/02 | GET/POST | `/clientes/` | Listar/registrar clientes (`UNIQUE`, `CHECK`). |
| MIN-03 | GET | `/clientes/{id}/eventos` | Eventos de un cliente. |
| MIN-04/05 | GET/POST | `/staff/` | Listar/registrar staff (jerarquía, solo el Director sin jefe). |
| MIN-06/07 | GET | `/salones/`, `/servicios/` | Catálogo. |
| MIN-08 | GET | `/salones/disponibles` | Función A5 (disponibilidad por horario y aforo). |
| MIN-09/10 | GET/POST | `/eventos/` | Listar/crear eventos — triggers A1 y A3. |
| MIN-11 | GET | `/eventos/{id}` | Detalle del evento con valores calculados. |
| MIN-12 | PATCH | `/eventos/{id}` | Reprogramar — triggers A1, A3 y A4. |
| MIN-13 | PATCH | `/eventos/{id}/estado` | Confirmar/finalizar/cancelar — trigger A4. |
| MIN-14/15/16 | POST/PUT/DELETE | `/eventos/{id}/servicios` | Configurar servicios del evento — trigger A3. |
| MIN-17 | GET | `/eventos/{id}/cotizacion` | Desglose de costos: salón + servicios = total. |
| MIN-18 | GET | `/eventos/{id}/auditoria` | Historial de cambios — trigger A4. |
| MIN-19/20 | GET/POST | `/asistentes/` | Listar/registrar asistentes (documento único). |
| MIN-21/22 | POST/GET | `/eventos/{id}/inscripciones` | Inscribir/listar inscritos — trigger A2 (cupo). |
| MIN-23 | POST | `/eventos/{id}/checkin` | Registrar check-in — trigger A2 (ventana horaria, único por persona). |
| B1–B4 | GET | `/reportes/organigrama`, `/escalamiento/{id}`, `/pareto-clientes`, `/ocupacion-salones` | Reportes del Módulo B. |

**Cómo validar el funcionamiento**: con la API corriendo y la base cargada, importe la colección de Postman (o use `/docs`) y ejecute las pruebas MIN-01 a MIN-23 en orden — varias dependen de IDs creados por pruebas previas (p. ej. MIN-21 inscribe al asistente creado en MIN-20). Para confirmar que una regla de negocio está activa en la base (no solo en Python), repita la operación bloqueada directamente desde `psql`/pgAdmin y verifique que también sea rechazada.

## Guía de Instalación y Uso

Requisitos: Python 3.11+ y PostgreSQL en ejecución.

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd NexoEventos_P2_Inge._Datos

# 2. Crear y activar el entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Instalar dependencias (API + frontend)
pip install -r requirements.txt

# 4. Configurar variables de entorno
#    Crear back/.env con la cadena de conexión a PostgreSQL:
#    DATABASE_URL=postgresql+psycopg2://usuario:password@localhost:5432/NexoEventos_DB

# 5. Crear la base de datos vacía en PostgreSQL
#    (desde psql o pgAdmin) CREATE DATABASE "NexoEventos_DB";

# 6. Levantar la API — crea las tablas automáticamente (Base.metadata.create_all)
cd back
uvicorn main:app --reload
#    Documentación interactiva: http://localhost:8000/docs

# 7. Aplicar triggers, funciones, vistas y datos de prueba (en este orden)
psql -U <usuario> -d NexoEventos_DB -f sql/a1_disponibilidad.sql
psql -U <usuario> -d NexoEventos_DB -f sql/a2_cupos_checkin.sql
psql -U <usuario> -d NexoEventos_DB -f sql/a3_liquidacion.sql
psql -U <usuario> -d NexoEventos_DB -f sql/a4_auditoria.sql
psql -U <usuario> -d NexoEventos_DB -f sql/a5_salones_disponibles.sql
psql -U <usuario> -d NexoEventos_DB -f sql/b1_organigrama.sql
psql -U <usuario> -d NexoEventos_DB -f sql/b2_escalamiento.sql
psql -U <usuario> -d NexoEventos_DB -f sql/b3_pareto_clientes.sql
psql -U <usuario> -d NexoEventos_DB -f sql/b4_ocupacion_salones.sql
psql -U <usuario> -d NexoEventos_DB -f sql/datos_prueba.sql

# 8. (Opcional) Levantar el frontend en otra terminal, desde la raíz del repo
cd front
streamlit run main.py
```

Con la API corriendo, pruebe los endpoints desde `http://localhost:8000/docs` o con la colección de Postman referenciada en [Lista de EndPoints.pdf](<Lista de EndPoints.pdf>).
