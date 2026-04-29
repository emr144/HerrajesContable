import psycopg2
import database # Importamos para obtener la ruta

def aplicar_migracion():
    """
    Añade las columnas necesarias para el seguimiento de listas de precios y
    modificaciones de coeficientes.
    """
    conexion = database.conectar()
    if not conexion:
        print("🚫 No se pudo establecer conexión para la migración de listas.")
        return
    cursor = conexion.cursor() # Use cursor from psycopg2 connection

    def columna_existe(tabla, columna):
        cursor.execute(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = CURRENT_SCHEMA AND table_name = '{tabla}' AND column_name = '{columna}'
        """)
        return cursor.fetchone() is not None

    # Columnas para 'productos'
    if not columna_existe('productos', 'numero_lista'):
        cursor.execute("ALTER TABLE productos ADD COLUMN numero_lista TEXT") # This is fine for PostgreSQL
        print("✅ Columna 'numero_lista' agregada a 'productos'.")
    
    if not columna_existe('productos', 'fecha_lista'):
        cursor.execute("ALTER TABLE productos ADD COLUMN fecha_lista DATE") # This is fine for PostgreSQL
        print("✅ Columna 'fecha_lista' agregada a 'productos'.")

    # Columnas para 'proveedores'
    if not columna_existe('proveedores', 'fecha_modif_coeficiente'):
        cursor.execute("ALTER TABLE proveedores ADD COLUMN fecha_modif_coeficiente DATE") # This is fine for PostgreSQL
        print("✅ Columna 'fecha_modif_coeficiente' agregada a 'proveedores'.")

    if not columna_existe('proveedores', 'incremento_global'):
        cursor.execute("ALTER TABLE proveedores ADD COLUMN incremento_global NUMERIC(10, 2) DEFAULT 0.0") # Use NUMERIC for PostgreSQL
        print("✅ Columna 'incremento_global' agregada a 'proveedores'.")

    conexion.commit()
    conexion.close()