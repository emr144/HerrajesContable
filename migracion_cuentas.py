import sqlite3

def aplicar_migracion():
    """Asegura que la tabla de cuentas corrientes exista y tenga las columnas correctas."""
    print("Verificando tabla 'cuenta_corriente_proveedores'...")
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()

    # 1. Crear la tabla si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cuenta_corriente_proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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