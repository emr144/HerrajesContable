import sqlite3
import database # Importamos para obtener la ruta

def aplicar_migracion():
    """
    Añade las columnas necesarias para el seguimiento de listas de precios y
    modificaciones de coeficientes.
    Este script se puede ejecutar de forma segura varias veces.
    """
    conexion = sqlite3.connect(database.get_db_path())
    cursor = conexion.cursor()

    def columna_existe(tabla, columna):
        cursor.execute(f"PRAGMA table_info({tabla})")
        return any(row[1] == columna for row in cursor.fetchall())

    # Columnas para 'productos'
    if not columna_existe('productos', 'numero_lista'):
        cursor.execute("ALTER TABLE productos ADD COLUMN numero_lista TEXT")
        print("✅ Columna 'numero_lista' agregada a 'productos'.")
    
    if not columna_existe('productos', 'fecha_lista'):
        cursor.execute("ALTER TABLE productos ADD COLUMN fecha_lista DATE")
        print("✅ Columna 'fecha_lista' agregada a 'productos'.")

    # Columnas para 'proveedores'
    if not columna_existe('proveedores', 'fecha_modif_coeficiente'):
        cursor.execute("ALTER TABLE proveedores ADD COLUMN fecha_modif_coeficiente DATE")
        print("✅ Columna 'fecha_modif_coeficiente' agregada a 'proveedores'.")

    if not columna_existe('proveedores', 'incremento_global'):
        cursor.execute("ALTER TABLE proveedores ADD COLUMN incremento_global REAL DEFAULT 0.0")
        print("✅ Columna 'incremento_global' agregada a 'proveedores'.")

    conexion.commit()
    conexion.close()