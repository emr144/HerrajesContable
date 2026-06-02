import sqlite3
import database # Importamos para obtener la ruta

def aplicar_migracion():
    """Asegura que la tabla de cuentas corrientes exista y tenga las columnas correctas."""
    print("Verificando tabla 'cuenta_corriente_proveedores'...")
    conexion = database.conectar()
    if not conexion:
        print("🚫 No se pudo establecer conexión para la migración de cuentas.")
        return
    cursor = conexion.cursor()

    # 1. Crear la tabla si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuenta_corriente_proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_proveedor INTEGER REFERENCES proveedores(id),
            tipo_cuenta TEXT NOT NULL DEFAULT 'Formal',
            tipo_movimiento TEXT NOT NULL,
            monto REAL NOT NULL,
            descripcion TEXT,
            fecha DATE DEFAULT CURRENT_DATE
        )
    """)

    # 2. Verificar columnas faltantes para SQLite
    cursor.execute("PRAGMA table_info(cuenta_corriente_proveedores)")
    columnas_existentes = [info[1] for info in cursor.fetchall()]

    # Si falta 'tipo_cuenta', la agregamos
    if 'tipo_cuenta' not in columnas_existentes:
        try:
            cursor.execute("ALTER TABLE cuenta_corriente_proveedores ADD COLUMN tipo_cuenta TEXT NOT NULL DEFAULT 'Formal'")
            print("✅ Columna 'tipo_cuenta' agregada exitosamente.")
        except sqlite3.Error as e:
            print(f"⚠️ Error intentando agregar columna 'tipo_cuenta': {e}")

    # Ensure FOREIGN KEY is set up correctly if table was created without it
    # This is more complex to alter if it doesn't exist, usually done at table creation.
    # Assuming database.py's crear_base_datos handles initial FKs.
    # If this script is run *after* database.crear_base_datos, it's fine.
    # If it's run *before*, it might create a table without FKs if it didn't exist.
    # Given the context, database.crear_base_datos is the primary table creator.

    conexion.commit()
    conexion.close()


if __name__ == '__main__':
    aplicar_migracion()