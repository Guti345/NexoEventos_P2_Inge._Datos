-- =========================================================
-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- A4. Cierre del evento y auditoría
-- =========================================================
-- Fuentes usadas (documentación oficial PostgreSQL 17):
-- Base: https://www.postgresql.org/docs/17/
-- [37.1]   trigger-definition.html
--          Orden de ejecución de triggers sobre la misma relación.
-- [41.5.3] plpgsql-statements.html
--          SELECT ... INTO.
-- [41.9.1] plpgsql-errors-and-messages.html
--          RAISE EXCEPTION.
-- [41.10]  plpgsql-trigger.html
--          NEW, OLD, TG_OP y funciones BEFORE/AFTER.
-- [9.5]    functions-math.html
--          ROUND para la tasa de asistencia.
-- [9.8]    functions-formatting.html
--          to_char para serializar fechas en la auditoría.
-- [9.9]    functions-datetime.html
--          now() para fecha/hora de cierre y auditoría.
-- [9.21]   functions-aggregate.html
--          COUNT y COUNT(columna) para inscritos y asistentes reales.
-- [9.28.1] functions-admin.html
--          current_setting para recuperar app.usuario definido por la API.
-- =========================================================

-- ---------------------------------------------------------
-- A4.1: control de estados y cálculo de tasa al finalizar.
-- ---------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_a4_control_estado()
RETURNS TRIGGER AS $$
DECLARE
    inscritos INTEGER;
    llegaron INTEGER;
BEGIN
    -- Todo evento nace como Cotizado.
    IF TG_OP = 'INSERT' THEN
        IF NEW.estado <> 'Cotizado' THEN
            RAISE EXCEPTION 'ESTADO: Todo evento nace como Cotizado (se recibió "%").', NEW.estado;
        END IF;
        RETURN NEW;
    END IF;

    -- Finalizado y Cancelado son estados definitivos.
    IF OLD.estado IN ('Finalizado', 'Cancelado') THEN
        RAISE EXCEPTION 'ESTADO: El evento "%" está % y ya no admite cambios.', OLD.nombre, OLD.estado;
    END IF;

    IF NEW.estado <> OLD.estado THEN
        IF NOT ((OLD.estado = 'Cotizado' AND NEW.estado IN ('Confirmado', 'Cancelado')) OR (OLD.estado = 'Confirmado' AND NEW.estado IN ('Finalizado', 'Cancelado'))) THEN
            RAISE EXCEPTION 'ESTADO: No se puede pasar un evento de % a %.', OLD.estado, NEW.estado;
        END IF;

        IF NEW.estado = 'Finalizado' THEN
            IF NEW.fin > now() THEN
                RAISE EXCEPTION 'CIERRE: El evento "%" termina el % y solo se puede finalizar después de esa hora.', NEW.nombre, to_char(NEW.fin, 'YYYY-MM-DD HH24:MI');
            END IF;

            SELECT COUNT(*), COUNT(fecha_checkin) INTO inscritos, llegaron FROM inscripciones WHERE evento_id = NEW.id;
            IF inscritos = 0 THEN NEW.tasa_asistencia := NULL; ELSE NEW.tasa_asistencia := ROUND(llegaron * 100.0 / inscritos, 2); END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_eventos_1_estado ON eventos;
CREATE TRIGGER tr_eventos_1_estado BEFORE INSERT OR UPDATE ON eventos FOR EACH ROW EXECUTE FUNCTION fn_a4_control_estado();

-- ---------------------------------------------------------
-- A4.2: auditoría de cambios de estado, salón e intervalo.
-- La API debe haber ejecutado previamente:
--   SELECT set_config('app.usuario', :usuario, true);
-- ---------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_a4_auditoria_evento()
RETURNS TRIGGER AS $$
DECLARE
    usuario_app VARCHAR;
BEGIN
    usuario_app := current_setting('app.usuario', true);
    IF usuario_app IS NULL OR usuario_app = '' THEN usuario_app := current_user; END IF;

    IF OLD.estado <> NEW.estado THEN
        INSERT INTO trazabilidad (evento_id, campo_modificado, valor_anterior, valor_nuevo, fecha_hora, usuario)
        VALUES (NEW.id, 'estado', OLD.estado, NEW.estado, now(), usuario_app);
    END IF;

    IF OLD.salon_id <> NEW.salon_id THEN
        INSERT INTO trazabilidad (evento_id, campo_modificado, valor_anterior, valor_nuevo, fecha_hora, usuario)
        VALUES (NEW.id, 'salon_id', OLD.salon_id::TEXT, NEW.salon_id::TEXT, now(), usuario_app);
    END IF;

    IF OLD.inicio <> NEW.inicio THEN
        INSERT INTO trazabilidad (evento_id, campo_modificado, valor_anterior, valor_nuevo, fecha_hora, usuario)
        VALUES (NEW.id, 'inicio', to_char(OLD.inicio, 'YYYY-MM-DD HH24:MI'), to_char(NEW.inicio, 'YYYY-MM-DD HH24:MI'), now(), usuario_app);
    END IF;

    IF OLD.fin <> NEW.fin THEN
        INSERT INTO trazabilidad (evento_id, campo_modificado, valor_anterior, valor_nuevo, fecha_hora, usuario)
        VALUES (NEW.id, 'fin', to_char(OLD.fin, 'YYYY-MM-DD HH24:MI'), to_char(NEW.fin, 'YYYY-MM-DD HH24:MI'), now(), usuario_app);
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_eventos_4_auditoria ON eventos;
CREATE TRIGGER tr_eventos_4_auditoria AFTER UPDATE ON eventos FOR EACH ROW EXECUTE FUNCTION fn_a4_auditoria_evento();
