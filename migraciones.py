import database
import migracion_cuentas
import migracion_actualizar_listas
import migracion_pedidos

def ejecutar_todas_las_migraciones():
    """
    Ejecuta todas las migraciones de la base de datos para asegurar que la estructura
    esté actualizada.
    """
    print("Iniciando proceso de migración de la base de datos...")
    database.crear_base_datos() # Crea tablas base (proveedores, productos)
    migracion_cuentas.aplicar_migracion()
    migracion_actualizar_listas.aplicar_migracion()
    migracion_pedidos.aplicar_migracion()
    print("Proceso de migración de la base de datos finalizado.")