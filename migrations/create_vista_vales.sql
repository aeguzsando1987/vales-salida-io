-- MIGRACION: Vista de vales (vista_vales)
-- Fecha: 2026-09-11
-- Descripcion:
--   Define la vista de solo lectura `vista_vales`, pensada para consultas
--   directas desde DBeaver / reportes. Traduce enums y FKs a texto legible
--   en espanol y filtra los vales borrados (is_deleted = false).
--
--   Columnas de notas incluidas:
--     - notas          -> vouchers.notes           (observaciones, visibles en PDF)
--     - notas_internas -> vouchers.internal_notes  (notas internas, no visibles en PDF)
--
-- Usa CREATE OR REPLACE VIEW: idempotente y seguro de re-ejecutar.
-- Nota: las columnas nuevas solo pueden anadirse al final de la vista existente.

BEGIN;

CREATE OR REPLACE VIEW vista_vales AS
 SELECT v.id,
    v.folio,
        CASE v.voucher_type
            WHEN 'EXIT'::vouchertypeenum THEN 'SALIDA'::text
            WHEN 'ENTRY'::vouchertypeenum THEN 'ENTRADA'::text
            ELSE NULL::text
        END AS tipo,
        CASE v.status
            WHEN 'PENDING'::voucherstatusenum THEN 'Pendiente'::text
            WHEN 'APPROVED'::voucherstatusenum THEN 'Aprobado'::text
            WHEN 'IN_TRANSIT'::voucherstatusenum THEN 'En Tránsito'::text
            WHEN 'CLOSED'::voucherstatusenum THEN 'Cerrado'::text
            WHEN 'OVERDUE'::voucherstatusenum THEN 'Vencido'::text
            WHEN 'CANCELLED'::voucherstatusenum THEN 'Cancelado'::text
            ELSE NULL::text
        END AS estado,
        CASE v.with_return
            WHEN true THEN 'Sí'::text
            WHEN false THEN 'No'::text
            ELSE NULL::text
        END AS con_retorno,
    c.company_name AS empresa,
    ob.branch_name AS origen,
    db.branch_name AS destino,
    v.outer_destination AS destino_externo,
    u.name AS creado_por,
    concat(ai.first_name, ' ', ai.last_name) AS aprobado_por,
    v.estimated_return_date AS fecha_retorno_estimada,
    (v.created_at AT TIME ZONE 'America/Mexico_City'::text) AS fecha_creacion,
    (v.updated_at AT TIME ZONE 'America/Mexico_City'::text) AS ultima_actualizacion,
    v.notes AS notas,
    v.internal_notes AS notas_internas
   FROM vouchers v
     LEFT JOIN companies c ON c.id = v.company_id
     LEFT JOIN branches ob ON ob.id = v.origin_branch_id
     LEFT JOIN branches db ON db.id = v.destination_branch_id
     LEFT JOIN users u ON u.id = v.created_by
     LEFT JOIN individuals ai ON ai.id = v.approved_by_id
  WHERE v.is_deleted = false
  ORDER BY v.created_at DESC;

COMMIT;
