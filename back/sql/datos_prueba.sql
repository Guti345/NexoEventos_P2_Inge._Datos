-- =========================================================
-- Parcial 2 - Ingeniería de Datos | Sistema NexoEventos
-- Catálogo del centro y datos de prueba (sección 2 del enunciado)
-- =========================================================

--rollback;

/*TRUNCATE TABLE
    trazabilidad,
    inscripciones,
    servicios_eventos,
    eventos,
    asistentes,
    clientes,
    staff,
    servicios,
    salones
RESTART IDENTITY CASCADE;*/

BEGIN;

-- ---------------------------------------------------------
-- 0. Usuario de aplicación para la auditoría de A4.
-- ---------------------------------------------------------
SELECT set_config('app.usuario', 'Antonio', true);

-- ---------------------------------------------------------
-- 1. SALONES (6 salones exigidos por el enunciado)
-- ---------------------------------------------------------
INSERT INTO salones (nombre_salon, tamano, capacidad, habilitado, precio_hora) VALUES
('Salón Orquídea',       'Pequeño', 40,   TRUE, 250000),
('Salón Heliconia',      'Pequeño', 60,   TRUE, 320000),
('Salón Guayacán',       'Mediano', 150,  TRUE, 650000),
('Salón Ceiba',          'Mediano', 200,  TRUE, 800000),
('Gran Salón Cóndor',    'Grande',  600,  TRUE, 1800000),
('Auditorio Principal',  'Grande',  1000, TRUE, 2500000);

-- ---------------------------------------------------------
-- 2. SERVICIOS (9 servicios exigidos por el enunciado)
-- ---------------------------------------------------------
INSERT INTO servicios (nombre_servicio, descripcion, unidad_cobro, precio) VALUES
('Estación de agua',       'Estación de hidratación con agua embotellada y vasos para los asistentes.',              'Persona', 3000),
('Estación de café',       'Estación de café, aromáticas y té caliente disponible durante todo el evento.',          'Persona', 6500),
('Refrigerio económico',   'Refrigerio sencillo con bebida y producto de panadería por persona.',                     'Persona', 12000),
('Refrigerio medio',       'Refrigerio intermedio con bebida, producto salado y producto dulce por persona.',         'Persona', 22000),
('Refrigerio alto',        'Refrigerio premium con variedad de bebidas calientes, frías y productos gourmet.',        'Persona', 38000),
('Sonido básico (2 micrófonos + parlantes)',    'Sistema de sonido con dos micrófonos y parlantes para espacios pequeños.',      'Hora', 120000),
('Sonido profesional (consola + 6 micrófonos)', 'Consola profesional con seis micrófonos para espacios grandes.',                'Hora', 350000),
('Multimedia (proyector + pantalla)',           'Proyector de alta definición con pantalla y cableado de video.',                'Hora', 90000),
('Streaming y grabación',                       'Transmisión en vivo y grabación profesional del evento.',                      'Hora', 450000);

-- ---------------------------------------------------------
-- 3. CLIENTES (10: 6 personas con CC, 4 empresas con NIT)
-- ---------------------------------------------------------
INSERT INTO clientes (tipo_documento, numero_documento, nombre, email, telefono, fecha_registro) VALUES
('CC',  '1001234567', 'Laura Fernanda Gómez',           'laura.gomez@example.com',          '3001234567', '2025-01-15 09:00'),
('CC',  '1002345678', 'Carlos Andrés Rodríguez',        'carlos.rodriguez@example.com',     '3002345678', '2025-02-10 10:30'),
('CC',  '1003456789', 'María Camila Torres',            'maria.torres@example.com',         '3003456789', '2025-03-05 14:00'),
('CC',  '1004567890', 'Juan Pablo Sánchez',             'juan.sanchez@example.com',         '3004567890', '2025-04-20 11:15'),
('CC',  '1005678901', 'Diana Patricia López',           'diana.lopez@example.com',          '3005678901', '2025-05-18 16:45'),
('CC',  '1006789012', 'Andrés Felipe Ramírez',          'andres.ramirez@example.com',       '3006789012', '2025-06-02 08:20'),
('NIT', '9001122334', 'Eventos Corporativos SAS',       'contacto@eventoscorp.com',         '6013456789', '2025-01-25 09:30'),
('NIT', '9002233445', 'Tecnología Avanzada S.A.',       'info@tecavanzada.com',             '6014567890', '2025-02-28 13:00'),
('NIT', '9003344556', 'Fundación Educativa del Valle',  'contacto@fundacionvalle.org',      '6025678901', '2025-03-12 10:00'),
('NIT', '9004455667', 'Grupo Comercial Andino',         'gerencia@grupoandino.com',         '6026789012', '2025-04-08 15:30');

-- ---------------------------------------------------------
-- 4. STAFF (17 personas, 5 niveles jerárquicos: Director >
--    Gerente > Jefe > Coordinador > Auxiliar/Técnico, cubriendo
--    las 6 áreas válidas del esquema)
-- ---------------------------------------------------------
INSERT INTO staff (nombre, email, area, cargo, fecha_ingreso, jefe_id) VALUES
('Ricardo Esteban Molina',   'ricardo.molina@nexoeventos.com',   'Dirección',           'Director',    '2015-01-10', NULL);

INSERT INTO staff (nombre, email, area, cargo, fecha_ingreso, jefe_id) VALUES
('Patricia Elena Vargas',    'patricia.vargas@nexoeventos.com',  'Operaciones',         'Gerente',     '2016-03-15', 1),
('Jorge Iván Castillo',      'jorge.castillo@nexoeventos.com',   'Comercial',           'Gerente',     '2016-06-01', 1);

INSERT INTO staff (nombre, email, area, cargo, fecha_ingreso, jefe_id) VALUES
('Sandra Milena Ortiz',      'sandra.ortiz@nexoeventos.com',     'Logística',           'Jefe',        '2017-02-20', 2),
('Felipe Antonio Reyes',     'felipe.reyes@nexoeventos.com',     'Alimentos y Bebidas', 'Jefe',        '2017-05-10', 2),
('Natalia Andrea Prieto',    'natalia.prieto@nexoeventos.com',   'Audiovisuales',       'Jefe',        '2017-08-22', 2),
('Camilo Ernesto Duarte',    'camilo.duarte@nexoeventos.com',    'Comercial',           'Jefe',        '2018-01-05', 3);

INSERT INTO staff (nombre, email, area, cargo, fecha_ingreso, jefe_id) VALUES
('Laura Vanessa Moreno',     'laura.moreno@nexoeventos.com',     'Operaciones',         'Coordinador', '2019-03-11', 4),
('Diego Alejandro Pérez',    'diego.perez@nexoeventos.com',      'Operaciones',         'Coordinador', '2019-07-19', 4),
('Valentina Suárez',         'valentina.suarez@nexoeventos.com', 'Alimentos y Bebidas', 'Coordinador', '2019-09-02', 5),
('Mateo Nicolás Gil',        'mateo.gil@nexoeventos.com',        'Audiovisuales',       'Coordinador', '2020-01-14', 6),
('Daniela Restrepo',         'daniela.restrepo@nexoeventos.com', 'Comercial',           'Coordinador', '2020-04-23', 7);

INSERT INTO staff (nombre, email, area, cargo, fecha_ingreso, jefe_id) VALUES
('Julián David Herrera',     'julian.herrera@nexoeventos.com',   'Logística',           'Auxiliar',    '2021-02-01', 8),
('Paula Andrea Cárdenas',    'paula.cardenas@nexoeventos.com',   'Alimentos y Bebidas', 'Auxiliar',    '2021-06-15', 10),
('Sebastián Londoño',        'sebastian.londono@nexoeventos.com','Audiovisuales',       'Técnico',     '2021-09-10', 11),
('Angélica María Rojas',     'angelica.rojas@nexoeventos.com',   'Audiovisuales',       'Técnico',     '2022-01-20', 11),
('Esteban Mauricio Gómez',   'esteban.gomez@nexoeventos.com',    'Comercial',           'Auxiliar',    '2022-05-05', 12);

-- ---------------------------------------------------------
-- 5. EVENTOS (14: Cotizado, Confirmado, Finalizado y Cancelado,
--    con eventos pasados y futuros, distintos salones, clientes
--    y coordinadores).
-- ---------------------------------------------------------
INSERT INTO eventos (nombre, inicio, fin, tipo, aforo_esperado, coordinador_id, estado, salon_id, cliente_id) VALUES
('Congreso Nacional de Innovación',    '2026-03-10 08:00', '2026-03-10 18:00', 'Congreso',     800, 8,  'Cotizado', 6, 7),
('Feria Empresarial Regional',         '2026-04-14 09:00', '2026-04-14 19:00', 'Feria',        500, 9,  'Cotizado', 5, 8),
('Seminario de Finanzas Corporativas', '2026-02-05 08:00', '2026-02-05 13:00', 'Seminario',    120, 12, 'Cotizado', 3, 9),
('Taller de Liderazgo',                '2026-05-20 08:00', '2026-05-20 17:00', 'Taller',       10, 8,  'Cotizado', 4, 10),
('Conferencia de Tecnología Educativa','2026-01-15 14:00', '2026-01-15 18:00', 'Conferencia',  55,  11, 'Cotizado', 2, 1),
('Exposición de Arte Contemporáneo',   '2025-11-20 10:00', '2025-11-20 16:00', 'Exposición',   35,  10, 'Cotizado', 1, 2),
('Corporativo Fin de Año',             '2025-12-12 18:00', '2025-12-12 23:00', 'Corporativo',  100, 9,  'Cotizado', 3, 7),
('Boda Social Pérez-Gómez',            '2026-12-05 16:00', '2026-12-05 23:00', 'Social',       550, 10, 'Cotizado', 5, 3),
('Congreso Médico Internacional',      '2027-02-10 08:00', '2027-02-10 19:00', 'Congreso',     950, 11, 'Cotizado', 6, 9),
('Taller de Cocina Gourmet',           '2026-11-18 09:00', '2026-11-18 17:00', 'Taller',       180, 10, 'Cotizado', 4, 4),
('Feria de Emprendimiento',            '2026-12-20 10:00', '2026-12-20 18:00', 'Feria',        58,  12, 'Cotizado', 2, 5),
('Seminario de Ventas B2B',            '2026-11-05 08:00', '2026-11-05 13:00', 'Seminario',    38,  8,  'Cotizado', 1, 8),
('Conferencia Internacional de IA',    '2027-01-22 09:00', '2027-01-22 18:00', 'Conferencia',  580, 11, 'Cotizado', 5, 10),
('Lanzamiento de Producto',            '2026-12-10 15:00', '2026-12-10 19:00', 'Otro',         140, 9,  'Cotizado', 3, 6);

-- ---------------------------------------------------------
-- 6. SERVICIOS_EVENTOS (contratación de servicios por evento).
-- ---------------------------------------------------------
INSERT INTO servicios_eventos (evento_id, servicio_id, cantidad) VALUES
-- Evento 1: Congreso Nacional de Innovación
(1, 7, NULL),   -- Sonido profesional (horas automáticas)
(1, 8, NULL),   -- Multimedia (horas automáticas)
(1, 5, 600),    -- Refrigerio alto (manual, menor al aforo)
(1, 2, NULL),   -- Estación de café (personas automáticas)
-- Evento 2: Feria Empresarial Regional
(2, 6, NULL),
(2, 8, NULL),
(2, 3, 350),
(2, 1, NULL),
-- Evento 3: Seminario de Finanzas Corporativas
(3, 6, NULL),
(3, 4, NULL),
(3, 2, NULL),
-- Evento 4: Taller de Liderazgo
(4, 6, NULL),
(4, 3, NULL),
(4, 1, NULL),
-- Evento 5: Conferencia de Tecnología Educativa (se cancelará luego)
(5, 8, NULL),
(5, 2, NULL),
-- Evento 7: Corporativo Fin de Año
(7, 7, NULL),
(7, 9, 3),      -- Streaming y grabación (manual, solo 3 de las 5 horas)
(7, 5, NULL),
-- Evento 8: Boda Social Pérez-Gómez
(8, 7, NULL),
(8, 9, NULL),
(8, 5, 500),
(8, 2, NULL),
-- Evento 9: Congreso Médico Internacional
(9, 7, NULL),
(9, 8, NULL),
(9, 4, NULL),
-- Evento 10: Taller de Cocina Gourmet
(10, 6, NULL),
(10, 4, NULL),
(10, 1, NULL),
-- Evento 11: Feria de Emprendimiento
(11, 6, NULL),
(11, 3, NULL),
-- Evento 12: Seminario de Ventas B2B
(12, 8, NULL),
(12, 2, NULL),
-- Evento 13: Conferencia Internacional de IA
(13, 7, NULL),
(13, 9, NULL),
(13, 5, 400),
-- Evento 14: Lanzamiento de Producto (se cancelará luego)
(14, 8, NULL);

-- ---------------------------------------------------------
-- 7. ASISTENTES (60 personas)
-- ---------------------------------------------------------
INSERT INTO asistentes (nombre, documento_identidad, email, empresa) VALUES
('Laura Ramírez',      '2000000001', 'asistente001@correo.com', 'Particular'),
('Carlos Ortiz',       '2000000002', 'asistente002@correo.com', 'Particular'),
('María Duarte',       '2000000003', 'asistente003@correo.com', 'Particular'),
('Juan Suárez',        '2000000004', 'asistente004@correo.com', 'Tech Solutions SAS'),
('Diana Herrera',      '2000000005', 'asistente005@correo.com', 'Grupo Andino'),
('Andrés Rodríguez',   '2000000006', 'asistente006@correo.com', 'Particular'),
('Camila López',       '2000000007', 'asistente007@correo.com', 'Comercializadora XYZ'),
('Felipe Castillo',    '2000000008', 'asistente008@correo.com', 'Particular'),
('Natalia Prieto',     '2000000009', 'asistente009@correo.com', 'Fundación Valle'),
('Jorge Pérez',        '2000000010', 'asistente010@correo.com', 'Particular'),
('Sandra Restrepo',    '2000000011', 'asistente011@correo.com', 'Particular'),
('Daniel Gómez',       '2000000012', 'asistente012@correo.com', 'Constructora ABC'),
('Paula Sánchez',      '2000000013', 'asistente013@correo.com', 'Particular'),
('Sebastián Vargas',   '2000000014', 'asistente014@correo.com', 'Particular'),
('Valentina Reyes',    '2000000015', 'asistente015@correo.com', 'Universidad Central'),
('Mateo Moreno',       '2000000016', 'asistente016@correo.com', 'Particular'),
('Daniela Gil',        '2000000017', 'asistente017@correo.com', 'Particular'),
('Esteban Cárdenas',   '2000000018', 'asistente018@correo.com', 'Logística Nacional'),
('Angélica Torres',    '2000000019', 'asistente019@correo.com', 'Particular'),
('Ricardo Ramírez',    '2000000020', 'asistente020@correo.com', 'Particular'),
('Laura Ortiz',        '2000000021', 'asistente021@correo.com', 'Particular'),
('Carlos Duarte',      '2000000022', 'asistente022@correo.com', 'Particular'),
('María Suárez',       '2000000023', 'asistente023@correo.com', 'Particular'),
('Juan Herrera',       '2000000024', 'asistente024@correo.com', 'Tech Solutions SAS'),
('Diana Rodríguez',    '2000000025', 'asistente025@correo.com', 'Grupo Andino'),
('Andrés López',       '2000000026', 'asistente026@correo.com', 'Particular'),
('Camila Castillo',    '2000000027', 'asistente027@correo.com', 'Comercializadora XYZ'),
('Felipe Prieto',      '2000000028', 'asistente028@correo.com', 'Particular'),
('Natalia Pérez',      '2000000029', 'asistente029@correo.com', 'Fundación Valle'),
('Jorge Restrepo',     '2000000030', 'asistente030@correo.com', 'Particular'),
('Sandra Gómez',       '2000000031', 'asistente031@correo.com', 'Particular'),
('Daniel Sánchez',     '2000000032', 'asistente032@correo.com', 'Constructora ABC'),
('Paula Vargas',       '2000000033', 'asistente033@correo.com', 'Particular'),
('Sebastián Reyes',    '2000000034', 'asistente034@correo.com', 'Particular'),
('Valentina Moreno',   '2000000035', 'asistente035@correo.com', 'Universidad Central'),
('Mateo Gil',          '2000000036', 'asistente036@correo.com', 'Particular'),
('Daniela Cárdenas',   '2000000037', 'asistente037@correo.com', 'Particular'),
('Esteban Torres',     '2000000038', 'asistente038@correo.com', 'Logística Nacional'),
('Angélica Ramírez',   '2000000039', 'asistente039@correo.com', 'Particular'),
('Ricardo Ortiz',      '2000000040', 'asistente040@correo.com', 'Particular'),
('Laura Duarte',       '2000000041', 'asistente041@correo.com', 'Particular'),
('Carlos Suárez',      '2000000042', 'asistente042@correo.com', 'Particular'),
('María Herrera',      '2000000043', 'asistente043@correo.com', 'Particular'),
('Juan Rodríguez',     '2000000044', 'asistente044@correo.com', 'Tech Solutions SAS'),
('Diana López',        '2000000045', 'asistente045@correo.com', 'Grupo Andino'),
('Andrés Castillo',    '2000000046', 'asistente046@correo.com', 'Particular'),
('Camila Prieto',      '2000000047', 'asistente047@correo.com', 'Comercializadora XYZ'),
('Felipe Pérez',       '2000000048', 'asistente048@correo.com', 'Particular'),
('Natalia Restrepo',   '2000000049', 'asistente049@correo.com', 'Fundación Valle'),
('Jorge Gómez',        '2000000050', 'asistente050@correo.com', 'Particular'),
('Sandra Sánchez',     '2000000051', 'asistente051@correo.com', 'Particular'),
('Daniel Vargas',      '2000000052', 'asistente052@correo.com', 'Constructora ABC'),
('Paula Reyes',        '2000000053', 'asistente053@correo.com', 'Particular'),
('Sebastián Moreno',   '2000000054', 'asistente054@correo.com', 'Particular'),
('Valentina Gil',      '2000000055', 'asistente055@correo.com', 'Universidad Central'),
('Mateo Cárdenas',     '2000000056', 'asistente056@correo.com', 'Particular'),
('Daniela Torres',     '2000000057', 'asistente057@correo.com', 'Particular'),
('Esteban Ramírez',    '2000000058', 'asistente058@correo.com', 'Logística Nacional'),
('Angélica Ortiz',     '2000000059', 'asistente059@correo.com', 'Particular'),
('Ricardo Duarte',     '2000000060', 'asistente060@correo.com', 'Particular');

-- ---------------------------------------------------------
-- 8. Confirmación de eventos (Cotizado -> Confirmado).
-- ---------------------------------------------------------
UPDATE eventos SET estado = 'Confirmado' WHERE id IN (1, 2, 3, 4, 7, 8, 10, 12);

-- ---------------------------------------------------------
-- 9. INSCRIPCIONES (108 inscripciones repartidas entre los 60
--    asistentes; ninguna supera el aforo contratado, validado
--    por A2 en cada INSERT).
-- ---------------------------------------------------------
-- Evento 1 (14 inscritos)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 1 FROM asistentes WHERE id BETWEEN 1 AND 14;
-- Evento 2 (12 inscritos)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 2 FROM asistentes WHERE id BETWEEN 15 AND 26;
-- Evento 3 (10 inscritos)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 3 FROM asistentes WHERE id BETWEEN 27 AND 36;
-- Evento 4 (10 inscritos)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 4 FROM asistentes WHERE id BETWEEN 37 AND 46;
-- Evento 5 (3 inscritos, luego se cancela el evento)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 5 FROM asistentes WHERE id BETWEEN 55 AND 57;
-- Evento 7 (8 inscritos)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 7 FROM asistentes WHERE id BETWEEN 47 AND 54;
-- Evento 8 (15 inscritos, evento futuro confirmado, sin check-in)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 8 FROM asistentes WHERE id BETWEEN 1 AND 15;
-- Evento 9 (5 inscritos, evento futuro cotizado)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 9 FROM asistentes WHERE id BETWEEN 16 AND 20;
-- Evento 10 (10 inscritos, evento futuro confirmado)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 10 FROM asistentes WHERE id BETWEEN 21 AND 30;
-- Evento 11 (4 inscritos, evento futuro cotizado)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 11 FROM asistentes WHERE id BETWEEN 31 AND 34;
-- Evento 12 (8 inscritos, evento futuro confirmado)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 12 FROM asistentes WHERE id BETWEEN 35 AND 42;
-- Evento 13 (6 inscritos, evento futuro cotizado)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 13 FROM asistentes WHERE id BETWEEN 43 AND 48;
-- Evento 14 (3 inscritos, luego se cancela el evento)
INSERT INTO inscripciones (asistente_id, evento_id) SELECT id, 14 FROM asistentes WHERE id BETWEEN 49 AND 51;

-- ---------------------------------------------------------
-- 10. CHECK-INS (solo en eventos ya Confirmados y dentro de la
--     ventana permitida por A2: [inicio - 1 hora, fin])
-- ---------------------------------------------------------
-- Evento 1: 12 de 14 llegan
UPDATE inscripciones i SET fecha_checkin = v.ts::timestamp
FROM (VALUES
    (1,'2026-03-10 07:45'),(2,'2026-03-10 07:50'),(3,'2026-03-10 07:55'),(4,'2026-03-10 08:00'),
    (5,'2026-03-10 08:05'),(6,'2026-03-10 08:10'),(7,'2026-03-10 08:15'),(8,'2026-03-10 08:20'),
    (9,'2026-03-10 08:25'),(10,'2026-03-10 08:30'),(11,'2026-03-10 08:35'),(12,'2026-03-10 08:40')
) AS v(asistente_id, ts)
WHERE i.evento_id = 1 AND i.asistente_id = v.asistente_id;

-- Evento 2: 6 de 12 llegan
UPDATE inscripciones i SET fecha_checkin = v.ts::timestamp
FROM (VALUES
    (15,'2026-04-14 08:50'),(16,'2026-04-14 08:55'),(17,'2026-04-14 09:00'),
    (18,'2026-04-14 09:05'),(19,'2026-04-14 09:10'),(20,'2026-04-14 09:15')
) AS v(asistente_id, ts)
WHERE i.evento_id = 2 AND i.asistente_id = v.asistente_id;

-- Evento 3: 2 de 10 llegan
UPDATE inscripciones i SET fecha_checkin = v.ts::timestamp
FROM (VALUES
    (27,'2026-02-05 07:50'),(28,'2026-02-05 07:55')
) AS v(asistente_id, ts)
WHERE i.evento_id = 3 AND i.asistente_id = v.asistente_id;

-- Evento 4: 10 de 10 llegan
UPDATE inscripciones i SET fecha_checkin = v.ts::timestamp
FROM (VALUES
    (37,'2026-05-20 07:40'),(38,'2026-05-20 07:43'),(39,'2026-05-20 07:46'),(40,'2026-05-20 07:49'),
    (41,'2026-05-20 07:52'),(42,'2026-05-20 07:55'),(43,'2026-05-20 07:58'),(44,'2026-05-20 08:01'),
    (45,'2026-05-20 08:04'),(46,'2026-05-20 08:07')
) AS v(asistente_id, ts)
WHERE i.evento_id = 4 AND i.asistente_id = v.asistente_id;

-- Evento 7: 5 de 8 llegan
UPDATE inscripciones i SET fecha_checkin = v.ts::timestamp
FROM (VALUES
    (47,'2025-12-12 17:50'),(48,'2025-12-12 17:55'),(49,'2025-12-12 18:00'),
    (50,'2025-12-12 18:05'),(51,'2025-12-12 18:10')
) AS v(asistente_id, ts)
WHERE i.evento_id = 7 AND i.asistente_id = v.asistente_id;

-- ---------------------------------------------------------
-- 11. Cambios de estado finales.
-- ---------------------------------------------------------
UPDATE eventos SET estado = 'Finalizado' WHERE id IN (1, 2, 3, 4, 7);
UPDATE eventos SET estado = 'Cancelado'  WHERE id IN (5, 6, 14);

COMMIT;

-- ---------------------------------------------------------
-- 12. Pruebas de carga.
-- ---------------------------------------------------------

-- Counts por registros tabla
SELECT
    (SELECT COUNT(*) FROM salones) AS salones,
    (SELECT COUNT(*) FROM servicios) AS servicios,
    (SELECT COUNT(*) FROM clientes) AS clientes,
    (SELECT COUNT(*) FROM staff) AS staff,
    (SELECT COUNT(*) FROM eventos) AS eventos,
    (SELECT COUNT(*) FROM servicios_eventos) AS servicios_eventos,
    (SELECT COUNT(*) FROM asistentes) AS asistentes,
    (SELECT COUNT(*) FROM inscripciones) AS inscripciones,
    (SELECT COUNT(*) FROM trazabilidad) AS trazabilidad;

-- Revisión a3 funcional liquidando
SELECT
    id,
    nombre,
    estado,
    precio_hora_salon_cotizado,
    valor_total_cotizado
FROM eventos
ORDER BY id;

-- Revisión a4 revisión asistencia
SELECT
    id,
    nombre,
    estado,
    tasa_asistencia
FROM eventos
ORDER BY id;

-- Revisión trazabilidad
SELECT *
FROM trazabilidad
ORDER BY fecha_hora;
