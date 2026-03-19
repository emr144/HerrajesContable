import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
import database

def iniciar_configuracion():
    root = tk.Tk()
    root.withdraw() # Ocultar ventana principal

    respuesta = messagebox.askyesno(
        "Configuración de Nube", 
        "¿Es esta la PC PRINCIPAL donde tienes los datos actualmente?\n\n"
        "SÍ: Moveremos tu base de datos a Google Drive.\n"
        "NO: Solo nos conectaremos a una base de datos ya existente en Drive."
    )

    # 1. Seleccionar carpeta de Google Drive
    messagebox.showinfo("Paso 1", "Selecciona tu carpeta sincronizada de Google Drive / OneDrive.")
    carpeta_nube = filedialog.askdirectory(title="Seleccionar Carpeta de Nube")
    
    if not carpeta_nube:
        return

    db_local = "herrajes.db"
    db_nube = os.path.join(carpeta_nube, "herrajes.db")
    ruta_txt = "ruta_db.txt"

    try:
        if respuesta: # ES LA PC PRINCIPAL
            if os.path.exists(db_local):
                # Movemos la DB actual a la nube
                shutil.move(db_local, db_nube)
                messagebox.showinfo("Éxito", f"Base de datos movida a:\n{db_nube}")
            else:
                if not os.path.exists(db_nube):
                    messagebox.showerror("Error", "No se encontró 'herrajes.db' en esta carpeta para mover.")
                    return
        
        # 2. Crear el archivo de enlace
        # Este paso se hace tanto en la PC principal como en las secundarias
        with open(ruta_txt, "w") as f:
            f.write(db_nube)
            
        messagebox.showinfo("¡Listo!", 
            "Configuración completada exitosamente.\n\n"
            "Ahora el programa leerá los datos desde la nube.\n"
            "Para usarlo en otra PC, instala el programa y copia el archivo 'ruta_db.txt' o ejecuta este script y selecciona 'NO' al principio.")

    except Exception as e:
        messagebox.showerror("Error Crítico", f"Ocurrió un error: {e}")

if __name__ == "__main__":
    iniciar_configuracion()
