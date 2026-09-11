-- MIGRACION: Agregar campos de notas a las vistas de reporte
-- Fecha: 2026-09-11
-- Descripcion:
--   Agrega a todas las vistas de reporte dos columnas de notas del vale:
--     - notas          -> vouchers.notes           (observaciones, visibles en PDF)
--     - notas_internas -> vouchers.internal_notes  (notas internas, no visibles en PDF)
--
--   Vistas afectadas:
--     - v_movimientos              (nivel vale)
--     - vista_materiales           (nivel linea; notas del vale como contexto de cabecera)
--     - v_discrepancias            (nivel linea; notas del vale como contexto)
--     - v_rechazos_cancelaciones   (nivel vale)
--     - v_bitacora_eventos         (UNION ALL; se agregan a cada una de las 6 ramas)
--
--   vista_vales se define aparte en create_vista_vales.sql.
--
-- Usa CREATE OR REPLACE VIEW: idempotente y seguro de re-ejecutar.
-- Nota: las columnas nuevas se anaden al final de cada vista.

BEGIN;

-- ============ v_movimientos ============
CREATE OR REPLACE VIEW v_movimientos AS
 SELECT v.id AS voucher_id,
    v.folio,
    v.voucher_type,
    v.status,
    v.with_return,
    v.is_intercompany,
    c.company_name AS empresa,
    ob.branch_name AS sucursal_origen,
    COALESCE(db.branch_name, v.outer_destination) AS destino,
    cu.name AS creador_usuario,
    (ci.first_name::text || ' '::text) || ci.last_name::text AS creador,
    (apr.first_name::text || ' '::text) || apr.last_name::text AS jefe_aprobador,
    v.first_approved_at,
    (io.first_name::text || ' '::text) || io.last_name::text AS contralor,
    v.io_approved_at,
    (dlv.first_name::text || ' '::text) || dlv.last_name::text AS entregado_por,
    (rcv.first_name::text || ' '::text) || rcv.last_name::text AS recibido_por,
    v.estimated_return_date,
    v.actual_return_date,
    (cb.first_name::text || ' '::text) || cb.last_name::text AS cancelado_por,
    v.cancelled_at,
    v.cancelled_from_status,
    v.cancellation_reason,
    v.created_at,
    v.notes AS notas,
    v.internal_notes AS notas_internas
   FROM vouchers v
     LEFT JOIN companies c ON c.id = v.company_id
     LEFT JOIN branches ob ON ob.id = v.origin_branch_id
     LEFT JOIN branches db ON db.id = v.destination_branch_id
     LEFT JOIN users cu ON cu.id = v.created_by
     LEFT JOIN individuals ci ON ci.user_id = v.created_by AND ci.is_deleted = false
     LEFT JOIN individuals apr ON apr.id = v.approved_by_id
     LEFT JOIN individuals io ON io.id = v.io_approved_by_id
     LEFT JOIN individuals dlv ON dlv.id = v.delivered_by_id
     LEFT JOIN individuals rcv ON rcv.id = v.received_by_id
     LEFT JOIN individuals cb ON cb.id = v.cancelled_by_id
  WHERE v.is_deleted = false;

-- ============ vista_materiales ============
CREATE OR REPLACE VIEW vista_materiales AS
 SELECT v.folio,
        CASE v.voucher_type
            WHEN 'EXIT'::vouchertypeenum THEN 'SALIDA'::text
            WHEN 'ENTRY'::vouchertypeenum THEN 'ENTRADA'::text
            ELSE NULL::text
        END AS tipo_movimiento,
        CASE v.status
            WHEN 'PENDING'::voucherstatusenum THEN 'Pendiente'::text
            WHEN 'APPROVED'::voucherstatusenum THEN 'Aprobado'::text
            WHEN 'IN_TRANSIT'::voucherstatusenum THEN 'En Transito'::text
            WHEN 'CLOSED'::voucherstatusenum THEN 'Cerrado'::text
            WHEN 'OVERDUE'::voucherstatusenum THEN 'Vencido'::text
            WHEN 'CANCELLED'::voucherstatusenum THEN 'Cancelado'::text
            ELSE NULL::text
        END AS estado_vale,
    c.company_name AS empresa,
    ob.branch_name AS origen,
    db.branch_name AS destino,
    v.outer_destination AS destino_externo,
    vd.line_number AS linea,
    vd.item_name AS articulo,
    p.category AS categoria,
    vd.item_description AS descripcion,
    vd.quantity AS cantidad,
    vd.unit_of_measure AS unidad,
    vd.serial_number AS numero_serie,
    vd.part_number AS numero_parte,
    vd.notes AS observaciones,
        CASE vd.ok_exit
            WHEN true THEN 'OK'::text
            WHEN false THEN 'Con observaciones'::text
            ELSE 'Sin validar'::text
        END AS validacion_salida,
    vd.ok_exit_notes AS obs_salida,
        CASE vd.ok_entry
            WHEN true THEN 'OK'::text
            WHEN false THEN 'Con observaciones'::text
            ELSE 'Sin validar'::text
        END AS validacion_entrada,
    vd.ok_entry_notes AS obs_entrada,
    u.name AS creado_por,
    concat(ai.first_name, ' ', ai.last_name) AS aprobado_por,
    v.created_at AS fecha_creacion,
    v.estimated_return_date AS fecha_retorno_estimada,
    v.notes AS notas,
    v.internal_notes AS notas_internas
   FROM voucher_details vd
     JOIN vouchers v ON v.id = vd.voucher_id
     LEFT JOIN products p ON p.id = vd.product_id
     LEFT JOIN companies c ON c.id = v.company_id
     LEFT JOIN branches ob ON ob.id = v.origin_branch_id
     LEFT JOIN branches db ON db.id = v.destination_branch_id
     LEFT JOIN users u ON u.id = v.created_by
     LEFT JOIN individuals ai ON ai.id = v.approved_by_id
  WHERE vd.is_deleted = false AND v.is_deleted = false
  ORDER BY v.created_at DESC, vd.line_number;

-- ============ v_discrepancias ============
CREATE OR REPLACE VIEW v_discrepancias AS
 SELECT v.id AS voucher_id,
    v.folio,
    v.status,
    c.company_name AS empresa,
    vd.line_number,
    vd.item_name,
    vd.quantity,
    vd.unit_of_measure,
    vd.serial_number,
    vd.ok_exit,
    vd.ok_exit_notes,
    vd.ok_entry,
    vd.ok_entry_notes,
    v.notes AS notas,
    v.internal_notes AS notas_internas
   FROM voucher_details vd
     JOIN vouchers v ON v.id = vd.voucher_id AND v.is_deleted = false
     LEFT JOIN companies c ON c.id = v.company_id
  WHERE vd.is_deleted = false AND (vd.ok_exit = false OR vd.ok_entry = false);

-- ============ v_rechazos_cancelaciones ============
CREATE OR REPLACE VIEW v_rechazos_cancelaciones AS
 SELECT v.id AS voucher_id,
    v.folio,
    v.voucher_type,
        CASE v.cancelled_from_status
            WHEN 'PENDING'::text THEN 'Rechazo Jefe Directo'::character varying
            WHEN 'PENDING_IO_APPROVAL'::text THEN 'Rechazo Contraloría'::character varying
            WHEN 'APPROVED'::text THEN 'Cancelación (post-aprobación)'::character varying
            ELSE COALESCE(v.cancelled_from_status, 'N/D'::character varying)
        END AS tipo,
    v.cancelled_from_status,
    (cb.first_name::text || ' '::text) || cb.last_name::text AS cancelado_por,
    v.cancelled_at,
    v.cancellation_reason,
    c.company_name AS empresa,
    v.notes AS notas,
    v.internal_notes AS notas_internas
   FROM vouchers v
     LEFT JOIN individuals cb ON cb.id = v.cancelled_by_id
     LEFT JOIN companies c ON c.id = v.company_id
  WHERE v.is_deleted = false AND (v.status = 'CANCELLED'::voucherstatusenum OR v.cancelled_at IS NOT NULL);

-- ============ v_bitacora_eventos (UNION ALL: notas en cada rama) ============
CREATE OR REPLACE VIEW v_bitacora_eventos AS
 SELECT v.id AS voucher_id,
    v.folio,
    1 AS orden,
    'Creación'::text AS evento,
    v.created_at AS fecha,
    COALESCE((ci.first_name::text || ' '::text) || ci.last_name::text, cu.name::text) AS actor,
    'Creador'::text AS capacidad,
    NULL::text AS detalle,
    v.notes AS notas,
    v.internal_notes AS notas_internas
   FROM vouchers v
     LEFT JOIN users cu ON cu.id = v.created_by
     LEFT JOIN individuals ci ON ci.user_id = v.created_by AND ci.is_deleted = false
  WHERE v.is_deleted = false
UNION ALL
 SELECT v.id AS voucher_id,
    v.folio,
    2 AS orden,
    'Aprobación Jefe Directo'::text AS evento,
    v.first_approved_at AS fecha,
    (a.first_name::text || ' '::text) || a.last_name::text AS actor,
    'Jefe Directo'::text AS capacidad,
    NULL::text AS detalle,
    v.notes,
    v.internal_notes
   FROM vouchers v
     JOIN individuals a ON a.id = v.approved_by_id
  WHERE v.is_deleted = false AND v.approved_by_id IS NOT NULL
UNION ALL
 SELECT v.id AS voucher_id,
    v.folio,
    3 AS orden,
    'Aprobación Contraloría'::text AS evento,
    v.io_approved_at AS fecha,
    (i.first_name::text || ' '::text) || i.last_name::text AS actor,
    'Contralor'::text AS capacidad,
    NULL::text AS detalle,
    v.notes,
    v.internal_notes
   FROM vouchers v
     JOIN individuals i ON i.id = v.io_approved_by_id
  WHERE v.is_deleted = false AND v.io_approved_by_id IS NOT NULL
UNION ALL
 SELECT v.id AS voucher_id,
    v.folio,
    4 AS orden,
    'Validación de Salida'::text AS evento,
    ol.created_at AS fecha,
    (s.first_name::text || ' '::text) || s.last_name::text AS actor,
    'Vigilante'::text AS capacidad,
    ol.validation_status::text || COALESCE(' - '::text || ol.observations, ''::text) AS detalle,
    v.notes,
    v.internal_notes
   FROM out_logs ol
     JOIN vouchers v ON v.id = ol.voucher_id AND v.is_deleted = false
     LEFT JOIN individuals s ON s.id = ol.scanned_by_id
UNION ALL
 SELECT v.id AS voucher_id,
    v.folio,
    5 AS orden,
    'Entrada de Material'::text AS evento,
    el.created_at AS fecha,
    (r.first_name::text || ' '::text) || r.last_name::text AS actor,
    'Receptor'::text AS capacidad,
    el.entry_status::text || COALESCE(' - Faltantes: '::text || el.missing_items_description, ''::text) AS detalle,
    v.notes,
    v.internal_notes
   FROM entry_logs el
     JOIN vouchers v ON v.id = el.voucher_id AND v.is_deleted = false
     LEFT JOIN individuals r ON r.id = el.received_by_id
UNION ALL
 SELECT v.id AS voucher_id,
    v.folio,
    6 AS orden,
        CASE v.cancelled_from_status
            WHEN 'PENDING'::text THEN 'Rechazo Jefe Directo'::text
            WHEN 'PENDING_IO_APPROVAL'::text THEN 'Rechazo Contraloría'::text
            WHEN 'APPROVED'::text THEN 'Cancelación'::text
            ELSE 'Cancelación'::text
        END AS evento,
    v.cancelled_at AS fecha,
    (cb.first_name::text || ' '::text) || cb.last_name::text AS actor,
    'Cancelación'::text AS capacidad,
    v.cancellation_reason AS detalle,
    v.notes,
    v.internal_notes
   FROM vouchers v
     LEFT JOIN individuals cb ON cb.id = v.cancelled_by_id
  WHERE v.is_deleted = false AND v.cancelled_at IS NOT NULL
  ORDER BY 1, 5;

COMMIT;
