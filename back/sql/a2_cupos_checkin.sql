-- =========================================================
-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- A2. Cupos y asistencia real
-- =========================================================
-- Fuentes usadas (documentación oficial PostgreSQL 17):
-- Base: https://www.postgresql.org/docs/17/
-- [41.3.5] plpgsql-declarations.html
--          Variables tipo RECORD.
-- [41.5.3] plpgsql-statements.html
--          SELECT ... INTO.
-- [41.9.1] plpgsql-errors-and-messages.html
--          RAISE EXCEPTION.
-- [41.10]  plpgsql-trigger.html
--          NEW, OLD, TG_OP y funciones de trigger.
-- [9.8]    functions-formatting.html
--          to_char para mostrar fechas y horas en mensajes.
-- [9.9]    functions-datetime.html
--          INTERVAL para la ventana de check-in.
-- [9.21]   functions-aggregate.html
--          COUNT para validar el cupo contratado.
-- =========================================================

CREATE OR REPLACE FUNCTION fn_a2_inscripcion_checkin()
RETURNS TRIGGER AS $$
DECLARE
    evento RECORD;
    inscritos INTEGER;
BEGIN
    SELECT *
    INTO evento
    FROM eventos
    WHERE id = NEW.evento_id;

    -- Validaciones al crear una inscripción.
    IF TG_OP = 'INSERT' THEN
        IF evento.estado IN ('Cancelado', 'Finalizado') THEN
            RAISE EXCEPTION
                'INSCRIPCION: El evento "%" está % y no recibe inscripciones.',
                evento.nombre,
                evento.estado;
        END IF;

        SELECT COUNT(*)
        INTO inscritos
        FROM inscripciones
        WHERE evento_id = NEW.evento_id;

        IF inscritos >= evento.aforo_esperado THEN
            RAISE EXCEPTION
                'CUPO: El evento "%" alcanzó su aforo contratado (% personas).',
                evento.nombre,
                evento.aforo_esperado;
        END IF;
    END IF;

    -- Si ya existe una fecha de check-in, no se permite registrarla de nuevo.
    IF TG_OP = 'UPDATE' AND OLD.fecha_checkin IS NOT NULL THEN
        RAISE EXCEPTION
            'CHECK-IN: Este asistente ya registró su llegada el %.',
            to_char(OLD.fecha_checkin, 'YYYY-MM-DD HH24:MI');
    END IF;

    -- Si se está registrando una llegada, se valida estado y ventana horaria.
    IF NEW.fecha_checkin IS NOT NULL THEN
        IF evento.estado <> 'Confirmado' THEN
            RAISE EXCEPTION
                'CHECK-IN: El evento "%" está %; solo se registra llegada en eventos confirmados.',
                evento.nombre,
                evento.estado;
        END IF;

        IF NEW.fecha_checkin < evento.inicio - INTERVAL '1 hour'
           OR NEW.fecha_checkin > evento.fin THEN
            RAISE EXCEPTION
                'CHECK-IN: Solo se permite ingresar entre % y % (hora indicada: %).',
                to_char(evento.inicio - INTERVAL '1 hour', 'YYYY-MM-DD HH24:MI'),
                to_char(evento.fin, 'YYYY-MM-DD HH24:MI'),
                to_char(NEW.fecha_checkin, 'YYYY-MM-DD HH24:MI');
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_inscripciones_cupo_checkin ON inscripciones;

CREATE TRIGGER tr_inscripciones_cupo_checkin
BEFORE INSERT OR UPDATE ON inscripciones
FOR EACH ROW
EXECUTE FUNCTION fn_a2_inscripcion_checkin();