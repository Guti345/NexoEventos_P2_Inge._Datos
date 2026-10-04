-- =========================================================
-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- A1. Disponibilidad y capacidad del salón
-- =========================================================
-- Fuentes usadas (documentación oficial PostgreSQL 17):
-- Base: https://www.postgresql.org/docs/17/
-- [37.1]   trigger-definition.html
--          Definición y orden de ejecución de triggers.
-- [41.3.5] plpgsql-declarations.html
--          Variables tipo RECORD.
-- [41.5.3] plpgsql-statements.html
--          SELECT ... INTO.
-- [41.5.5] plpgsql-statements.html
--          Variable FOUND después de SELECT ... INTO.
-- [41.9.1] plpgsql-errors-and-messages.html
--          RAISE EXCEPTION.
-- [41.10]  plpgsql-trigger.html
--          NEW, OLD, TG_OP y funciones de trigger.
-- [9.8]    functions-formatting.html
--          to_char para mostrar fechas y horas en mensajes.
-- [9.9]    functions-datetime.html
--          INTERVAL y operaciones con TIMESTAMP.
-- [9.21]   functions-aggregate.html
--          COUNT para validar inscritos al reducir el aforo.
-- =========================================================

CREATE OR REPLACE FUNCTION fn_a1_disponibilidad_salon()
RETURNS TRIGGER AS $$
DECLARE
    salon RECORD;
    cruce RECORD;
    inscritos INTEGER;
BEGIN
    -- Un evento cancelado libera el salón.
    IF NEW.estado = 'Cancelado' THEN RETURN NEW; END IF;

    -- En UPDATE solo se vuelve a validar si cambió salón, horario o aforo, o si el evento venía de estar cancelado.
    IF TG_OP = 'UPDATE' AND NEW.salon_id = OLD.salon_id AND NEW.inicio = OLD.inicio AND NEW.fin = OLD.fin AND NEW.aforo_esperado = OLD.aforo_esperado AND OLD.estado <> 'Cancelado' THEN
        RETURN NEW;
    END IF;

    SELECT * INTO salon FROM salones WHERE id = NEW.salon_id;

    -- Si no existe, la ForeignKey se encargará de rechazar la operación.
    IF NOT FOUND THEN RETURN NEW; END IF;

    IF NOT salon.habilitado THEN
        RAISE EXCEPTION 'SALON INACTIVO: El salón "%" está deshabilitado temporalmente.', salon.nombre_salon;
    END IF;

    IF NEW.aforo_esperado > salon.capacidad THEN
        RAISE EXCEPTION 'CAPACIDAD: El aforo esperado (% personas) supera la capacidad del salón "%" (% personas).', NEW.aforo_esperado, salon.nombre_salon, salon.capacidad;
    END IF;

    -- Cruce con otro evento no cancelado del mismo salón, dejando por lo menos 1 hora libre entre eventos.
    SELECT e.id, e.nombre, e.inicio, e.fin INTO cruce FROM eventos e
    WHERE e.salon_id = NEW.salon_id AND (TG_OP = 'INSERT' OR e.id <> NEW.id) AND e.estado <> 'Cancelado'
      AND e.inicio < NEW.fin + INTERVAL '1 hour' AND e.fin + INTERVAL '1 hour' > NEW.inicio
    ORDER BY e.inicio LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION 'DISPONIBILIDAD: El salón "%" se cruza con el evento % "%" (% a %). Se requiere 1 hora libre entre eventos.',
            salon.nombre_salon, cruce.id, cruce.nombre, to_char(cruce.inicio, 'YYYY-MM-DD HH24:MI'), to_char(cruce.fin, 'YYYY-MM-DD HH24:MI');
    END IF;

    -- Al reducir el aforo, este no puede quedar por debajo del número de personas que ya están inscritas.
    IF TG_OP = 'UPDATE' THEN
        SELECT COUNT(*) INTO inscritos FROM inscripciones WHERE evento_id = NEW.id;
        IF NEW.aforo_esperado < inscritos THEN
            RAISE EXCEPTION 'CUPO: El evento "%" ya tiene % inscritos; el aforo no puede bajar a %.', NEW.nombre, inscritos, NEW.aforo_esperado;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_eventos_2_disponibilidad ON eventos;
CREATE TRIGGER tr_eventos_2_disponibilidad BEFORE INSERT OR UPDATE ON eventos FOR EACH ROW EXECUTE FUNCTION fn_a1_disponibilidad_salon();
