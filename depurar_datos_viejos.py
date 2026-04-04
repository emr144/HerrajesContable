import sqlite3
import database

def limpiar_coeficientes_residuales():
    print("🧹 Depurando coeficientes de inflación antiguos...")
    conexion = sqlite3.connect(database.get_db_path())
    cursor = conexion.cursor()

    # Reseteamos todos los coeficientes globales para empezar de cero
    cursor.execute("UPDATE proveedores SET descuento_global = 0.0, incremento_global = 0.0")
    
    filas_afectadas = cursor.rowcount
    conexion.commit()
    conexion.close()
    print(f"✅ ¡Limpieza completada! Se resetearon {filas_afectadas} proveedores. Ahora podés cargar los valores correctos desde la pestaña Importar.")

if __name__ == '__main__':
    limpiar_coeficientes_residuales()