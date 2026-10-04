-- =========================================================
-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- A5. Salones disponibles
-- =========================================================
-- Fuentes usadas (documentación oficial PostgreSQL 17):
-- Base: https://www.postgresql.org/docs/17/
-- [8.5]     datatype-datetime.html
--           TIMESTAMP para fecha y hora.
-- [36.5.10] xfunc-sql.html
--           Funciones que devuelven una tabla (RETURNS TABLE).
-- [9.24.1]  functions-subquery.html
--           NOT EXISTS.
-- [9.5]     functions-math.html
--           CEIL para redondear la duración hacia arriba.
-- [9.9]     functions-datetime.html
--           EXTRACT e INTERVAL.
-- =========================================================

DROP FUNCTION IF EXISTS fn_salones_disponibles(TIMESTAMP, TIMESTAMP, INTEGER);

CREATE FUNCTION fn_salones_disponibles(
    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,
    personas INTEGER
)
RETURNS TABLE (
    salon_id INTEGER,
    nombre_salon VARCHAR,
    tamano VARCHAR,
    capacidad INTEGER,
    precio_hora NUMERIC,
    costo_estimado NUMERIC
) AS $$
    SELECT
        s.id,
        s.nombre_salon,
        s.tamano,
        s.capacidad,
        s.precio_hora,
        CEIL(EXTRACT(EPOCH FROM (fecha_fin - fecha_inicio)) / 3600) * s.precio_hora
    FROM salones s
    WHERE s.habilitado = TRUE
      AND s.capacidad >= personas
      AND NOT EXISTS (
          SELECT 1
          FROM eventos e
          WHERE e.salon_id = s.id
            AND e.estado <> 'Cancelado'
            AND e.inicio < fecha_fin + INTERVAL '1 hour'
            AND e.fin + INTERVAL '1 hour' > fecha_inicio
      )
    ORDER BY s.capacidad;
$$ LANGUAGE sql;

'''-- prueba:
SELECT *
FROM fn_salones_disponibles(
    '2026-11-18 09:00',
    '2026-11-18 11:00',
    50
);'''
