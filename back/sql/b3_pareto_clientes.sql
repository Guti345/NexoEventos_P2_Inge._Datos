-- =========================================================
-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- B3. Ranking de clientes y análisis de Pareto
-- =========================================================
-- Fuentes usadas (documentación oficial PostgreSQL 17):
-- Base: https://www.postgresql.org/docs/17/
-- [3.5]  tutorial-window.html
--        Funciones de ventana con OVER() y OVER(ORDER BY ...).
-- [9.22] functions-window.html
--        RANK y funciones de ventana.
-- =========================================================

DROP VIEW IF EXISTS vista_ranking_clientes;

CREATE VIEW vista_ranking_clientes AS
SELECT t.cliente_id, t.cliente, t.eventos, t.total_facturado,
       RANK() OVER (ORDER BY t.total_facturado DESC) AS posicion,
       ROUND(t.total_facturado * 100 / SUM(t.total_facturado) OVER (), 2) AS participacion,
       ROUND(SUM(t.total_facturado) OVER (ORDER BY t.total_facturado DESC, t.cliente_id) * 100 / SUM(t.total_facturado) OVER (), 2) AS acumulado,
       CASE WHEN (SUM(t.total_facturado) OVER (ORDER BY t.total_facturado DESC, t.cliente_id) - t.total_facturado) * 100 / SUM(t.total_facturado) OVER () < 80 THEN 'A' ELSE 'B' END AS segmento_pareto
FROM (
    SELECT c.id AS cliente_id, c.nombre AS cliente, COUNT(e.id) AS eventos, SUM(e.valor_total_cotizado) AS total_facturado
    FROM clientes c JOIN eventos e ON e.cliente_id = c.id
    WHERE e.estado <> 'Cancelado'
    GROUP BY c.id, c.nombre
) t;

-- prueba:
-- SELECT * FROM vista_ranking_clientes ORDER BY posicion;
