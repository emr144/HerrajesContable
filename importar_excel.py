import sqlite3
import pandas as pd

def importar_lista():
    # 1. Nos conectamos a la base de datos que creaste
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()

    # --- CREAR TABLAS SI NO EXISTEN ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            contacto TEXT,
            descuento_global REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER,
            codigo_proveedor TEXT,
            descripcion TEXT,
            costo_base REAL,
            coeficiente_ganancia REAL
        )
    ''')

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
        # Pandas lee el Excel y lo convierte en una tabla virtual llamada DataFrame (df)
        df = pd.read_excel('lista_precios.xlsx')
        
        # 4. Recorremos fila por fila el Excel para guardarlo en SQLite
        productos_agregados = 0
        for index, fila in df.iterrows():
            # Insertamos los datos. Usamos 1.6 como coeficiente por defecto (60% de ganancia)
            cursor.execute('''
                INSERT INTO productos (proveedor_id, codigo_proveedor, descripcion, costo_base, coeficiente_ganancia)
                VALUES (?, ?, ?, ?, ?)
            ''', (proveedor_id, str(fila['codigo']), fila['descripcion'], float(fila['costo']), 1.6))
            
            productos_agregados += 1
        
        # Guardamos los cambios
        conexion.commit()
        print(f"¡Éxito! Se agregaron {productos_agregados} productos a la base de datos.")
        
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'lista_precios.xlsx'. Asegúrate de guardarlo en la carpeta HerrajesContable.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        # Siempre cerramos la conexión al terminar
        conexion.close()

if __name__ == '__main__':
    importar_lista()