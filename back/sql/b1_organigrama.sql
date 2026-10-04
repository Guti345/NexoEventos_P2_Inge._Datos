-- =========================================================
-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- B1. Organigrama
-- =========================================================
-- Fuentes usadas (documentación oficial PostgreSQL 17):
-- Base: https://www.postgresql.org/docs/17/
-- [7.8.2]   queries-with.html
--           WITH RECURSIVE: término ancla + UNION ALL + término recursivo.
-- [7.8.2.2] queries-with.html
--           Protección contra ciclos mediante arreglo de visitados.
-- [36.5.10] xfunc-sql.html
--           Funciones que devuelven una tabla (RETURNS TABLE).
-- [9.21]    functions-aggregate.html
--           COUNT para calcular personas a cargo.
-- =========================================================

DROP FUNCTION IF EXISTS fn_organigrama(INTEGER);

CREATE FUNCTION fn_organigrama(p_staff_id INTEGER)
RETURNS TABLE (staff_id INTEGER, nombre VARCHAR, cargo VARCHAR, area VARCHAR, jefe_id INTEGER, nivel INTEGER, ruta_mando TEXT, personas_a_cargo BIGINT) AS $$
    WITH RECURSIVE org AS (
        -- Miembro ancla: la persona pedida o quienes no tienen jefe.
        SELECT s.id, s.nombre, s.cargo, s.area, s.jefe_id, 1 AS nivel, s.nombre::TEXT AS ruta, ARRAY[s.id] AS visitados
        FROM staff s
        WHERE (p_staff_id IS NULL AND s.jefe_id IS NULL) OR s.id = p_staff_id

        UNION ALL

        -- Miembro recursivo: subordinados directos del nivel anterior.
        SELECT s.id, s.nombre, s.cargo, s.area, s.jefe_id, o.nivel + 1, o.ruta || ' > ' || s.nombre || ' (' || s.cargo || ')', o.visitados || s.id
        FROM staff s JOIN org o ON s.jefe_id = o.id
        WHERE NOT s.id = ANY(o.visitados)
    )
    SELECT o.id, o.nombre, o.cargo, o.area, o.jefe_id, o.nivel, o.ruta,
           (SELECT COUNT(*) FROM org x WHERE o.id = ANY(x.visitados) AND x.id <> o.id)
    FROM org o
    ORDER BY o.ruta;
$$ LANGUAGE sql;

-- pruebas:
-- SELECT * FROM fn_organigrama(NULL);
-- SELECT * FROM fn_organigrama(2);
