import sqlite3
import os
import sys

def get_db_path():
    r"""
    Devuelve la ruta completa a la base de datos.
    Configurada para usar Google Drive: "G:\Mi unidad\DbHerrajesDrive\herrajes.db"
    """
    # --- RUTA DE GOOGLE DRIVE ---
    ruta_drive = r"G:\Mi unidad\DbHerrajesDrive\herrajes.db"
    
    # Si la carpeta existe, usamos esta ruta
    if os.path.exists(os.path.dirname(ruta_drive)):
        # LIMPIEZA: Intentamos borrar la DB local vieja si existe
        try:
            if getattr(sys, 'frozen', False):
                local_dir = os.path.dirname(sys.executable)
            else:
                local_dir = os.path.dirname(os.path.abspath(__file__))
            
            db_vieja = os.path.join(local_dir, 'herrajes.db')
            
            # Verificamos que no sea la misma ruta antes de borrar para no borrar la del drive
            if os.path.exists(db_vieja) and os.path.abspath(db_vieja).lower() != os.path.abspath(ruta_drive).lower():
                os.remove(db_vieja)
                print("🗑️ Base de datos local antigua eliminada.")
        except: pass
        
        return ruta_drive
    
    # --- FALLBACK: Si no encuentra la carpeta Drive, usa local ---
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), 'herrajes.db')
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'herrajes.db')

def crear_base_datos():
    conexion = sqlite3.connect(get_db_path())
    cursor = conexion.cursor()

    # 1. Tabla Proveedores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        contacto TEXT,
        descuento_global REAL DEFAULT 0.0,
        incremento_global REAL DEFAULT 0.0,
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