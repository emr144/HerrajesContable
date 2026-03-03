import sqlite3
import sys
import os

try:
    import pandas as pd
except ImportError:
    print("❌ ERROR: No tienes instalada la librería 'pandas'.", file=sys.stderr)
    print("Ejecuta en tu terminal: pip install pandas openpyxl", file=sys.stderr)
    sys.exit(1)

def _verificar_y_actualizar_esquema(cursor):
    """Asegura que la tabla tenga la columna 'estado'."""
    cursor.execute("PRAGMA table_info(productos)")
    columnas = [info[1] for info in cursor.fetchall()]
    if 'estado' not in columnas:
        try:
            cursor.execute("ALTER TABLE productos ADD COLUMN estado TEXT DEFAULT 'ACTIVO'")
        except Exception as e:
            print(f"❌ Error al actualizar esquema: {e}", file=sys.stderr)

def importar_lista():
    archivo_excel = 'lista_precios.xlsx'
    db_nombre = 'herrajes.db'

    if not os.path.exists(archivo_excel):
        print(f"❌ ERROR: No se encuentra el archivo '{archivo_excel}'", file=sys.stderr)
        sys.exit(1)

    conexion = sqlite3.connect(db_nombre)
    cursor = conexion.cursor()

    # --- INICIALIZACIÓN DE TABLAS ---
    cursor.execute('''CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, contacto TEXT, descuento_global REAL DEFAULT 0.0)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, proveedor_id INTEGER, codigo_proveedor TEXT NOT NULL,
        descripcion TEXT NOT NULL, costo_base REAL NOT NULL, coeficiente_ganancia REAL NOT NULL,
        iva REAL DEFAULT 0.21, estado TEXT DEFAULT 'ACTIVO', ultima_actualizacion DATE DEFAULT CURRENT_DATE,
        FOREIGN KEY (proveedor_id) REFERENCES proveedores (id))''')

    _verificar_y_actualizar_esquema(cursor)

    # Proveedor por defecto
    cursor.execute("SELECT id FROM proveedores WHERE nombre = 'Proveedor Principal'")
    res = cursor.fetchone()
    if not res:
        cursor.execute("INSERT INTO proveedores (nombre) VALUES ('Proveedor Principal')")
        proveedor_id = cursor.lastrowid
    else:
        proveedor_id = res[0]

    print(f"📂 Leyendo {archivo_excel}...")
    try:
        # Leemos el excel
        df = pd.read_excel(archivo_excel)

        # --- NORMALIZACIÓN DE COLUMNAS (La magia ocurre aquí) ---
        # Pasamos todos los nombres de columnas a minúsculas y quitamos espacios/tildes extraños
        df.columns = df.columns.astype(str).str.lower().str.strip()
        
        # Mapeamos variaciones comunes a nombres que el código entiende
        mapeo = {
            'código': 'codigo', 'codigo': 'codigo',
            'descripción': 'descripcion', 'descripcion': 'descripcion',
            'costo base': 'costo', 'costo': 'costo', 'precio': 'costo'
        }
        df.rename(columns=mapeo, inplace=True)

        # Verificación de columnas obligatorias
        columnas_actuales = df.columns.tolist()
        for col in ['codigo', 'descripcion', 'costo']:
            if col not in columnas_actuales:
                print(f"❌ ERROR: Falta la columna '{col}' en el Excel.", file=sys.stderr)
                print(f"Columnas detectadas: {columnas_actuales}", file=sys.stderr)
                sys.exit(1)

        print("🔄 Procesando productos...")
        cursor.execute("UPDATE productos SET estado = 'INACTIVO'")

        nuevos = 0
        actualizados = 0

        for _, fila in df.iterrows():
            # Extraemos datos limpiando posibles valores nulos
            cod = str(fila['codigo']).strip()
            desc = str(fila['descripcion']).strip()
            try:
                prec = float(fila['costo'])
            except:
                prec = 0.0

            if not cod or cod == 'nan':
                continue

            cursor.execute("SELECT id FROM productos WHERE codigo_proveedor = ?", (cod,))
            existe = cursor.fetchone()

            if existe:
                cursor.execute("""UPDATE productos SET descripcion = ?, costo_base = ?, 
                               estado = 'ACTIVO', ultima_actualizacion = CURRENT_DATE 
                               WHERE codigo_proveedor = ?""", (desc, prec, cod))
                actualizados += 1
            else:
                cursor.execute("""INSERT INTO productos (proveedor_id, codigo_proveedor, descripcion, 
                               costo_base, coeficiente_ganancia, estado) 
                               VALUES (?, ?, ?, ?, ?, 'ACTIVO')""", 
                               (proveedor_id, cod, desc, prec, 1.6))
                nuevos += 1

        conexion.commit()
        print(f"\n✨ ¡IMPORTACIÓN EXITOSA!")
        print(f"✅ Nuevos: {nuevos} | 🔄 Actualizados: {actualizados}")

    except PermissionError:
        print("❌ ERROR: El Excel está abierto. Ciérralo y reintenta.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conexion.close()

if __name__ == '__main__':
    importar_lista()