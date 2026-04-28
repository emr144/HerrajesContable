import psycopg2
import os
from dotenv import load_dotenv

# Carga la URL desde el archivo .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def conectar():
    """Crea una conexión a Supabase (PostgreSQL)."""
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        return conexion
    except Exception as e:
        print(f"Error al conectar a Supabase: {e}")
        return None

def crear_base_datos():
    conexion = conectar()
    if not conexion:
        print("No se pudo establecer conexión para crear las tablas.")
        return
    
    try:
        cursor = conexion.cursor()

        # 1. Tabla Proveedores
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL UNIQUE,
            contacto TEXT,
            descuento_global NUMERIC(10, 2) DEFAULT 0.0,
            incremento_global NUMERIC(10, 2) DEFAULT 0.0,
            fecha_modif_coeficiente DATE DEFAULT CURRENT_DATE
        )
        ''')

        # 2. Tabla Productos
        # Nota: Usamos NUMERIC para precisión en precios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            proveedor_id INTEGER,
            codigo_proveedor TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            costo_base NUMERIC(12, 2) NOT NULL, 
            coeficiente_ganancia NUMERIC(10, 2) NOT NULL, 
            iva NUMERIC(5, 2) DEFAULT 0.21, 
            estado TEXT DEFAULT 'ACTIVO', 
            ultima_actualizacion DATE DEFAULT CURRENT_DATE,
            numero_lista TEXT,
            fecha_lista DATE,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores (id) ON DELETE SET NULL,
            UNIQUE(proveedor_id, codigo_proveedor)
        )
        ''')

        # 3. Tabla Presupuestos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS presupuestos (
            id SERIAL PRIMARY KEY,
            cliente_nombre TEXT,
            cliente_tipo TEXT DEFAULT 'FINAL', 
            fecha DATE DEFAULT CURRENT_DATE,
            estado TEXT DEFAULT 'BORRADOR', 
            total NUMERIC(12, 2) DEFAULT 0.0
        )
        ''')

        # 4. Tabla Detalle de Presupuestos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS presupuesto_detalles (
            id SERIAL PRIMARY KEY,
            presupuesto_id INTEGER,
            producto_id INTEGER,
            cantidad NUMERIC(10, 2) NOT NULL,
            precio_unitario_congelado NUMERIC(12, 2) NOT NULL, 
            FOREIGN KEY (presupuesto_id) REFERENCES presupuestos (id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos (id) ON DELETE SET NULL
        )
        ''')

        # 5. Tabla Cuenta Corriente Proveedores
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cuenta_corriente_proveedores (
            id SERIAL PRIMARY KEY,
            id_proveedor INTEGER,
            fecha DATE DEFAULT CURRENT_DATE,
            tipo_cuenta TEXT NOT NULL,      -- 'Formal' o 'Informal'
            tipo_movimiento TEXT NOT NULL,  -- 'Factura', 'Pago', 'Saldo Inicial'
            monto NUMERIC(12, 2) NOT NULL,
            metodo_pago TEXT,               -- 'Efectivo', 'Transferencia'
            descripcion TEXT,
            FOREIGN KEY (id_proveedor) REFERENCES proveedores(id) ON DELETE CASCADE
        )
        ''')

        # 6. Tabla Clientes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            email TEXT,
            cuit_dni TEXT
        )
        ''')

        # Inserción de datos iniciales necesarios
        # Cliente por defecto
        cursor.execute("""
            INSERT INTO clientes (id, nombre) 
            VALUES (1, 'Consumidor Final') 
            ON CONFLICT (id) DO NOTHING
        """)

        # Proveedor Fabher por defecto (necesario para cargar tus productos luego)
        cursor.execute("""
            INSERT INTO proveedores (nombre) 
            VALUES ('Fabher') 
            ON CONFLICT (nombre) DO NOTHING
        """)

        conexion.commit()
        print("¡Base de datos en Supabase y tablas creadas/verificadas con éxito!")

    except Exception as e:
        print(f"Error al crear las tablas: {e}")
        conexion.rollback()
    finally:
        cursor.close()
        conexion.close()

if __name__ == '__main__':
    crear_base_datos()