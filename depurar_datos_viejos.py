import psycopg2
import database

def limpiar_coeficientes_residuales():
    print("🧹 Depurando coeficientes de inflación antiguos...")
    conexion = database.conectar()
    if not conexion:
        print("🚫 No se pudo establecer conexión para depurar datos viejos.")
        return
    cursor = conexion.cursor() # Use cursor from psycopg2 connection

    # Reseteamos todos los coeficientes globales para empezar de cero
    cursor.execute("UPDATE proveedores SET descuento_global = 0.0, incremento_global = 0.0")
    
    filas_afectadas = cursor.rowcount
    conexion.commit()
    conexion.close()
    print(f"✅ ¡Limpieza completada! Se resetearon {filas_afectadas} proveedores. Ahora podés cargar los valores correctos desde la pestaña Importar.")

if __name__ == '__main__':
    limpiar_coeficientes_residuales()