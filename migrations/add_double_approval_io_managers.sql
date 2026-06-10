-- MIGRACION: Doble aprobacion de vales (jefe directo + contraloria/io manager)
-- Fecha: 2026-06-10
-- Descripcion:
--   1. Crea la tabla io_managers (fuente de verdad de "quien es contralor")
--   2. Agrega el estado PENDING_IO_APPROVAL al enum de status
--   3. Agrega columnas de 2a aprobacion a vouchers
-- Aplica SOLO a una BBDD existente (con esquema viejo). En una BBDD nueva,
-- create_all ya genera todo desde los modelos.
-- Idempotente: usa IF NOT EXISTS / ADD VALUE IF NOT EXISTS. Seguro de re-ejecutar.

BEGIN;

-- 1. Tabla io_managers (contralores). Transversal, sin alcance por empresa.
--    (create_all tambien la crea si falta; aqui es explicita para reproducibilidad.)
CREATE TABLE IF NOT EXISTS io_managers (
    id SERIAL PRIMARY KEY,
    individual_id INTEGER NOT NULL UNIQUE REFERENCES individuals(id) ON DELETE RESTRICT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NULL,
    deleted_at TIMESTAMP NULL,
    created_by INTEGER NULL REFERENCES users(id),
    updated_by INTEGER NULL REFERENCES users(id),
    deleted_by INTEGER NULL REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_io_managers_individual_id ON io_managers(individual_id);

-- 2. Nuevo estado intermedio del enum de status de vouchers
ALTER TYPE voucherstatusenum ADD VALUE IF NOT EXISTS 'PENDING_IO_APPROVAL';

-- 3. Columnas de doble aprobacion en vouchers
ALTER TABLE vouchers
ADD COLUMN IF NOT EXISTS io_approved_by_id INTEGER NULL REFERENCES individuals(id) ON DELETE RESTRICT,
ADD COLUMN IF NOT EXISTS io_approved_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS first_approved_at TIMESTAMP NULL;

CREATE INDEX IF NOT EXISTS idx_vouchers_io_approved_by_id ON vouchers(io_approved_by_id);

-- 4. Comentarios para documentacion
COMMENT ON TABLE io_managers IS 'Contralores (io managers): pertenencia activa habilita la 2a aprobacion de vales';
COMMENT ON COLUMN io_managers.individual_id IS 'Individual que es contralor (unico)';
COMMENT ON COLUMN vouchers.io_approved_by_id IS 'Contralor que dio la 2a aprobacion';
COMMENT ON COLUMN vouchers.io_approved_at IS 'Momento de la 2a aprobacion (contraloria)';
COMMENT ON COLUMN vouchers.first_approved_at IS 'Momento de la 1a aprobacion (jefe directo)';

COMMIT;

-- VERIFICACION POST-MIGRACION
-- a) Estructura de io_managers
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'io_managers'
ORDER BY ordinal_position;

-- b) El enum tiene el nuevo valor
SELECT e.enumlabel
FROM pg_enum e
JOIN pg_type t ON t.oid = e.enumtypid
WHERE t.typname = 'voucherstatusenum'
ORDER BY e.enumsortorder;

-- c) Columnas nuevas en vouchers
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'vouchers'
AND column_name IN ('io_approved_by_id', 'io_approved_at', 'first_approved_at');
