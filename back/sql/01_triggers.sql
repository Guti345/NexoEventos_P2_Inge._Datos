-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- Módulo A: triggers A1 a A4. Se aplica después de create_all y se puede correr varias veces.
--
-- Referencias (documentación oficial PostgreSQL 17, https://www.postgresql.org/docs/17/):
--   [37.1]   trigger-definition.html              Comportamiento de los triggers (orden de disparo)
--   [41.3.5] plpgsql-declarations.html            Variables tipo RECORD
--   [41.5.3] plpgsql-statements.html              SELECT ... INTO
--   [41.5.5] plpgsql-statements.html              Variable FOUND
--   [41.6.4] plpgsql-control-structures.html      IF y CASE
--   [41.9.1] plpgsql-errors-and-messages.html     RAISE EXCEPTION
--   [41.10]  plpgsql-trigger.html                 Funciones de trigger: NEW, OLD, TG_OP, valor de retorno
--   [9.5]    functions-math.html                  CEIL y ROUND
--   [9.8]    functions-formatting.html            to_char
--   [9.9]    functions-datetime.html              EXTRACT, INTERVAL, now()
--   [9.21]   functions-aggregate.html             COUNT
--   [9.28.1] functions-admin.html                 set_config y current_setting
--
-- Doc 37.1: "If more than one trigger is defined for the same event on the same relation,
-- the triggers will be fired in alphabetical order by trigger name."
-- Por eso los triggers de eventos se numeran: 1 estado, 2 disponibilidad, 3 liquidación, 4 auditoría, 5 servicios.


-- ============ Funciones de apoyo ============

-- Horas del evento redondeadas hacia arriba (3h10m = 4h)
CREATE OR REPLACE FUNCTION fn_horas_evento(p_inicio TIMESTAMP, p_fin TIMESTAMP)
RETURNS INTEGER AS $$
BEGIN
  -- Doc 9.9.1: EXTRACT(EPOCH FROM intervalo) = "the total number of seconds in the interval"
  -- Doc 9.5: CEIL = "nearest integer greater than or equal to argument"
  RETURN CEIL(EXTRACT(EPOCH FROM (p_fin - p_inicio)) / 3600);
END;
$$ LANGUAGE plpgsql;

-- Suma de los servicios contratados de un evento
CREATE OR REPLACE FUNCTION fn_total_servicios(p_evento_id INTEGER)
RETURNS NUMERIC AS $$
DECLARE
  -- Definición de variables
  total NUMERIC;
BEGIN
  -- Lógica
  SELECT SUM(s.cantidad * s.precio_unitario) INTO total   -- Doc 41.5.3: SELECT ... INTO guarda el resultado en la variable
  FROM evento_servicios s
  WHERE s.evento_id = p_evento_id;

  IF total IS NULL THEN   -- SUM de cero filas da NULL
    total := 0;
  END IF;
  RETURN total;
END;
$$ LANGUAGE plpgsql;


-- ============ A4 (parte 1): estados del evento y cierre ============

CREATE OR REPLACE FUNCTION fn_a4_control_estado()
RETURNS TRIGGER AS $$
DECLARE
  -- Definición de variables
  inscritos INTEGER;
  llegaron INTEGER;
BEGIN
  -- Lógica
  -- Doc 41.10: TG_OP = "operation for which the trigger was fired: INSERT, UPDATE, DELETE, or TRUNCATE"
  IF TG_OP = 'INSERT' THEN
    IF NEW.estado <> 'Cotizado' THEN
      -- Doc 41.9.1: cada % se reemplaza por el siguiente argumento; sin código, el error es P0001
      RAISE EXCEPTION 'ESTADO: Todo evento nace como Cotizado (se recibió "%").', NEW.estado;
    END IF;
    RETURN NEW;
  END IF;

  -- Finalizado y Cancelado son definitivos
  IF OLD.estado IN ('Finalizado', 'Cancelado') THEN
    RAISE EXCEPTION 'ESTADO: El evento "%" está % y ya no admite cambios.', OLD.nombre, OLD.estado;
  END IF;

  IF NEW.estado <> OLD.estado THEN
    IF NOT ((OLD.estado = 'Cotizado' AND NEW.estado IN ('Confirmado', 'Cancelado'))
         OR (OLD.estado = 'Confirmado' AND NEW.estado IN ('Finalizado', 'Cancelado'))) THEN
      RAISE EXCEPTION 'ESTADO: No se puede pasar un evento de % a %.', OLD.estado, NEW.estado;
    END IF;

    IF NEW.estado = 'Finalizado' THEN
      -- Doc 9.9.5: now() = fecha y hora actual (inicio de la transacción)
      IF NEW.fin > now() THEN
        -- Doc 9.8: to_char(fecha, 'YYYY-MM-DD HH24:MI') convierte la fecha a texto con ese formato
        RAISE EXCEPTION 'CIERRE: El evento "%" termina el % y solo se puede finalizar después de esa hora.',
          NEW.nombre, to_char(NEW.fin, 'YYYY-MM-DD HH24:MI');
      END IF;

      -- Doc 9.21: COUNT(*) cuenta todas las filas; COUNT(columna) solo las que "is not null"
      -- => COUNT(fecha_checkin) cuenta a los que sí hicieron check-in
      SELECT COUNT(*), COUNT(fecha_checkin) INTO inscritos, llegaron
      FROM inscripciones
      WHERE evento_id = NEW.id;

      IF inscritos = 0 THEN
        NEW.tasa_asistencia := NULL;
      ELSE
        NEW.tasa_asistencia := ROUND(llegaron * 100.0 / inscritos, 2);   -- Doc 9.5: ROUND(v, s) = s decimales
      END IF;
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_eventos_1_estado ON eventos;
CREATE TRIGGER tr_eventos_1_estado
  BEFORE INSERT OR UPDATE ON eventos
  FOR EACH ROW
  EXECUTE FUNCTION fn_a4_control_estado();


-- ============ A1: disponibilidad y capacidad del salón ============

CREATE OR REPLACE FUNCTION fn_a1_disponibilidad_salon()
RETURNS TRIGGER AS $$
DECLARE
  -- Definición de variables
  salon RECORD;   -- Doc 41.3.5: un RECORD toma la estructura de la fila que se le asigna en el SELECT
  cruce RECORD;
  inscritos INTEGER;
BEGIN
  -- Lógica
  -- Un evento cancelado libera el salón
  IF NEW.estado = 'Cancelado' THEN
    RETURN NEW;
  END IF;

  -- En UPDATE solo se valida si cambió salón, horario o aforo (o si se reactiva)
  IF TG_OP = 'UPDATE' AND NEW.salon_id = OLD.salon_id AND NEW.inicio = OLD.inicio
     AND NEW.fin = OLD.fin AND NEW.aforo_esperado = OLD.aforo_esperado
     AND OLD.estado <> 'Cancelado' THEN
    RETURN NEW;
  END IF;

  SELECT * INTO salon FROM salones WHERE id = NEW.salon_id;
  -- Doc 41.5.5: "A SELECT INTO statement sets FOUND true if a row is assigned, false if no row is returned."
  IF NOT FOUND THEN
    RETURN NEW;  -- la llave foránea se encarga del error
  END IF;

  IF NOT salon.activo THEN
    RAISE EXCEPTION 'SALON INACTIVO: El salón "%" está deshabilitado temporalmente.', salon.nombre;
  END IF;

  IF NEW.aforo_esperado > salon.capacidad THEN
    RAISE EXCEPTION 'CAPACIDAD: El aforo esperado (% personas) supera la capacidad del salón "%" (% personas).',
      NEW.aforo_esperado, salon.nombre, salon.capacidad;
  END IF;

  -- Cruce con otro evento no cancelado del mismo salón, dejando 1 hora de montaje
  -- Doc 9.9: fecha + INTERVAL '1 hour' suma una hora a la fecha
  SELECT e.nombre, e.inicio, e.fin INTO cruce
  FROM eventos e
  WHERE e.salon_id = NEW.salon_id
    AND e.id <> NEW.id
    AND e.estado <> 'Cancelado'
    AND e.inicio < NEW.fin + INTERVAL '1 hour'
    AND e.fin + INTERVAL '1 hour' > NEW.inicio
  ORDER BY e.inicio
  LIMIT 1;

  IF FOUND THEN
    RAISE EXCEPTION 'DISPONIBILIDAD: El salón "%" está reservado para "%" (% a %). Se requiere 1 hora de montaje entre eventos.',
      salon.nombre, cruce.nombre, to_char(cruce.inicio, 'YYYY-MM-DD HH24:MI'), to_char(cruce.fin, 'YYYY-MM-DD HH24:MI');
  END IF;

  -- Al bajar el aforo no puede quedar por debajo de los ya inscritos
  IF TG_OP = 'UPDATE' THEN
    SELECT COUNT(*) INTO inscritos FROM inscripciones WHERE evento_id = NEW.id;
    IF NEW.aforo_esperado < inscritos THEN
      RAISE EXCEPTION 'CUPO: El evento "%" ya tiene % inscritos; el aforo no puede bajar a %.',
        NEW.nombre, inscritos, NEW.aforo_esperado;
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_eventos_2_disponibilidad ON eventos;
CREATE TRIGGER tr_eventos_2_disponibilidad
  BEFORE INSERT OR UPDATE ON eventos
  FOR EACH ROW
  EXECUTE FUNCTION fn_a1_disponibilidad_salon();


-- ============ A3: liquidación automática ============

-- 3.1 Valor total del evento = horas x precio del salón + servicios
CREATE OR REPLACE FUNCTION fn_a3_liquidar_evento()
RETURNS TRIGGER AS $$
BEGIN
  -- Lógica
  -- El precio del salón se congela al crear el evento o al cambiarlo de salón
  IF TG_OP = 'INSERT' OR NEW.salon_id <> OLD.salon_id THEN
    SELECT precio_hora INTO NEW.precio_hora_salon FROM salones WHERE id = NEW.salon_id;
  END IF;

  -- Doc 41.10: en un trigger BEFORE se puede cambiar NEW antes de que se guarde la fila
  NEW.valor_total := fn_horas_evento(NEW.inicio, NEW.fin) * NEW.precio_hora_salon
                     + fn_total_servicios(NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_eventos_3_liquidacion ON eventos;
CREATE TRIGGER tr_eventos_3_liquidacion
  BEFORE INSERT OR UPDATE ON eventos
  FOR EACH ROW
  EXECUTE FUNCTION fn_a3_liquidar_evento();

-- 3.2 Al contratar un servicio: congelar precio y calcular cantidad por defecto
CREATE OR REPLACE FUNCTION fn_a3_servicio_evento()
RETURNS TRIGGER AS $$
DECLARE
  -- Definición de variables
  evento RECORD;
  servicio RECORD;
BEGIN
  -- Lógica
  -- Doc 41.10: en DELETE solo existe OLD; en INSERT solo existe NEW
  IF TG_OP = 'DELETE' THEN
    SELECT * INTO evento FROM eventos WHERE id = OLD.evento_id;
  ELSE
    SELECT * INTO evento FROM eventos WHERE id = NEW.evento_id;
  END IF;

  IF evento.estado IN ('Finalizado', 'Cancelado') THEN
    RAISE EXCEPTION 'SERVICIOS: El evento "%" está % y sus servicios ya no se pueden modificar.',
      evento.nombre, evento.estado;
  END IF;

  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  END IF;

  SELECT * INTO servicio FROM servicios WHERE id = NEW.servicio_id;

  IF NOT servicio.activo THEN
    RAISE EXCEPTION 'SERVICIOS: El servicio "%" no está disponible en el catálogo.', servicio.nombre;
  END IF;

  -- Precio congelado: solo se toma del catálogo al contratar (o si cambian el servicio)
  IF TG_OP = 'INSERT' OR NEW.servicio_id <> OLD.servicio_id THEN
    NEW.precio_unitario := servicio.precio_unitario;
  ELSE
    NEW.precio_unitario := OLD.precio_unitario;
  END IF;

  -- Sin cantidad: por persona = aforo, por hora = duración (hacia arriba), por unidad = 1
  IF NEW.cantidad IS NULL THEN
    NEW.cantidad_manual := FALSE;
    -- Doc 41.6.4.4: CASE simple = "conditional execution based on equality of operands"
    CASE servicio.unidad_cobro
      WHEN 'Por persona' THEN NEW.cantidad := evento.aforo_esperado;
      WHEN 'Por hora' THEN NEW.cantidad := fn_horas_evento(evento.inicio, evento.fin);
      ELSE NEW.cantidad := 1;
    END CASE;
  ELSE
    NEW.cantidad_manual := TRUE;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_servicios_1_contratar ON evento_servicios;
CREATE TRIGGER tr_servicios_1_contratar
  BEFORE INSERT OR UPDATE OR DELETE ON evento_servicios
  FOR EACH ROW
  EXECUTE FUNCTION fn_a3_servicio_evento();

-- 3.3 Después de agregar, cambiar o quitar un servicio, se actualiza el total del evento
CREATE OR REPLACE FUNCTION fn_a3_actualizar_total()
RETURNS TRIGGER AS $$
DECLARE
  -- Definición de variables
  id_evento INTEGER;
BEGIN
  -- Lógica
  IF TG_OP = 'DELETE' THEN
    id_evento := OLD.evento_id;
  ELSE
    id_evento := NEW.evento_id;
  END IF;

  UPDATE eventos
  SET valor_total = fn_horas_evento(inicio, fin) * precio_hora_salon + fn_total_servicios(id)
  WHERE id = id_evento;

  -- Doc 41.10: "The return value of a row-level trigger fired AFTER ... is always ignored; it might as well be null."
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_servicios_2_total ON evento_servicios;
CREATE TRIGGER tr_servicios_2_total
  AFTER INSERT OR UPDATE OR DELETE ON evento_servicios
  FOR EACH ROW
  EXECUTE FUNCTION fn_a3_actualizar_total();

-- 3.4 Al reprogramar horario o aforo, las cantidades automáticas se recalculan
--     (las que el cliente puso a mano se respetan)
CREATE OR REPLACE FUNCTION fn_a3_reprogramar_servicios()
RETURNS TRIGGER AS $$
BEGIN
  -- Lógica
  IF NEW.inicio <> OLD.inicio OR NEW.fin <> OLD.fin OR NEW.aforo_esperado <> OLD.aforo_esperado THEN
    -- cantidad = NULL hace que el trigger 3.2 la vuelva a calcular
    UPDATE evento_servicios
    SET cantidad = NULL
    WHERE evento_id = NEW.id AND cantidad_manual = FALSE;
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_eventos_5_servicios ON eventos;
CREATE TRIGGER tr_eventos_5_servicios
  AFTER UPDATE ON eventos
  FOR EACH ROW
  EXECUTE FUNCTION fn_a3_reprogramar_servicios();


-- ============ A4 (parte 2): auditoría con el usuario de la aplicación ============

CREATE OR REPLACE FUNCTION fn_a4_auditoria_evento()
RETURNS TRIGGER AS $$
DECLARE
  -- Definición de variables
  usuario_app VARCHAR;
BEGIN
  -- Lógica
  -- La API entra siempre con el mismo usuario de BD; el real lo envía con set_config('app.usuario', ..., true)
  -- Doc 9.28.1: current_setting(nombre, true) devuelve NULL "if there is no such setting" en vez de error
  usuario_app := current_setting('app.usuario', true);
  IF usuario_app IS NULL OR usuario_app = '' THEN
    usuario_app := current_user;  -- cambio hecho desde psql o pgAdmin
  END IF;

  IF TG_OP = 'INSERT' THEN
    INSERT INTO auditoria_eventos (evento_id, campo, valor_anterior, valor_nuevo, usuario)
    VALUES (NEW.id, 'estado', NULL, NEW.estado, usuario_app);
    RETURN NULL;
  END IF;

  -- Igual que el ejemplo de clase (auditoría SkyHigh): solo se registra si el valor cambió
  IF OLD.estado <> NEW.estado THEN
    INSERT INTO auditoria_eventos (evento_id, campo, valor_anterior, valor_nuevo, usuario)
    VALUES (NEW.id, 'estado', OLD.estado, NEW.estado, usuario_app);
  END IF;

  IF OLD.salon_id <> NEW.salon_id THEN
    INSERT INTO auditoria_eventos (evento_id, campo, valor_anterior, valor_nuevo, usuario)
    VALUES (NEW.id, 'salon',
            (SELECT nombre FROM salones WHERE id = OLD.salon_id),
            (SELECT nombre FROM salones WHERE id = NEW.salon_id), usuario_app);
  END IF;

  IF OLD.inicio <> NEW.inicio THEN
    INSERT INTO auditoria_eventos (evento_id, campo, valor_anterior, valor_nuevo, usuario)
    VALUES (NEW.id, 'inicio', to_char(OLD.inicio, 'YYYY-MM-DD HH24:MI'),
            to_char(NEW.inicio, 'YYYY-MM-DD HH24:MI'), usuario_app);
  END IF;

  IF OLD.fin <> NEW.fin THEN
    INSERT INTO auditoria_eventos (evento_id, campo, valor_anterior, valor_nuevo, usuario)
    VALUES (NEW.id, 'fin', to_char(OLD.fin, 'YYYY-MM-DD HH24:MI'),
            to_char(NEW.fin, 'YYYY-MM-DD HH24:MI'), usuario_app);
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_eventos_4_auditoria ON eventos;
CREATE TRIGGER tr_eventos_4_auditoria
  AFTER INSERT OR UPDATE ON eventos
  FOR EACH ROW
  EXECUTE FUNCTION fn_a4_auditoria_evento();


-- ============ A2: cupos y asistencia real ============

CREATE OR REPLACE FUNCTION fn_a2_inscripcion_checkin()
RETURNS TRIGGER AS $$
DECLARE
  -- Definición de variables
  evento RECORD;
  inscritos INTEGER;
BEGIN
  -- Lógica
  SELECT * INTO evento FROM eventos WHERE id = NEW.evento_id;

  IF TG_OP = 'INSERT' THEN
    IF evento.estado IN ('Cancelado', 'Finalizado') THEN
      RAISE EXCEPTION 'INSCRIPCION: El evento "%" está % y no recibe inscripciones.', evento.nombre, evento.estado;
    END IF;

    SELECT COUNT(*) INTO inscritos FROM inscripciones WHERE evento_id = NEW.evento_id;
    IF inscritos >= evento.aforo_esperado THEN
      RAISE EXCEPTION 'CUPO: El evento "%" alcanzó su aforo contratado (% personas).', evento.nombre, evento.aforo_esperado;
    END IF;
  END IF;

  -- Un solo check-in por asistente: si OLD ya tenía hora de llegada, se bloquea
  IF TG_OP = 'UPDATE' AND OLD.fecha_checkin IS NOT NULL THEN
    RAISE EXCEPTION 'CHECK-IN: Este asistente ya registró su llegada el %.', to_char(OLD.fecha_checkin, 'YYYY-MM-DD HH24:MI');
  END IF;

  IF NEW.fecha_checkin IS NOT NULL THEN
    IF evento.estado <> 'Confirmado' THEN
      RAISE EXCEPTION 'CHECK-IN: El evento "%" está %; solo se registra llegada en eventos confirmados.', evento.nombre, evento.estado;
    END IF;

    -- Ventana: desde 1 hora antes del inicio hasta la hora de fin
    IF NEW.fecha_checkin < evento.inicio - INTERVAL '1 hour' OR NEW.fecha_checkin > evento.fin THEN
      RAISE EXCEPTION 'CHECK-IN: Solo se permite ingresar entre % y % (hora indicada: %).',
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
