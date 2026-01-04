"""Script temporal para crear base de datos de prueba."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Conectar a postgres (base de datos por defecto)
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="root",
    host="localhost",
    port="5432"
)

# Configurar autocommit para poder crear DB
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

# Crear base de datos
cursor = conn.cursor()

# Verificar si existe
cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'bpta_db_VALES_TEST'")
exists = cursor.fetchone()

if exists:
    print("[WARN] Base de datos 'bpta_db_VALES_TEST' ya existe")
else:
    cursor.execute("CREATE DATABASE bpta_db_VALES_TEST")
    print("[OK] Base de datos 'bpta_db_VALES_TEST' creada exitosamente")

cursor.close()
conn.close()
