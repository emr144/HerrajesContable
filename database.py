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
        print(f"❌ Error al conectar a Supabase: {e}")
        return None

def crear_base_datos():
    conexion = conectar()
    if not conexion:
        print("🚫 No se pudo establecer conexión para crear las tablas.")
        return
    
    cursor = None 
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

        # 2. Tabla Clientes
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

        # 3. Tabla Productos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id SERIAL PRIMARY KEY,
            proveedor_id INTEGER REFERENCES proveedores (id) ON DELETE SET NULL,
            codigo_proveedor TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            costo_base NUMERIC(12, 2) NOT NULL, 
            coeficiente_ganancia NUMERIC(10, 2) NOT NULL, 
            iva NUMERIC(5, 2) DEFAULT 0.21, 
            estado TEXT DEFAULT 'ACTIVO', 
            ultima_actualizacion DATE DEFAULT CURRENT_DATE,
            numero_lista TEXT,
            fecha_lista DATE,
            UNIQUE(proveedor_id, codigo_proveedor)
        )
        ''')

        # 4. Tabla Presupuestos
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

        # 5. Tabla Detalle de Presupuestos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS presupuesto_detalles (
            id SERIAL PRIMARY KEY,
            presupuesto_id INTEGER REFERENCES presupuestos (id) ON DELETE CASCADE,
            producto_id INTEGER REFERENCES productos (id) ON DELETE SET NULL,
            cantidad NUMERIC(10, 2) NOT NULL,
            precio_unitario_congelado NUMERIC(12, 2) NOT NULL
        )
        ''')

        # 6. Tabla Cuenta Corriente Proveedores
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cuenta_corriente_proveedores (
            id SERIAL PRIMARY KEY,
            id_proveedor INTEGER REFERENCES proveedores(id) ON DELETE CASCADE,
            fecha DATE DEFAULT CURRENT_DATE,
            tipo_cuenta TEXT NOT NULL,
            tipo_movimiento TEXT NOT NULL,
            monto NUMERIC(12, 2) NOT NULL,
            metodo_pago TEXT,
            descripcion TEXT
        )
        ''')

        # --- DATOS INICIALES (MÉTODO ULTRA-SEGURO) ---
        
        # Insertar Consumidor Final si no existe
        cursor.execute("""
            INSERT INTO clientes (id, nombre) 
            SELECT 1, 'Consumidor Final'
            WHERE NOT EXISTS (SELECT 1 FROM clientes WHERE id = 1)
        """)

        # Insertar Proveedor Fabher si no existe
        cursor.execute("""
            INSERT INTO proveedores (nombre) 
            SELECT 'Fabher'
            WHERE NOT EXISTS (SELECT 1 FROM proveedores WHERE nombre = 'Fabher')
        """)
        
        # AJUSTE DE SECUENCIA
        cursor.execute("SELECT setval(pg_get_serial_sequence('clientes', 'id'), coalesce(max(id), 1)) FROM clientes")

        conexion.commit()
        print("🚀 ¡Estructura de Supabase verificada y tablas listas!")

    except Exception as e:
        print(f"⚠️ Error al crear las tablas: {e}")
        if conexion:
            conexion.rollback()
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def ejecutar_consulta(query, params=()):
    conn = conectar()
    cursor = None # CRÍTICO: Definir antes del try
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            conn.commit()
        except Exception as e:
            print(f"❌ Error en consulta: {e}")
        finally:
            if cursor:
                cursor.close()
            conn.close()
    return None

if __name__ == '__main__':
    crear_base_datos()