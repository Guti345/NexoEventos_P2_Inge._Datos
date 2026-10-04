-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- Módulo B: reportes (CTE recursivas y funciones de ventana)
--
-- Referencias (documentación oficial PostgreSQL 17, https://www.postgresql.org/docs/17/):
--   [7.8.2]   queries-with.html        WITH RECURSIVE (ancla + UNION ALL + recursivo)
--   [7.8.2.2] queries-with.html        Protección contra ciclos con un arreglo de visitados
--   [3.5]     tutorial-window.html     Funciones de ventana: OVER (), PARTITION BY, ORDER BY
--   [9.22]    functions-window.html    ROW_NUMBER, RANK, LAG
--   [36.5.10] xfunc-sql.html           Funciones que devuelven TABLE
-- Se borran antes de crearlas para poder cambiar sus columnas sin error.

DROP FUNCTION IF EXISTS fn_organigrama(INTEGER);
DROP FUNCTION IF EXISTS fn_cadena_escalamiento(INTEGER);
DROP VIEW IF EXISTS vista_ranking_clientes;
DROP VIEW IF EXISTS vista_ocupacion_salones;


-- ============ B1: Organigrama (CTE recursiva) ============
-- Sin staff_id (NULL) arranca desde la directora general
CREATE FUNCTION fn_organigrama(p_staff_id INTEGER)
RETURNS TABLE (staff_id INTEGER, nombre VARCHAR, cargo VARCHAR, nivel INTEGER,
               ruta_mando TEXT, personas_a_cargo BIGINT) AS $$
  WITH RECURSIVE org AS (
    -- Miembro ancla: la persona pedida, o quien no tiene jefe
    SELECT s.id, s.nombre, s.cargo, 1 AS nivel,
           CAST(s.nombre AS TEXT) AS ruta, ARRAY[s.id] AS visitados
    FROM staff s
    WHERE (p_staff_id IS NULL AND s.jefe_id IS NULL) OR s.id = p_staff_id

    UNION ALL

    -- Miembro recursivo: los subordinados del nivel anterior
    SELECT s.id, s.nombre, s.cargo, o.nivel + 1,
           o.ruta || ' > ' || s.nombre, o.visitados || s.id
    FROM staff s
    JOIN org o ON s.jefe_id = o.id
    WHERE NOT s.id = ANY(o.visitados)   -- Doc 7.8.2.2: si ya pasó por esa persona hay un ciclo, se detiene
  )
  -- Personas a cargo = cuántos tienen una ruta que empieza por la ruta de esta persona
  SELECT o.id, o.nombre, o.cargo, o.nivel, o.ruta,
         (SELECT COUNT(*) FROM org x WHERE x.ruta LIKE o.ruta || ' > %')
  FROM org o
  ORDER BY o.ruta;
$$ LANGUAGE sql;

-- prueba: SELECT * FROM fn_organigrama(NULL);  SELECT * FROM fn_organigrama(2);


-- ============ B2: Cadena de escalamiento (CTE recursiva) ============
-- Igual que B1 pero al revés: en vez de bajar a los subordinados, sube al jefe
CREATE FUNCTION fn_cadena_escalamiento(p_staff_id INTEGER)
RETURNS TABLE (orden INTEGER, staff_id INTEGER, nombre VARCHAR, cargo VARCHAR, correo VARCHAR) AS $$
  WITH RECURSIVE cadena AS (
    -- Ancla: quien reporta el incidente (orden 0)
    SELECT s.id, s.nombre, s.cargo, s.correo, s.jefe_id, 0 AS orden, ARRAY[s.id] AS visitados
    FROM staff s
    WHERE s.id = p_staff_id

    UNION ALL

    -- Recursivo: su jefe inmediato, luego el jefe del jefe...
    SELECT s.id, s.nombre, s.cargo, s.correo, s.jefe_id, c.orden + 1, c.visitados || s.id
    FROM staff s
    JOIN cadena c ON s.id = c.jefe_id
    WHERE NOT s.id = ANY(c.visitados)   -- Doc 7.8.2.2: protección contra ciclos
  )
  SELECT orden, id, nombre, cargo, correo
  FROM cadena
  WHERE orden > 0   -- solo los jefes, no la persona que reporta
  ORDER BY orden;
$$ LANGUAGE sql;

-- prueba: SELECT * FROM fn_cadena_escalamiento(18);


-- ============ B3: Ranking de clientes y Pareto (funciones de ventana) ============
-- Paso 1 (t): total por cliente | Paso 2 (r): ranking y porcentajes | Paso 3: segmento
-- Doc 3.5: SUM() OVER () = gran total de todas las filas
--          SUM() OVER (ORDER BY ...) = acumulado "from the start ... up through the current row"
CREATE VIEW vista_ranking_clientes AS
SELECT r.*,
       CASE WHEN r.acumulado - r.participacion < 80 THEN 'A' ELSE 'B' END AS segmento_pareto
FROM (
  SELECT t.cliente_id, t.cliente, t.eventos, t.total_facturado,
         RANK() OVER (ORDER BY t.total_facturado DESC) AS posicion,
         ROUND(t.total_facturado * 100 / SUM(t.total_facturado) OVER (), 2) AS participacion,
         ROUND(SUM(t.total_facturado) OVER (ORDER BY t.total_facturado DESC, t.cliente_id) * 100
               / SUM(t.total_facturado) OVER (), 2) AS acumulado
  FROM (
    SELECT c.id AS cliente_id, c.nombre AS cliente, COUNT(e.id) AS eventos, SUM(e.valor_total) AS total_facturado
    FROM clientes c
    JOIN eventos e ON e.cliente_id = c.id
    WHERE e.estado <> 'Cancelado'
    GROUP BY c.id, c.nombre
  ) t
) r;
-- Segmento A: el cliente entra cuando lo acumulado ANTES de él (acumulado - su participación) aún no llega al 80 %

-- prueba: SELECT * FROM vista_ranking_clientes ORDER BY posicion;


-- ============ B4: Ocupación de salones y tiempos muertos (funciones de ventana) ============
-- Paso 1 (t): por salón y en orden de fecha, número, evento anterior, fin anterior y horas acumuladas
-- Paso 2: días libres = inicio del evento - fin del anterior
-- Doc 9.22: ROW_NUMBER() cuenta "within its partition, counting from 1"; LAG() trae la fila anterior
CREATE VIEW vista_ocupacion_salones AS
SELECT t.salon_id, t.salon, t.evento_id, t.evento, t.inicio, t.fin,
       t.numero_en_salon, t.evento_anterior,
       ROUND(EXTRACT(EPOCH FROM (t.inicio - t.fin_anterior)) / 86400, 2) AS dias_libres,   -- 86400 s = 1 día
       t.horas_acumuladas
FROM (
  SELECT s.id AS salon_id, s.nombre AS salon, e.id AS evento_id, e.nombre AS evento, e.inicio, e.fin,
         ROW_NUMBER() OVER (PARTITION BY s.id ORDER BY e.inicio) AS numero_en_salon,
         LAG(e.nombre) OVER (PARTITION BY s.id ORDER BY e.inicio) AS evento_anterior,
         LAG(e.fin) OVER (PARTITION BY s.id ORDER BY e.inicio) AS fin_anterior,
         SUM(fn_horas_evento(e.inicio, e.fin)) OVER (PARTITION BY s.id ORDER BY e.inicio) AS horas_acumuladas
  FROM salones s
  JOIN eventos e ON e.salon_id = s.id
  WHERE e.estado <> 'Cancelado'
) t;

-- prueba: SELECT * FROM vista_ocupacion_salones ORDER BY salon_id, numero_en_salon;-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- Módulo B: reportes de inteligencia de negocio (CTE recursivas y funciones de ventana)


-- ============ B1: Organigrama (CTE recursiva) ============
-- Sin staff_id (NULL) arranca desde la dirección general
CREATE OR REPLACE FUNCTION fn_organigrama(p_staff_id INTEGER)
RETURNS TABLE (staff_id INTEGER, nombre VARCHAR, cargo VARCHAR, area VARCHAR, jefe_id INTEGER,
               nivel INTEGER, ruta_mando TEXT, personas_a_cargo BIGINT) AS $$
  WITH RECURSIVE org AS (
    -- Miembro ancla: la persona pedida, o quien no tiene jefe
    SELECT s.id, s.nombre, s.cargo, s.area, s.jefe_id, 1 AS nivel,
           s.nombre::TEXT AS ruta, ARRAY[s.id] AS visitados
    FROM staff s
    WHERE (p_staff_id IS NULL AND s.jefe_id IS NULL) OR s.id = p_staff_id

    UNION ALL

    -- Miembro recursivo: los subordinados directos del nivel anterior
    SELECT s.id, s.nombre, s.cargo, s.area, s.jefe_id, o.nivel + 1,
           o.ruta || ' > ' || s.nombre, o.visitados || s.id
    FROM staff s
    JOIN org o ON s.jefe_id = o.id
    WHERE NOT s.id = ANY(o.visitados)  -- protección contra ciclos (doc PostgreSQL 7.8.2.2)
  )
  -- Personas a cargo = filas cuyo camino pasa por esta persona (sin contarla a ella)
  SELECT o.id, o.nombre, o.cargo, o.area, o.jefe_id, o.nivel, o.ruta,
         (SELECT COUNT(*) FROM org x WHERE o.id = ANY(x.visitados) AND x.id <> o.id)
  FROM org o
  ORDER BY o.ruta;
$$ LANGUAGE sql;

-- prueba: SELECT * FROM fn_organigrama(NULL);  SELECT * FROM fn_organigrama(2);


-- ============ B2: Cadena de escalamiento (CTE recursiva) ============
CREATE OR REPLACE FUNCTION fn_cadena_escalamiento(p_staff_id INTEGER)
RETURNS TABLE (orden INTEGER, staff_id INTEGER, nombre VARCHAR, cargo VARCHAR,
               area VARCHAR, correo VARCHAR) AS $$
  WITH RECURSIVE cadena AS (
    -- Ancla: quien reporta el incidente
    SELECT s.id, s.nombre, s.cargo, s.area, s.correo, s.jefe_id, 0 AS orden, ARRAY[s.id] AS visitados
    FROM staff s
    WHERE s.id = p_staff_id

    UNION ALL

    -- Recursivo: sube al jefe inmediato
    SELECT s.id, s.nombre, s.cargo, s.area, s.correo, s.jefe_id, c.orden + 1, c.visitados || s.id
    FROM staff s
    JOIN cadena c ON s.id = c.jefe_id
    WHERE NOT s.id = ANY(c.visitados)
  )
  SELECT orden, id, nombre, cargo, area, correo
  FROM cadena
  WHERE orden > 0
  ORDER BY orden;
$$ LANGUAGE sql;

-- prueba: SELECT * FROM fn_cadena_escalamiento(18);


-- ============ B3: Ranking de clientes y Pareto ============
-- SUM() OVER () = gran total | SUM() OVER (ORDER BY ...) = acumulado fila a fila
-- Segmento A: clientes que entran antes de completar el 80 % de la facturación
CREATE OR REPLACE VIEW vista_ranking_clientes AS
SELECT t.cliente_id, t.cliente, t.eventos, t.total_facturado,
       RANK() OVER (ORDER BY t.total_facturado DESC) AS posicion,
       ROUND(t.total_facturado * 100 / SUM(t.total_facturado) OVER (), 2) AS participacion,
       ROUND(SUM(t.total_facturado) OVER (ORDER BY t.total_facturado DESC, t.cliente_id) * 100
             / SUM(t.total_facturado) OVER (), 2) AS acumulado,
       CASE
         WHEN (SUM(t.total_facturado) OVER (ORDER BY t.total_facturado DESC, t.cliente_id) - t.total_facturado) * 100
              / SUM(t.total_facturado) OVER () < 80 THEN 'A'
         ELSE 'B'
       END AS segmento_pareto
FROM (
  SELECT c.id AS cliente_id, c.nombre AS cliente, COUNT(e.id) AS eventos, SUM(e.valor_total) AS total_facturado
  FROM clientes c
  JOIN eventos e ON e.cliente_id = c.id
  WHERE e.estado <> 'Cancelado'
  GROUP BY c.id, c.nombre
) t;

-- prueba: SELECT * FROM vista_ranking_clientes ORDER BY posicion;


-- ============ B4: Ocupación de salones y tiempos muertos (funciones de ventana) ============
CREATE OR REPLACE VIEW vista_ocupacion_salones AS
SELECT s.id AS salon_id, s.nombre AS salon, e.id AS evento_id, e.nombre AS evento, e.inicio, e.fin,
       ROW_NUMBER() OVER (PARTITION BY s.id ORDER BY e.inicio) AS numero_en_salon,
       LAG(e.nombre) OVER (PARTITION BY s.id ORDER BY e.inicio) AS evento_anterior,
       ROUND(EXTRACT(EPOCH FROM (e.inicio - LAG(e.fin) OVER (PARTITION BY s.id ORDER BY e.inicio))) / 86400, 2) AS dias_libres,
       ROUND(SUM(EXTRACT(EPOCH FROM (e.fin - e.inicio)) / 3600) OVER (PARTITION BY s.id ORDER BY e.inicio), 2) AS horas_acumuladas
FROM salones s
JOIN eventos e ON e.salon_id = s.id
WHERE e.estado <> 'Cancelado';

-- prueba: SELECT * FROM vista_ocupacion_salones ORDER BY salon_id, numero_en_salon;
