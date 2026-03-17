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
    print("Aplicando migraciones a la base de datos 'herrajes.db'...")

    try:
        # Añadir columnas a la tabla 'productos'
        cursor.execute("ALTER TABLE productos ADD COLUMN numero_lista TEXT")
        cursor.execute("ALTER TABLE productos ADD COLUMN fecha_lista DATE")
        print("✅ Columnas 'numero_lista' y 'fecha_lista' agregadas a la tabla 'productos'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️  Las columnas 'numero_lista' y 'fecha_lista' ya existen en 'productos'. No se requiere acción.")
        else:
            raise e

    try:
        # Añadir columna a la tabla 'proveedores'
        cursor.execute("ALTER TABLE proveedores ADD COLUMN fecha_modif_coeficiente DATE")
        print("✅ Columna 'fecha_modif_coeficiente' agregada a la tabla 'proveedores'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️  La columna 'fecha_modif_coeficiente' ya existe en 'proveedores'. No se requiere acción.")
        else:
            raise e

    conexion.commit()
    conexion.close()
    print("\n✨ Migración completada. La base de datos está actualizada.")

if __name__ == '__main__':
    aplicar_migracion()