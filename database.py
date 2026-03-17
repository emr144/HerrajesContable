import sqlite3
import os
import sys

def get_db_path():
    """
    Devuelve la ruta completa a la base de datos.
    La crea en AppData para evitar problemas de permisos en C:\Program Files.
    """
    # 1. Determinar dónde estamos ejecutando (Script o EXE)
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Verificar si ya existe una base de datos local (Tu caso actual)
    local_db = os.path.join(base_path, 'herrajes.db')
    
    # Intentamos ver si la local existe y es escribible
    if os.path.exists(local_db):
        try:
            # Prueba rápida de escritura
            f = open(local_db, 'a'); f.close()
            return local_db # Si funciona, usamos la local (Recuperas tus datos)
        except PermissionError:
            pass # Si falla (está en Program Files), seguimos a AppData

    # 3. Si no hay local o no se puede escribir, usar AppData (Modo Instalado Seguro)
    app_data_dir = os.getenv('APPDATA')
    if not app_data_dir:
        return local_db
    
    herrajes_dir = os.path.join(app_data_dir, 'HerrajesContable')
    os.makedirs(herrajes_dir, exist_ok=True)
    
    return os.path.join(herrajes_dir, 'herrajes.db')

def crear_base_datos():
    conexion = sqlite3.connect(get_db_path())
    cursor = conexion.cursor()

    # 1. Tabla Proveedores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        contacto TEXT,
        descuento_global REAL DEFAULT 0.0, -- Ej: 0.10 para un 10% de descuento de gremio que te hacen a vos
        fecha_modif_coeficiente DATE
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
        numero_lista TEXT,
        fecha_lista DATE,
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

    # Nueva Tabla para Cuentas Corrientes de Fábricas (Proveedores)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cuenta_corriente_proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_proveedor INTEGER,
        fecha DATE DEFAULT CURRENT_DATE,
        tipo_cuenta TEXT NOT NULL,      -- 'Formal' o 'Informal'
        tipo_movimiento TEXT NOT NULL,  -- 'Factura', 'Pago', 'Saldo Inicial'
        monto REAL NOT NULL,
        metodo_pago TEXT,               -- 'Efectivo', 'Transferencia' o 'N/A'
        descripcion TEXT,
        FOREIGN KEY (id_proveedor) REFERENCES proveedores(id)
    )
    ''')

    # 5. Tabla Clientes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT,
        direccion TEXT,
        email TEXT,
        cuit_dni TEXT
    )
    ''')
    # Insertamos un cliente por defecto
    cursor.execute("INSERT OR IGNORE INTO clientes (id, nombre) VALUES (1, 'Consumidor Final')")

    conexion.commit()
    conexion.close()
    print("¡Base de datos 'herrajes.db' y tablas creadas con éxito!")

if __name__ == '__main__':
    crear_base_datos()