import sqlite3
import os

def check_db(path, name):
    """
    Verifica un archivo de base de datos SQLite, su tamaño y el número de clientes.
    Retorna el conteo de clientes o None si hay un error.
    """
    if not os.path.exists(path):
        print(f"❌ {name}: No se encontró el archivo en:\n   {path}")
        return None
    
    try:
        # Usar 'with' para asegurar que la conexión se cierre siempre
        with sqlite3.connect(path) as conn:
            c = conn.cursor()
            count = 0
            try:
                c.execute("SELECT COUNT(*) FROM clientes")
                count = c.fetchone()[0]
            except sqlite3.OperationalError:
                # Esto es más específico: ocurre si la tabla 'clientes' no existe.
                count = 0

            size = os.path.getsize(path) / 1024 # KB
            print(f"\n📂 {name}:")
            print(f"   Ruta: {path}")
            print(f"   Tamaño: {size:.1f} KB")
            print(f"   CLIENTES: {count}  <-- Fíjate aquí")
            return count
    except sqlite3.Error as e:
        print(f"⚠️ {name}: Error de base de datos ({e})")
        return None
    except Exception as e:
        print(f"⚠️ {name}: Error inesperado leyendo el archivo ({e})")
        return None

def main():
    """Función principal para ejecutar el diagnóstico de bases de datos."""
    print("--- 🕵️ DIAGNÓSTICO DE BASES DE DATOS ---")

    # 1. Chequear Base de Datos Local
    local_path = os.path.abspath("herrajes.db")
    local_clients = check_db(local_path, "ARCHIVO LOCAL (Carpeta del Proyecto)")

    # 2. Chequear Base de Datos en la Nube
    drive_path = ""
    drive_clients = None
    config_file = "ruta_db.txt"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            drive_path = f.read().strip().strip('"')
        if drive_path:
            drive_clients = check_db(drive_path, "ARCHIVO NUBE (Google Drive)")
        else:
            print(f"\nℹ️ El archivo '{config_file}' está vacío.")
    else:
        print(f"\nℹ️ No hay configuración de Nube ('{config_file}' no existe)")

    # 3. Imprimir Conclusión
    print("\n---------------------------------------")
    print("CONCLUSIÓN:")
    if drive_path and os.path.exists(drive_path):
        print("✅ El programa está configurado para usar el ARCHIVO NUBE.")
        if local_clients is not None and drive_clients is not None and local_clients > drive_clients:
            print("⚠️  ¡ATENCIÓN! El ARCHIVO LOCAL tiene más clientes que el de la NUBE.")
            print("   Para no perder datos, deberías copiar el archivo local y reemplazar el de la nube.")
            print(f"   - Origen: {local_path}")
            print(f"   - Destino: {drive_path}")
        else:
            print("ℹ️  El archivo de la NUBE parece estar actualizado. ¡Todo en orden!")
    elif local_clients is not None:
        print("✅ El programa está usando el ARCHIVO LOCAL.")
        print("   Si quieres usar una base de datos en la nube, crea el archivo 'ruta_db.txt'.")
    else:
        print("❌ No se encontró ninguna base de datos válida. El programa principal podría fallar.")

if __name__ == "__main__":
    main()
