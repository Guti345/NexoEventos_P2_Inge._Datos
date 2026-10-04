-- =========================================================
-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- B2. Cadena de escalamiento
-- =========================================================
-- Fuentes usadas (documentación oficial PostgreSQL 17):
-- Base: https://www.postgresql.org/docs/17/
-- [7.8.2]   queries-with.html
--           WITH RECURSIVE: término ancla + UNION ALL + término recursivo.
-- [7.8.2.2] queries-with.html
--           Protección contra ciclos mediante arreglo de visitados.
-- [36.5.10] xfunc-sql.html
--           Funciones que devuelven una tabla (RETURNS TABLE).
-- =========================================================

DROP FUNCTION IF EXISTS fn_cadena_escalamiento(INTEGER);

CREATE FUNCTION fn_cadena_escalamiento(p_staff_id INTEGER)
RETURNS TABLE (orden INTEGER, staff_id INTEGER, nombre VARCHAR, cargo VARCHAR, area VARCHAR, email VARCHAR) AS $$
    WITH RECURSIVE cadena AS (
        -- Ancla: quien reporta el incidente.
        SELECT s.id, s.nombre, s.cargo, s.area, s.email, s.jefe_id, 0 AS orden, ARRAY[s.id] AS visitados
        FROM staff s
        WHERE s.id = p_staff_id

        UNION ALL

        -- Recursivo: jefe inmediato, luego el jefe del jefe, etc.
        SELECT s.id, s.nombre, s.cargo, s.area, s.email, s.jefe_id, c.orden + 1, c.visitados || s.id
        FROM staff s JOIN cadena c ON s.id = c.jefe_id
        WHERE NOT s.id = ANY(c.visitados)
    )
    SELECT orden, id, nombre, cargo, area, email FROM cadena WHERE orden > 0 ORDER BY orden;
$$ LANGUAGE sql;

-- prueba:
-- SELECT * FROM fn_cadena_escalamiento(18);
