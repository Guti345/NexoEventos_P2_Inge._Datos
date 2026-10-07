# NexoEventos

Proyecto integrador de la materia **Ingeniería de Datos** (Universidad del Rosario, Escuela de Ciencias e Ingeniería) — Parcial 2.

## Finalidad

El Centro de Convenciones Nexo alquila salones y servicios para congresos, ferias y eventos corporativos/sociales, y hoy gestiona todo en hojas de cálculo. NexoEventos es el sistema de información que lo reemplaza: evita dobles reservas de salones, liquida automáticamente el valor de cada evento (salón + servicios contratados) y mide la tasa real de asistencia a partir de las inscripciones y los check-in en puerta.

## Arquitectura

El sistema tiene tres capas, y el frontend **nunca** se conecta directo a la base de datos: toda operación pasa por la API.

```
Streamlit (front/)  →  FastAPI (back/app/)  →  PostgreSQL (triggers, funciones y vistas en back/sql/)
```

- **Backend — `back/`**: API REST en FastAPI con SQLAlchemy (entidades) y Pydantic (DTO de entrada/salida). Expone endpoints para clientes, salones, eventos, servicios, asistentes, inscripciones, staff, auditoría y reportes.
- **Reglas de negocio — `back/sql/`**: scripts SQL (triggers, funciones y vistas) que se aplican después de crear las tablas y garantizan las reglas aunque se inserten datos fuera de la API (por ejemplo desde psql). Incluye el script de carga de datos de prueba.
- **Frontend — `front/`**: aplicación Streamlit que debe consumir la API para la gestión visual de eventos, asistentes, disponibilidad de salones y reportes. 
- **Documentación — `documentacion/`**: capturas de evidencia (Swagger/API/Postman + Streamlit) de las reglas de negocio y reportes.

## Componentes del dominio

| Entidad | Resumen |
|---|---|
| Clientes | Empresa (NIT) o persona natural (cédula) que contrata eventos. |
| Salones | 6 salones (pequeño/mediano/grande) con capacidad y precio por hora; pueden deshabilitarse temporalmente. |
| Eventos | Pertenecen a un cliente y un salón; ciclo de vida `Cotizado → Confirmado → Finalizado/Cancelado`. |
| Servicios | Catálogo de bebidas, refrigerios y audiovisuales, cobrados por persona, hora o unidad; el precio se congela al contratarlos. |
| Asistentes | Se registran una vez y se inscriben a eventos; se controla cupo, aforo y check-in. |
| Staff | Jerarquía organizacional (dirección, gerencias, jefaturas, coordinaciones) con jefe inmediato. |
| Trazabilidad | Auditoría de cambios de estado, salón u horario de cada evento (valor anterior, nuevo, fecha y usuario). |

## Lógica en base de datos

**Triggers y funciones (Módulo A)**
- **A1** — Disponibilidad y capacidad del salón (bloquea cruces de horario y aforo excedido).
- **A2** — Control de cupos e inscripción, y ventana válida de check-in.
- **A3** — Liquidación automática del valor total del evento (salón + servicios).
- **A4** — Cierre de evento (estados definitivos), cálculo de tasa de asistencia y auditoría.
- **A5** — Función de salones disponibles para un horario y aforo dados.

**Reportes de inteligencia de negocio (Módulo B)**
- **B1** — Organigrama (CTE recursiva).
- **B2** — Cadena de escalamiento (CTE recursiva).
- **B3** — Ranking de clientes y análisis de Pareto (funciones de ventana).
- **B4** — Ocupación de salones y tiempos muertos (funciones de ventana).
