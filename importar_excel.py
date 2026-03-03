import sqlite3
import sys

try:
    import pandas as pd
except ImportError:
    print("❌ ERROR CRÍTICO: No tienes instalada la librería 'pandas'.", file=sys.stderr)
    print("⚠️  SOLUCIÓN: Abre tu terminal (CMD) y escribe:", file=sys.stderr)
    print("pip install pandas openpyxl", file=sys.stderr)
    sys.exit(1)

def _verificar_y_actualizar_esquema(cursor):
    """
    Verifica si la tabla 'productos' tiene la columna 'estado'.
    Si no la tiene, la agrega. Esto asegura compatibilidad con bases de datos antiguas.
    """
    cursor.execute("PRAGMA table_info(productos)")
    columnas = [info[1] for info in cursor.fetchall()]
    
    if 'estado' not in columnas:
        print("ADVERTENCIA: La base de datos es de una versión anterior.")
        print("Actualizando la tabla 'productos' para agregar la columna 'estado'...")
        try:
            # Agregamos la columna que falta para manejar productos activos/inactivos
            cursor.execute("ALTER TABLE productos ADD COLUMN estado TEXT DEFAULT 'ACTIVO'")
            print("✅ Tabla 'productos' actualizada con éxito.")
        except Exception as e:
            print(f"❌ No se pudo actualizar la tabla 'productos': {e}", file=sys.stderr)
            # Salimos si no podemos actualizar el esquema, porque el resto del script fallará.
            sys.exit(1)

def importar_lista():
    # 1. Nos conectamos a la base de datos que creaste
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()

    # --- CREAR/ACTUALIZAR TABLAS (con el esquema más reciente) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            contacto TEXT,
            descuento_global REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER,
            codigo_proveedor TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            costo_base REAL NOT NULL,
            coeficiente_ganancia REAL NOT NULL,
            iva REAL DEFAULT 0.21,
            estado TEXT DEFAULT 'ACTIVO',
            ultima_actualizacion DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
        )
    ''')

    # Verificamos y reparamos la tabla 'productos' si es una versión antigua
    _verificar_y_actualizar_esquema(cursor)

    # 2. Creamos un proveedor genérico si no existe (para cumplir con tu diseño de base de datos)
    cursor.execute("SELECT id FROM proveedores WHERE nombre = 'Proveedor Principal'")
    proveedor = cursor.fetchone()
    
    if not proveedor:
        cursor.execute("INSERT INTO proveedores (nombre, contacto, descuento_global) VALUES ('Proveedor Principal', 'Vendedor de prueba', 0.0)")
        proveedor_id = cursor.lastrowid
    else:
        proveedor_id = proveedor[0]

    # 3. Intentamos leer el Excel
    print("Leyendo el archivo Excel...")
    try:
        try:
            # Pandas lee el Excel y lo convierte en una tabla virtual llamada DataFrame (df)
            df = pd.read_excel('lista_precios.xlsx')
        except ImportError as e:
            if "openpyxl" in str(e):
                print("❌ ERROR: Falta instalar 'openpyxl' para leer archivos .xlsx", file=sys.stderr)
                print("👉 Ejecuta: pip install openpyxl", file=sys.stderr)
                sys.exit(1)
            raise e
        except PermissionError:
            print("❌ ERROR: El archivo Excel está abierto. Ciérralo e intenta de nuevo.", file=sys.stderr)
            sys.exit(1)
        
        # --- NUEVA LÓGICA: MARCAR TODO COMO INACTIVO PRIMERO ---
        print("Paso 1: Marcando todos los productos como inactivos...")
        cursor.execute("UPDATE productos SET estado = 'INACTIVO'")
        print(f"Paso 2: Actualizando la base de datos con {len(df)} productos del Excel...")

        # 4. Recorremos fila por fila el Excel para guardarlo en SQLite
        productos_nuevos = 0
        productos_actualizados = 0
        for index, fila in df.iterrows():
            codigo = str(fila['codigo'])
            descripcion = fila['descripcion']
            costo = float(fila['costo'])

            # Verificamos si el producto ya existe por su código
            cursor.execute("SELECT id FROM productos WHERE codigo_proveedor = ?", (codigo,))
            producto_existente = cursor.fetchone()

            if producto_existente:
                # Si existe, lo actualizamos (UPDATE) y lo reactivamos
                cursor.execute("UPDATE productos SET descripcion = ?, costo_base = ?, estado = 'ACTIVO' WHERE codigo_proveedor = ?", (descripcion, costo, codigo))
                productos_actualizados += 1
            else:
                # Si no existe, lo insertamos (INSERT) como activo
                cursor.execute('''
                    INSERT INTO productos (proveedor_id, codigo_proveedor, descripcion, costo_base, coeficiente_ganancia, estado)
                    VALUES (?, ?, ?, ?, ?, 'ACTIVO')
                ''', (proveedor_id, codigo, descripcion, costo, 1.6))
                productos_nuevos += 1
        
        cursor.execute("SELECT COUNT(*) FROM productos WHERE estado = 'INACTIVO'")
        productos_descontinuados = cursor.fetchone()[0]

        # Guardamos los cambios
        conexion.commit()
        print(f"\n--- RESUMEN ---")
        print(f"✅ Productos nuevos: {productos_nuevos}")
        print(f"🔄 Productos actualizados: {productos_actualizados}")
        print(f"🗑️ Productos descontinuados (inactivos): {productos_descontinuados}")
        
    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo 'lista_precios.xlsx'.", file=sys.stderr)
        print("Asegúrate de guardarlo en la carpeta HerrajesContable.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Siempre cerramos la conexión al terminar
        conexion.close()

if __name__ == '__main__':
    importar_lista()