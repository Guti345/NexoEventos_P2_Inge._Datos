-- =========================================================
-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- A3. Liquidación automática del evento
-- =========================================================
-- Fuentes usadas (documentación oficial PostgreSQL 17):
-- Base: https://www.postgresql.org/docs/17/
-- [37.1]   trigger-definition.html
--          Orden de ejecución cuando existen varios triggers.
-- [41.3.5] plpgsql-declarations.html
--          Variables tipo RECORD.
-- [41.5.3] plpgsql-statements.html
--          SELECT ... INTO.
-- [41.6.4] plpgsql-control-structures.html
--          IF y CASE para la lógica condicional.
-- [41.9.1] plpgsql-errors-and-messages.html
--          RAISE EXCEPTION.
-- [41.10]  plpgsql-trigger.html
--          NEW, OLD, TG_OP; modificación de NEW en BEFORE y retorno en AFTER.
-- [9.5]    functions-math.html
--          CEIL para redondear la duración hacia arriba.
-- [9.9]    functions-datetime.html
--          EXTRACT(EPOCH FROM intervalo).
-- [9.21]   functions-aggregate.html
--          SUM para sumar los servicios contratados.
-- =========================================================

-- ---------------------------------------------------------
-- Función de apoyo: duración del evento en horas,
-- redondeada hacia arriba (por ejemplo, 3h10m = 4 horas).
-- ---------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_horas_evento(
    p_inicio TIMESTAMP,
    p_fin TIMESTAMP
)
RETURNS INTEGER AS $$
BEGIN
    RETURN CEIL(EXTRACT(EPOCH FROM (p_fin - p_inicio)) / 3600);
END;
$$ LANGUAGE plpgsql;


-- ---------------------------------------------------------
-- Función de apoyo: total de servicios contratados.
-- ---------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_total_servicios(p_evento_id INTEGER)
RETURNS NUMERIC AS $$
DECLARE
    total NUMERIC;
BEGIN
    SELECT SUM(se.cantidad * se.precio_unidad_cotizado)
    INTO total
    FROM servicios_eventos se
    WHERE se.evento_id = p_evento_id;

    IF total IS NULL THEN
        total := 0;
    END IF;

    RETURN total;
END;
$$ LANGUAGE plpgsql;


-- ---------------------------------------------------------
-- A3.1: congelar precio del salón y mantener valor total.
-- ---------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_a3_liquidar_evento()
RETURNS TRIGGER AS $$
BEGIN
    -- El precio del salón se congela al crear el evento
    -- y se vuelve a congelar si cambia de salón.
    IF TG_OP = 'INSERT' OR NEW.salon_id <> OLD.salon_id THEN
        SELECT precio_hora
        INTO NEW.precio_hora_salon_cotizado
        FROM salones
        WHERE id = NEW.salon_id;
    END IF;

    NEW.valor_total_cotizado :=
        fn_horas_evento(NEW.inicio, NEW.fin) * NEW.precio_hora_salon_cotizado
        + fn_total_servicios(NEW.id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_eventos_3_liquidacion ON eventos;

CREATE TRIGGER tr_eventos_3_liquidacion
BEFORE INSERT OR UPDATE ON eventos
FOR EACH ROW
EXECUTE FUNCTION fn_a3_liquidar_evento();


-- ---------------------------------------------------------
-- A3.2: congelar precio del servicio y completar cantidad
-- cuando la unidad de cobro permite deducirla.
-- ---------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_a3_servicio_evento()
RETURNS TRIGGER AS $$
DECLARE
    evento RECORD;
    servicio RECORD;
BEGIN
    IF TG_OP = 'DELETE' THEN
        SELECT *
        INTO evento
        FROM eventos
        WHERE id = OLD.evento_id;
    ELSE
        SELECT *
        INTO evento
        FROM eventos
        WHERE id = NEW.evento_id;
    END IF;

    IF evento.estado IN ('Finalizado', 'Cancelado') THEN
        RAISE EXCEPTION
            'SERVICIOS: El evento "%" está % y sus servicios ya no se pueden modificar.',
            evento.nombre,
            evento.estado;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    SELECT *
    INTO servicio
    FROM servicios
    WHERE id = NEW.servicio_id;

    -- Precio congelado: se toma del catálogo al contratar el servicio.
    -- Si no cambia el servicio en un UPDATE, conserva el precio histórico.
    IF TG_OP = 'INSERT' OR NEW.servicio_id <> OLD.servicio_id THEN
        NEW.precio_unidad_cotizado := servicio.precio;
    ELSE
        NEW.precio_unidad_cotizado := OLD.precio_unidad_cotizado;
    END IF;

    -- Cantidad automática únicamente cuando no fue indicada.
    IF NEW.cantidad IS NULL THEN
        CASE servicio.unidad_cobro
            WHEN 'Persona' THEN
                NEW.cantidad := evento.aforo_esperado;
            WHEN 'Hora' THEN
                NEW.cantidad := fn_horas_evento(evento.inicio, evento.fin);
            WHEN 'Unidad' THEN
                RAISE EXCEPTION
                    'SERVICIOS: El servicio "%" se cobra por unidad y requiere una cantidad explícita.',
                    servicio.nombre_servicio;
        END CASE;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_servicios_eventos_1_contratar ON servicios_eventos;

CREATE TRIGGER tr_servicios_eventos_1_contratar
BEFORE INSERT OR UPDATE OR DELETE ON servicios_eventos
FOR EACH ROW
EXECUTE FUNCTION fn_a3_servicio_evento();


-- ---------------------------------------------------------
-- A3.3: después de agregar, modificar o quitar un servicio,
-- actualizar el total persistido del evento.
-- ---------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_a3_actualizar_total()
RETURNS TRIGGER AS $$
DECLARE
    id_evento INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        id_evento := OLD.evento_id;
    ELSE
        id_evento := NEW.evento_id;
    END IF;

    UPDATE eventos
    SET valor_total_cotizado =
        fn_horas_evento(inicio, fin) * precio_hora_salon_cotizado
        + fn_total_servicios(id)
    WHERE id = id_evento;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_servicios_eventos_2_total ON servicios_eventos;
