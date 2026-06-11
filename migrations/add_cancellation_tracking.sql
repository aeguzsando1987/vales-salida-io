-- MIGRACION: Trazabilidad de cancelaciones / rechazos de vales
-- Fecha: 2026-06-11
-- Descripcion:
--   Agrega a vouchers las columnas que permiten reflejar en la bitacora
--   QUIEN cancelo/rechazo, CUANDO y EN QUE CAPACIDAD:
--     - cancelled_by_id        -> Individual que ejecuto la cancelacion (firma)
--     - cancelled_at           -> Momento de la cancelacion
--     - cancelled_from_status  -> Estado previo (PENDING = rechazo jefe directo,
--                                 PENDING_IO_APPROVAL = rechazo contraloria,
--                                 APPROVED = cancelacion)
--     - cancellation_reason    -> Razon dedicada (espejo de la nota en internal_notes)
-- Aplica SOLO a una BBDD existente. En una BBDD nueva, create_all ya genera
-- estas columnas desde el modelo.
-- Idempotente: usa ADD COLUMN IF NOT EXISTS. Seguro de re-ejecutar.

BEGIN;

ALTER TABLE vouchers
ADD COLUMN IF NOT EXISTS cancelled_by_id INTEGER NULL REFERENCES individuals(id) ON DELETE RESTRICT,
ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS cancelled_from_status VARCHAR(30) NULL,
ADD COLUMN IF NOT EXISTS cancellation_reason TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_vouchers_cancelled_by_id ON vouchers(cancelled_by_id);

COMMENT ON COLUMN vouchers.cancelled_by_id IS 'Individual que cancelo/rechazo el vale';
COMMENT ON COLUMN vouchers.cancelled_at IS 'Momento de la cancelacion/rechazo';
COMMENT ON COLUMN vouchers.cancelled_from_status IS 'Estado previo a la cancelacion (define la capacidad del rechazo)';
COMMENT ON COLUMN vouchers.cancellation_reason IS 'Razon de la cancelacion/rechazo (columna dedicada)';

COMMIT;

-- VERIFICACION POST-MIGRACION
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'vouchers'
AND column_name IN ('cancelled_by_id', 'cancelled_at', 'cancelled_from_status', 'cancellation_reason')
ORDER BY ordinal_position;
