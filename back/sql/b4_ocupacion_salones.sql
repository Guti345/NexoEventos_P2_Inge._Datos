-- =========================================================
-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- B4. Ocupación de salones y tiempos muertos
-- =========================================================
-- Fuentes usadas (documentación oficial PostgreSQL 17):
-- Base: https://www.postgresql.org/docs/17/
-- [3.5]  tutorial-window.html
--        OVER(), PARTITION BY y ORDER BY en funciones de ventana.
-- [9.22] functions-window.html
--        ROW_NUMBER y LAG.
-- [9.9]  functions-datetime.html
--        EXTRACT(EPOCH FROM intervalo) para convertir intervalos a segundos.
-- =========================================================

DROP VIEW IF EXISTS vista_ocupacion_salones;

CREATE VIEW vista_ocupacion_salones AS
SELECT
    s.id AS salon_id,
    s.nombre_salon AS salon,
    e.id AS evento_id,
    e.nombre AS evento,
    e.inicio,
    e.fin,
    ROW_NUMBER() OVER (
        PARTITION BY s.id
        ORDER BY e.inicio
    ) AS numero_en_salon,
    LAG(e.nombre) OVER (
        PARTITION BY s.id
        ORDER BY e.inicio
    ) AS evento_anterior,
    ROUND(
        EXTRACT(
            EPOCH FROM (
                e.inicio
                - LAG(e.fin) OVER (
                    PARTITION BY s.id
                    ORDER BY e.inicio
                )
            )
        ) / 86400,
        2
    ) AS dias_libres,
    ROUND(
        SUM(
            EXTRACT(EPOCH FROM (e.fin - e.inicio)) / 3600
        ) OVER (
            PARTITION BY s.id
            ORDER BY e.inicio
        ),
        2
    ) AS horas_acumuladas
FROM salones s
JOIN eventos e
    ON e.salon_id = s.id
WHERE e.estado <> 'Cancelado';

'''-- prueba:
SELECT *
FROM vista_ocupacion_salones
ORDER BY salon_id, numero_en_salon;
'''
