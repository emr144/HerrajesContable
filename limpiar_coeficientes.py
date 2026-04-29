import psycopg2
import database

def limpiar_residuos_db():
    print("🧹 Limpiando valores residuales de inflación en la base de datos...")
    conexion = database.conectar()
    if not conexion:
        print("🚫 No se pudo establecer conexión para limpiar coeficientes.")
        return
    cursor = conexion.cursor() # Use cursor from psycopg2 connection
    # Seteamos a 0 los campos para que no afecten el cálculo hasta que cargues valores nuevos
    cursor.execute("UPDATE proveedores SET descuento_global = 0.0, incremento_global = 0.0")
    conexion.commit()
    conexion.close()
    print("✅ Base de datos depurada. Ya no hay valores antiguos aplicándose.")

if __name__ == '__main__':
    limpiar_residuos_db()