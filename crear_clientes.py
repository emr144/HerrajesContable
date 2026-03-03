import sqlite3

def crear_tabla():
    try:
        conexion = sqlite3.connect('herrajes.db')
        cursor = conexion.cursor()
        
        # Creamos la tabla de clientes con todos los campos necesarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT,
                direccion TEXT,
                email TEXT,
                cuit_dni TEXT
            )
        ''')
        
        # Opcional: Insertar un cliente por defecto para que no esté vacío
        cursor.execute("INSERT OR IGNORE INTO clientes (id, nombre) VALUES (1, 'Consumidor Final')")
        
        conexion.commit()
        conexion.close()
        print("✅ ÉXITO: La tabla 'clientes' ha sido creada correctamente.")
    except Exception as e:
        print(f"❌ ERROR: No se pudo crear la tabla: {e}")

if __name__ == "__main__":
    crear_tabla()