-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- A5: salones disponibles para un horario y un número de personas, del más pequeño al más grande
--
-- Referencias (documentación oficial PostgreSQL 17, https://www.postgresql.org/docs/17/):
--   [8.5]     datatype-datetime.html    TIMESTAMP = fecha + hora (ej. '2026-11-18 09:00')
--   [36.5.10] xfunc-sql.html            Funciones que devuelven una tabla (RETURNS TABLE)
--   [9.24.1]  functions-subquery.html   NOT EXISTS

DROP FUNCTION IF EXISTS fn_salones_disponibles(TIMESTAMP, TIMESTAMP, INTEGER);

-- Recibe: fecha y hora de inicio, fecha y hora de fin, número de personas
-- Devuelve: una tabla con los salones libres y lo que costarían
CREATE FUNCTION fn_salones_disponibles(fecha_inicio TIMESTAMP, fecha_fin TIMESTAMP, personas INTEGER)
RETURNS TABLE (salon_id INTEGER, nombre VARCHAR, tamano VARCHAR, capacidad INTEGER,
               precio_hora NUMERIC, costo_estimado NUMERIC) AS $$
  SELECT s.id, s.nombre, s.tamano, s.capacidad, s.precio_hora,
         fn_horas_evento(fecha_inicio, fecha_fin) * s.precio_hora   -- horas x precio por hora
  FROM salones s
  WHERE s.activo = TRUE              -- 1. el salón no está en mantenimiento
    AND s.capacidad >= personas      -- 2. caben las personas
    AND NOT EXISTS (                 -- 3. no hay ningún evento que se cruce (Doc 9.24.1)
      SELECT 1
      FROM eventos e
      WHERE e.salon_id = s.id
        AND e.estado <> 'Cancelado'
        AND e.inicio < fecha_fin + INTERVAL '1 hour'      -- el otro empieza antes de que yo termine + 1 h de montaje
        AND e.fin + INTERVAL '1 hour' > fecha_inicio      -- y termina (+ 1 h de montaje) después de que yo empiezo
    )
  ORDER BY s.capacidad;              -- del más pequeño que sirva al más grande
$$ LANGUAGE sql;

-- prueba: SELECT * FROM fn_salones_disponibles('2026-11-18 09:00', '2026-11-18 11:00', 50);
