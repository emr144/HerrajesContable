import psycopg2
import os
from dotenv import load_dotenv

# Carga la URL desde el archivo .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

class SupabaseManager:
    def __init__(self):
        self.url = DATABASE_URL

    def conectar(self):
        """Crea una conexión a Supabase (PostgreSQL)."""
        try:
            return psycopg2.connect(DATABASE_URL)
        except Exception as e:
            print(f"❌ Error al conectar a Supabase: {e}")
            return None

    def table(self, nombre_tabla):
        """Simulador de interfaz para compatibilidad con el importador"""
        return TableHelper(self, nombre_tabla)

    def ejecutar_consulta(self, query, params=()):
        conn = self.conectar()
        if not conn: return None
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error en consulta: {e}")
            if conn: conn.rollback()
            return None
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

class TableHelper:
    def __init__(self, manager, table_name):
        self.manager = manager
        self.table_name = table_name

    def select(self, columns):
        self.query = f"SELECT {columns} FROM {self.table_name}"
        return self

    def order(self, column):
        self.query += f" ORDER BY {column}"
        return self

    def execute(self):
        res = self.manager.ejecutar_consulta(self.query)
        if "id, nombre" in self.query:
            return ResultHelper([{"id": r[0], "nombre": r[1]} for r in res] if res else [])
        return ResultHelper(res)

    def update(self, data):
        sets = ", ".join([f"{k} = %s" for k in data.keys()])
        self.query = f"UPDATE {self.table_name} SET {sets}"
        self.params = list(data.values())
        return self

    def eq(self, column, value):
        self.query += f" WHERE {column} = %s"
        self.params.append(value)
        return self

    def upsert(self, data_list):
        """Inserta o actualiza en bloque asegurando el COMMIT final."""
        if not data_list: return self
        conn = self.manager.conectar()
        if not conn: return self
        cursor = conn.cursor()
        try:
            for item in data_list:
                cols = ", ".join(item.keys())
                vals = ", ".join(["%s"] * len(item))
                updates = ", ".join([f"{k} = EXCLUDED.{k}" for k in item.keys() if k not in ['proveedor_id', 'codigo_proveedor']])
                
                query = f"""
                    INSERT INTO {self.table_name} ({cols}) 
                    VALUES ({vals}) 
                    ON CONFLICT (proveedor_id, codigo_proveedor) 
                    DO UPDATE SET {updates}
                """
                cursor.execute(query, list(item.values()))
            
            conn.commit()
            print(f"✅ Sincronización exitosa en {self.table_name}")
        except Exception as e:
            print(f"❌ Error en upsert: {e}")
            conn.rollback()
            raise e # Lanzamos el error para que la interfaz lo capture
        finally:
            cursor.close()
            conn.close()
        return self

class ResultHelper:
    def __init__(self, data):
        self.data = data

def conectar():
    return db.conectar()

def crear_base_datos():
    conexion = conectar()
    if not conexion: return
    cursor = conexion.cursor()
    try:
        # Tabla Proveedores
        cursor.execute('''CREATE TABLE IF NOT EXISTS proveedores (
            id SERIAL PRIMARY KEY, nombre TEXT NOT NULL UNIQUE, contacto TEXT,
            descuento_global NUMERIC(10, 2) DEFAULT 0.0, incremento_global NUMERIC(10, 2) DEFAULT 0.0,
            fecha_modif_coeficiente DATE DEFAULT CURRENT_DATE)''')

        # Tabla Productos con UNIQUE explícito
        cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
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
            CONSTRAINT productos_uq UNIQUE(proveedor_id, codigo_proveedor))''')

        # Fix de seguridad: Intentar crear la restricción si el CREATE TABLE IF NOT EXISTS no la aplicó
        try:
            cursor.execute("ALTER TABLE productos ADD CONSTRAINT productos_uq UNIQUE(proveedor_id, codigo_proveedor)")
        except:
            conexion.rollback() # Ignorar si ya existe

        cursor.execute("INSERT INTO clientes (id, nombre) SELECT 1, 'Consumidor Final' WHERE NOT EXISTS (SELECT 1 FROM clientes WHERE id = 1)")
        
        conexion.commit()
        print("🚀 Estructura de Supabase verificada.")
    except Exception as e:
        print(f"⚠️ Aviso en inicialización: {e}")
        conexion.rollback()
    finally:
        cursor.close()
        conexion.close()

db = SupabaseManager()