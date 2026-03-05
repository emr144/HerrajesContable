import sqlite3

def aplicar_migracion():
    """Crea las tablas para la gestión de pedidos a fábrica si no existen."""
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()

    # Tabla para la cabecera de cada pedido
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos_fabrica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER NOT NULL,
            fecha_creacion TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
            estado TEXT NOT NULL DEFAULT 'PENDIENTE',
            FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
        )
    """)

    # Tabla para el detalle de productos en cada pedido
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos_fabrica_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            unidad_medida TEXT NOT NULL DEFAULT 'Unidad',
            FOREIGN KEY (pedido_id) REFERENCES pedidos_fabrica (id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    """)

    # Migración para añadir la columna unidad_medida si no existe
    try:
        cursor.execute("ALTER TABLE pedidos_fabrica_detalle ADD COLUMN unidad_medida TEXT NOT NULL DEFAULT 'Unidad'")
        print("✅ Columna 'unidad_medida' agregada a la tabla 'pedidos_fabrica_detalle'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️  La columna 'unidad_medida' ya existe en 'pedidos_fabrica_detalle'. No se requiere acción.")
        else:
            raise e

    print("Migración de pedidos a fábrica aplicada correctamente.")
    conexion.commit()
    conexion.close()

if __name__ == '__main__':
    aplicar_migracion()