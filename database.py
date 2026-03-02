import sqlite3

def crear_base_datos():
    # Esto crea un archivo llamado 'herrajes.db' en tu carpeta actual
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()

    # 1. Tabla Proveedores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        contacto TEXT,
        descuento_global REAL DEFAULT 0.0 -- Ej: 0.10 para un 10% de descuento de gremio que te hacen a vos
    )
    ''')

    # 2. Tabla Productos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proveedor_id INTEGER,
        codigo_proveedor TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        costo_base REAL NOT NULL, -- Precio de lista del proveedor SIN IVA
        coeficiente_ganancia REAL NOT NULL, -- Tu remarcación (Ej: 1.5 para ganar el 50%)
        iva REAL DEFAULT 0.21, -- 21% de IVA por defecto
        estado TEXT DEFAULT 'ACTIVO', -- Por si dejan de fabricarlo
        ultima_actualizacion DATE DEFAULT CURRENT_DATE,
        FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
    )
    ''')

    # 3. Tabla Presupuestos (Cabecera)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS presupuestos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_nombre TEXT,
        cliente_tipo TEXT DEFAULT 'FINAL', -- 'FINAL' o 'GREMIO' (para cobrar distinto)
        fecha DATE DEFAULT CURRENT_DATE,
        estado TEXT DEFAULT 'BORRADOR', -- BORRADOR, ENVIADO, APROBADO
        total REAL DEFAULT 0.0
    )
    ''')

    # 4. Tabla Detalle de Presupuestos (Los items adentro del presupuesto)
    # MUY IMPORTANTE: Acá guardamos el 'precio_unitario_congelado'. 
    # Si mañana aumenta el producto, el presupuesto viejo no debe cambiar de precio.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS presupuesto_detalles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        presupuesto_id INTEGER,
        producto_id INTEGER,
        cantidad REAL NOT NULL,
        precio_unitario_congelado REAL NOT NULL, 
        FOREIGN KEY (presupuesto_id) REFERENCES presupuestos (id),
        FOREIGN KEY (producto_id) REFERENCES productos (id)
    )
    ''')

    conexion.commit()
    conexion.close()
    print("¡Base de datos 'herrajes.db' y tablas creadas con éxito!")

if __name__ == '__main__':
    crear_base_datos()