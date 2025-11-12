-- Migration: Add deleted_at and deleted_by to users table
-- Date: 2025-10-03
-- Description: Agrega campos de auditoría completos para soft delete en tabla users

-- Agregar columna deleted_at
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;

-- Agregar columna deleted_by
ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_by INTEGER NULL;

-- Agregar foreign key para deleted_by
ALTER TABLE users ADD CONSTRAINT fk_users_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id);

-- Comentarios en las columnas
COMMENT ON COLUMN users.deleted_at IS 'Fecha y hora de eliminación lógica (soft delete)';
COMMENT ON COLUMN users.deleted_by IS 'Usuario que eliminó el registro (soft delete)';
