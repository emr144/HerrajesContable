import sqlite3
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def obtener_url_supabase():
    """Devuelve la URL de Supabase desde el .env si existe."""
    return os.getenv("DATABASE_URL") or None


def conectar_supabase():
    """Crea la conexión a Supabase usando la URL configurada."""
    url = obtener_url_supabase()
    if not url or "TU_URL_DE_SUPABASE_AQUI" in url:
        print("⚠️ No hay DATABASE_URL válida para Supabase.")
        return None
    try:
        return psycopg2.connect(url)
    except Exception as e:
        print(f"⚠️ Error al conectar con Supabase: {e}")
        return None


def sincronizar_cuenta_corriente_proveedores():
    """Trae los movimientos de cuenta corriente desde Supabase y los replica en SQLite."""
    conn_pg = conectar_supabase()
    if not conn_pg:
        return False

    conn_sl = None
    try:
        with conn_pg.cursor() as cur_pg:
            cur_pg.execute("""
                SELECT id, id_proveedor, fecha, tipo_cuenta, tipo_movimiento, monto, metodo_pago, descripcion
                FROM cuenta_corriente_proveedores
                ORDER BY id
            """)
            filas = cur_pg.fetchall()

        conn_sl = conectar()
        if not conn_sl:
            return False

        cursor = conn_sl.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS cuenta_corriente_proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER REFERENCES proveedores (id) ON DELETE CASCADE,
            tipo_cuenta TEXT NOT NULL,
            tipo_movimiento TEXT NOT NULL,
            monto REAL NOT NULL,
            descripcion TEXT,
            fecha DATE NOT NULL,
            metodo_pago TEXT)''')

        cursor.execute("PRAGMA table_info(cuenta_corriente_proveedores)")
        columnas_existentes = [info[1] for info in cursor.fetchall()]
        if 'tipo_cuenta' not in columnas_existentes:
            cursor.execute("ALTER TABLE cuenta_corriente_proveedores ADD COLUMN tipo_cuenta TEXT NOT NULL DEFAULT 'Formal'")
        if 'metodo_pago' not in columnas_existentes:
            cursor.execute("ALTER TABLE cuenta_corriente_proveedores ADD COLUMN metodo_pago TEXT")
        if 'proveedor_id' not in columnas_existentes and 'id_proveedor' in columnas_existentes:
            cursor.execute("ALTER TABLE cuenta_corriente_proveedores RENAME COLUMN id_proveedor TO proveedor_id")

        for row in filas:
            row_id, id_proveedor, fecha, tipo_cuenta, tipo_movimiento, monto, metodo_pago, descripcion = row
            cursor.execute("""
                INSERT INTO cuenta_corriente_proveedores (id, proveedor_id, fecha, tipo_cuenta, tipo_movimiento, monto, metodo_pago, descripcion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    proveedor_id = excluded.proveedor_id,
                    fecha = excluded.fecha,
                    tipo_cuenta = excluded.tipo_cuenta,
                    tipo_movimiento = excluded.tipo_movimiento,
                    monto = excluded.monto,
                    metodo_pago = excluded.metodo_pago,
                    descripcion = excluded.descripcion
            """, (row_id, id_proveedor, fecha, tipo_cuenta, tipo_movimiento, monto, metodo_pago, descripcion))

        conn_sl.commit()
        print(f"✅ Sincronizados {len(filas)} movimientos desde Supabase.")
        return True
    except Exception as e:
        print(f"❌ Error sincronizando cuenta_corriente_proveedores: {e}")
        if conn_sl:
            conn_sl.rollback()
        return False
    finally:
        if conn_pg:
            conn_pg.close()
        if conn_sl:
            conn_sl.close()

def obtener_ruta_bd():
    """
    Determina la ruta absoluta de la base de datos.
    Busca primero una configuración en 'ruta_db.txt' y, si no existe,
    usa 'herrajes.db' en el directorio del ejecutable o script.
    """
    # 1. Detectar directorio base (donde está el .exe o el script .py)
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    # 2. Verificar si existe configuración de Nube/Drive
    ruta_txt = os.path.join(base_path, "ruta_db.txt")
    if os.path.exists(ruta_txt):
        try:
            with open(ruta_txt, "r") as f:
                cloud_path = f.read().strip().strip('"')
                if cloud_path and os.path.exists(cloud_path):
                    return cloud_path
        except Exception as e:
            print(f"⚠️ Error leyendo ruta_db.txt: {e}")

    # 3. Retornar ruta local por defecto
    return os.path.join(base_path, "herrajes.db")

class DatabaseManager:
    def __init__(self):
        self.url = obtener_ruta_bd()

    def conectar(self):
        """Crea una conexión a SQLite local."""
        try:
            # Recalculamos la ruta en cada conexión por si el archivo de config cambió
            return sqlite3.connect(obtener_ruta_bd())
        except Exception as e:
            print(f"❌ Error al conectar a SQLite: {e}")
            return None

    def table(self, nombre_tabla):
        """Interfaz para compatibilidad con el resto del sistema"""
        return TableHelper(self, nombre_tabla)

    def ejecutar_consulta(self, query, params=()):
        conn = self.conectar()
        if not conn: return None
        cursor = None
        try:
            # Adaptamos los placeholders de %s (PostgreSQL) a ? (SQLite) e ILIKE a LIKE
            query = query.replace("%s", "?").replace("ILIKE", "LIKE")
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

# Alias para mantener compatibilidad con el resto de los módulos
SupabaseManager = DatabaseManager

class TableHelper:
    def __init__(self, manager, table_name):
        self.manager = manager
        self.table_name = table_name
        self.query = ""
        self.params = []

    def select(self, columns):
        self.query = f"SELECT {columns} FROM {self.table_name}"
        return self

    def order(self, column):
        self.query += f" ORDER BY {column}"
        return self

    def execute(self):
        res = self.manager.ejecutar_consulta(self.query, self.params)
        # Formateo básico para mantener compatibilidad
        if res and "id, nombre" in self.query:
            return ResultHelper([{"id": r[0], "nombre": r[1]} for r in res])
        return ResultHelper(res if res else [])

    def upsert(self, data_list):
        """Inserta o actualiza en bloque (SQLite Syntax)."""
        if not data_list: return self
        conn = self.manager.conectar()
        if not conn: return self
        cursor = conn.cursor()
        try:
            for item in data_list:
                cols = ", ".join(item.keys())
                vals = ", ".join(["?"] * len(item))
                
                # Identificamos el target del conflicto según la tabla para SQLite
                conflict_target = ""
                if self.table_name == "productos":
                    conflict_target = "proveedor_id, codigo_proveedor"
                elif self.table_name == "proveedores":
                    conflict_target = "nombre"
                
                if conflict_target:
                    keys_to_update = [k for k in item.keys() if k not in conflict_target.split(", ")]
                    updates = ", ".join([f"{k} = excluded.{k}" for k in keys_to_update])
                    query = f"""
                        INSERT INTO {self.table_name} ({cols}) 
                        VALUES ({vals}) 
                        ON CONFLICT ({conflict_target}) 
                        DO UPDATE SET {updates}
                    """
                else:
                    query = f"INSERT OR REPLACE INTO {self.table_name} ({cols}) VALUES ({vals})"

                cursor.execute(query, list(item.values()))
            
            conn.commit()
            print(f"✅ Sincronización exitosa en {self.table_name}")
        except Exception as e:
            print(f"❌ Error en upsert: {e}")
            conn.rollback()
            raise e 
        finally:
            cursor.close()
            conn.close()
        return self

class ResultHelper:
    def __init__(self, data):
        self.data = data

# --- Instancia global para ser usada por otros archivos ---
db = DatabaseManager()

def conectar():
    """Función de acceso directo para otros módulos"""
    return db.conectar()

def crear_base_datos():
    """Inicializa las tablas si no existen en SQLite"""
    conexion = conectar()
    if not conexion: return
    cursor = conexion.cursor()
    try:
        # Tabla Proveedores
        cursor.execute('''CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nombre TEXT NOT NULL UNIQUE, 
            contacto TEXT,
            descuento_global REAL DEFAULT 0.0, 
            incremento_global REAL DEFAULT 0.0,
            fecha_modif_coeficiente DATE DEFAULT CURRENT_DATE)''')

        # Tabla Productos
        cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            proveedor_id INTEGER REFERENCES proveedores (id) ON DELETE SET NULL,
            codigo_proveedor TEXT NOT NULL, 
            descripcion TEXT NOT NULL, 
            costo_base REAL NOT NULL, 
            coeficiente_ganancia REAL NOT NULL, 
            iva REAL DEFAULT 0.21, 
            estado TEXT DEFAULT 'ACTIVO', 
            ultima_actualizacion DATE DEFAULT CURRENT_DATE,
            numero_lista TEXT, 
            fecha_lista DATE, 
            UNIQUE(proveedor_id, codigo_proveedor))''')

        # Tabla Cuenta Corriente Proveedores
        cursor.execute('''CREATE TABLE IF NOT EXISTS cuenta_corriente_proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER REFERENCES proveedores (id) ON DELETE CASCADE,
            tipo_cuenta TEXT NOT NULL,
            tipo_movimiento TEXT NOT NULL,
            monto REAL NOT NULL,
            descripcion TEXT,
            fecha DATE NOT NULL,
            metodo_pago TEXT)''')

        cursor.execute("PRAGMA table_info(cuenta_corriente_proveedores)")
        columnas_existentes = [info[1] for info in cursor.fetchall()]
        if 'tipo_cuenta' not in columnas_existentes:
            cursor.execute("ALTER TABLE cuenta_corriente_proveedores ADD COLUMN tipo_cuenta TEXT NOT NULL DEFAULT 'Formal'")
        if 'metodo_pago' not in columnas_existentes:
            cursor.execute("ALTER TABLE cuenta_corriente_proveedores ADD COLUMN metodo_pago TEXT")

        conexion.commit()
        print("🚀 Estructura de SQLite verificada.")
    except Exception as e:
        print(f"⚠️ Aviso en inicialización: {e}")
        conexion.rollback()
    finally:
        cursor.close()
        conexion.close()

# Aseguramos la creación de tablas al importar/iniciar
crear_base_datos()