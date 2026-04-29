import psycopg2
import database # Importamos para obtener la ruta

def aplicar_migracion():
    """Asegura que la tabla de cuentas corrientes exista y tenga las columnas correctas."""
    print("Verificando tabla 'cuenta_corriente_proveedores'...")
    conexion = database.conectar()
    if not conexion:
        print("🚫 No se pudo establecer conexión para la migración de cuentas.")
        return
    cursor = conexion.cursor() # Use cursor from psycopg2 connection

    # 1. Crear la tabla si no existe
    # This table is already created in database.py, so this part is mostly for ensuring columns.
    # If it were to create, it should use PostgreSQL syntax.
    # For now, we'll focus on column checks.

    # 2. Verificar columnas faltantes (Migración de versiones viejas)
    # For PostgreSQL, we query information_schema.columns
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = CURRENT_SCHEMA AND table_name = 'cuenta_corriente_proveedores'
    """)
    columnas_existentes = [info[0] for info in cursor.fetchall()]

    # Si falta 'tipo_cuenta', la agregamos
    if 'tipo_cuenta' not in columnas_existentes:
        try:
            cursor.execute("ALTER TABLE cuenta_corriente_proveedores ADD COLUMN tipo_cuenta TEXT NOT NULL DEFAULT 'Formal'")
            print("✅ Columna 'tipo_cuenta' agregada exitosamente.")
        except psycopg2.Error as e:
            print(f"⚠️ Error intentando agregar columna 'tipo_cuenta': {e}")

    # Ensure FOREIGN KEY is set up correctly if table was created without it
    # This is more complex to alter if it doesn't exist, usually done at table creation.
    # Assuming database.py's crear_base_datos handles initial FKs.
    # If this script is run *after* database.crear_base_datos, it's fine.
    # If it's run *before*, it might create a table without FKs if it didn't exist.
    # Given the context, database.crear_base_datos is the primary table creator.

    conexion.commit()
    conexion.close()
        id_proveedor INTEGER,
        fecha DATE DEFAULT CURRENT_DATE,
        tipo_cuenta TEXT NOT NULL DEFAULT 'Formal',
        tipo_movimiento TEXT NOT NULL,
        monto REAL NOT NULL,
        metodo_pago TEXT,
        descripcion TEXT,
        FOREIGN KEY (id_proveedor) REFERENCES proveedores(id)
    )
    ''')

    # 2. Verificar columnas faltantes (Migración de versiones viejas)
    cursor.execute("PRAGMA table_info(cuenta_corriente_proveedores)")
    columnas_existentes = [info[1] for info in cursor.fetchall()]

    # Si falta 'tipo_cuenta', la agregamos
    if 'tipo_cuenta' not in columnas_existentes:
        try:
            cursor.execute("ALTER TABLE cuenta_corriente_proveedores ADD COLUMN tipo_cuenta TEXT NOT NULL DEFAULT 'Formal'")
            print("✅ Columna 'tipo_cuenta' agregada exitosamente.")
        except Exception as e:
            print(f"⚠️ Error intentando agregar columna: {e}")

    conexion.commit()
    conexion.close()

if __name__ == '__main__':
    aplicar_migracion()