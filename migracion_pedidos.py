import sqlite3
import database # Importamos para obtener la ruta

def aplicar_migracion():
    """Crea las tablas para la gestión de pedidos a fábrica si no existen."""
    conexion = database.conectar()
    if not conexion:
        print("🚫 No se pudo establecer conexión para la migración de pedidos.")
        return
    cursor = conexion.cursor() # Use cursor from psycopg2 connection

    # Tabla para la cabecera de cada pedido
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos_fabrica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER NOT NULL REFERENCES proveedores (id) ON DELETE CASCADE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado TEXT NOT NULL DEFAULT 'PENDIENTE',
            FOREIGN KEY (proveedor_id) REFERENCES proveedores (id) ON DELETE CASCADE
        )
    """)

    # Tabla para el detalle de productos en cada pedido
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos_fabrica_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL REFERENCES pedidos_fabrica (id) ON DELETE CASCADE,
            producto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            unidad_medida TEXT NOT NULL DEFAULT 'Unidad',
            FOREIGN KEY (pedido_id) REFERENCES pedidos_fabrica (id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    """)

    # Verificar si la columna existe antes de intentar agregarla
    cursor.execute("PRAGMA table_info(pedidos_fabrica_detalle)")
    columnas = [row[1] for row in cursor.fetchall()] # row[1] is the column name in PRAGMA table_info
    
    if 'unidad_medida' not in columnas:
        cursor.execute("ALTER TABLE pedidos_fabrica_detalle ADD COLUMN unidad_medida TEXT NOT NULL DEFAULT 'Unidad'")
    conexion.commit()
    conexion.close()

if __name__ == '__main__':
    aplicar_migracion()