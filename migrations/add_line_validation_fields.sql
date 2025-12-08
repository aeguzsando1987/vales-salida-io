-- MIGRACION: Agregar campos de validacion linea por linea
-- Fecha: 2025-12-04
-- Descripcion: Agrega ok_exit, ok_entry, outer_destination e INCOMPLETE_DAMAGED

BEGIN;

-- 1. Agregar campos a voucher_details
ALTER TABLE voucher_details
ADD COLUMN IF NOT EXISTS ok_exit BOOLEAN NULL DEFAULT NULL,
ADD COLUMN IF NOT EXISTS ok_exit_notes TEXT NULL,
ADD COLUMN IF NOT EXISTS ok_entry BOOLEAN NULL DEFAULT NULL,
ADD COLUMN IF NOT EXISTS ok_entry_notes TEXT NULL;

-- 2. Agregar indices para performance
CREATE INDEX IF NOT EXISTS idx_voucher_details_ok_exit ON voucher_details(ok_exit);
CREATE INDEX IF NOT EXISTS idx_voucher_details_ok_entry ON voucher_details(ok_entry);

-- 3. Agregar campo a vouchers
ALTER TABLE vouchers
ADD COLUMN IF NOT EXISTS outer_destination VARCHAR(255) NULL;

-- 4. Agregar nuevo estado INCOMPLETE_DAMAGED al enum de status
ALTER TYPE voucherstatusenum ADD VALUE IF NOT EXISTS 'INCOMPLETE_DAMAGED';

-- 5. Comentarios para documentacion
COMMENT ON COLUMN voucher_details.ok_exit IS 'Validacion visual de salida por vigilante';
COMMENT ON COLUMN voucher_details.ok_exit_notes IS 'Observaciones si ok_exit=false';
COMMENT ON COLUMN voucher_details.ok_entry IS 'Validacion visual de entrada por gerente/supervisor';
COMMENT ON COLUMN voucher_details.ok_entry_notes IS 'Observaciones si ok_entry=false';
COMMENT ON COLUMN vouchers.outer_destination IS 'Destino en texto libre cuando NO es intercompañia';

COMMIT;

-- VERIFICACION POST-MIGRACION
SELECT
    v.id,
    v.folio,
    v.status,
    COUNT(vd.id) as total_lines,
    COUNT(CASE WHEN vd.ok_exit = true THEN 1 END) as ok_exit_count,
    COUNT(CASE WHEN vd.ok_entry = true THEN 1 END) as ok_entry_count
FROM vouchers v
LEFT JOIN voucher_details vd ON v.id = vd.voucher_id
GROUP BY v.id, v.folio, v.status;
