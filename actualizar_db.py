import sqlite3

def actualizar_estructura():
    # 1. Agregamos timeout=30 para que espere si el archivo está ocupado
    conexion = sqlite3.connect('herrajes.db', timeout=30)
    
    # 2. Activamos el modo WAL inmediatamente después de conectar
    # Esto permite que otros procesos lean mientras este script crea la tabla
    conexion.execute("PRAGMA journal_mode=WAL;")
    
    cursor = conexion.cursor()
    
    # Creamos la tabla de clientes formalmente
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
    
    conexion.commit()
    conexion.close()
    print("✅ Tabla de clientes creada con éxito y modo WAL activado.")

if __name__ == "__main__":
    actualizar_estructura()