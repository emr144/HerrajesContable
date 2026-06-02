import psycopg2
import sqlite3
import os
from dotenv import load_dotenv

# === CONFIGURACIÓN ===
# Intenta cargar la URL desde el archivo .env si existe
load_dotenv()

# Si no está en el .env, puedes pegarla aquí manualmente
DATABASE_URL = os.getenv("DATABASE_URL") or "TU_URL_DE_SUPABASE_AQUI"
DB_LOCAL = "herrajes.db"

def migrar_datos():
    print("🔌 Conectando a Supabase (PostgreSQL)...")
    try:
        conn_pg = psycopg2.connect(DATABASE_URL)
        cur_pg = conn_pg.cursor()
    except Exception as e:
        print(f"❌ Error al conectar con Supabase: {e}")
        return

    print("📂 Conectando a Base de Datos Local (SQLite)...")
    conn_sl = sqlite3.connect(DB_LOCAL)
    cur_sl = conn_sl.cursor()

    # Lista de tablas a copiar en orden para respetar claves foráneas
    tablas = [
        "proveedores",
        "clientes",
        "productos",
        "presupuestos",
        "presupuesto_detalles",
        "cuenta_corriente_proveedores",
        "pedidos_fabrica",
        "pedidos_fabrica_detalle"
    ]

    for tabla in tablas:
        print(f"--- Migrando tabla: {tabla} ---")
        try:
            # 1. Obtener datos de Supabase
            cur_pg.execute(f"SELECT * FROM {tabla}")
            filas = cur_pg.fetchall()
            
            if not filas:
                print(f"   ℹ️ La tabla {tabla} está vacía en la nube.")
                continue

            # Obtener nombres de columnas
            colnames = [desc[0] for desc in cur_pg.description]
            
            # 2. Limpiar tabla local antes de insertar para evitar duplicados
            cur_sl.execute(f"DELETE FROM {tabla}")
            
            # 3. Preparar insert para SQLite
            placeholders = ", ".join(["?"] * len(colnames))
            columnas_str = ", ".join(colnames)
            query_insert = f"INSERT INTO {tabla} ({columnas_str}) VALUES ({placeholders})"
            
            # 4. Insertar datos
            cur_sl.executemany(query_insert, filas)
            conn_sl.commit()
            print(f"   ✅ {len(filas)} registros migrados.")
            
        except Exception as e:
            print(f"   ⚠️ Error en tabla {tabla}: {e}")
            conn_sl.rollback()

    cur_pg.close()
    conn_pg.close()
    cur_sl.close()
    conn_sl.close()
    print("\n==========================================")
    print("✨ MIGRACIÓN COMPLETADA CON ÉXITO")
    print("Ahora puedes abrir tu programa y ver tus datos.")
    print("==========================================")

if __name__ == "__main__":
    if not DATABASE_URL or "TU_URL_DE_SUPABASE_AQUI" in DATABASE_URL:
        print("❌ ERROR: No se encontró la DATABASE_URL de Supabase.")
        print("Asegúrate de tener un archivo .env con la variable DATABASE_URL o pégala manualmente en el script.")
    else:
        migrar_datos()