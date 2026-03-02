import sqlite3
import tkinter as tk
from tkinter import messagebox
import os

try:
    from PIL import Image, ImageTk
except ImportError:
    # Creamos una ventana oculta temporal solo para mostrar el error
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error de Librería", "Falta instalar la librería 'Pillow'.\n\nPor favor ejecuta en la terminal:\npip install pillow")
    exit()

def buscar_producto(event=None):
    # 1. Obtenemos el texto escrito y lo limpiamos
    codigo_buscado = entrada_codigo.get().strip().upper() 
    
    if not codigo_buscado:
        return 

    # 2. Conexión a la base de datos
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT descripcion, costo_base, coeficiente_ganancia, iva 
        FROM productos WHERE codigo_proveedor = ?
    ''', (codigo_buscado,))
    producto = cursor.fetchone()
    conexion.close()

    # 3. Actualización de la interfaz
    if producto:
        desc, costo, coef, iva = producto
        precio_final = costo * coef * (1 + iva)
        
        label_desc.config(text=desc)
        label_codigo.config(text=f"Código: {codigo_buscado}")
        label_precio.config(text=f"Precio Venta: $ {precio_final:.2f}")

        # Buscamos la foto en la carpeta que creamos
        ruta_imagen = f"imagenes_productos/{codigo_buscado}.jpg"
        if os.path.exists(ruta_imagen):
            try:
                img = Image.open(ruta_imagen)
                img.thumbnail((250, 250))
                img_tk = ImageTk.PhotoImage(img)
                label_imagen.config(image=img_tk, text="") 
                label_imagen.image = img_tk 
            except Exception:
                label_imagen.config(image='', text="[ Error al cargar imagen ]", fg="red")
        else:
            label_imagen.config(image='', text="[ Sin imagen disponible ]", fg="red")
    else:
        messagebox.showwarning("No encontrado", f"El código '{codigo_buscado}' no existe.")

# --- Configuración Visual ---
ventana = tk.Tk()
ventana.title("Buscador de Productos - HerrajesContable")
ventana.geometry("450x550")
ventana.config(padx=20, pady=20)

frame_buscador = tk.Frame(ventana)
frame_buscador.pack(pady=10)

tk.Label(frame_buscador, text="Código:").pack(side=tk.LEFT, padx=5)

entrada_codigo = tk.Entry(frame_buscador, font=("Arial", 12), width=12)
entrada_codigo.pack(side=tk.LEFT, padx=5)
# Esto hace que el Enter dispare la búsqueda
entrada_codigo.bind('<Return>', buscar_producto)

btn_buscar = tk.Button(frame_buscador, text="Buscar", command=buscar_producto, 
                       bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
btn_buscar.pack(side=tk.LEFT, padx=5)

tk.Frame(ventana, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=15)

label_desc = tk.Label(ventana, text="---", font=("Arial", 16, "bold"))
label_desc.pack(pady=5)

label_codigo = tk.Label(ventana, text="Código: ---", font=("Arial", 12, "italic"), fg="gray")
label_codigo.pack()

label_precio = tk.Label(ventana, text="Precio Venta: $ 0.00", font=("Arial", 18, "bold"), fg="darkgreen")
label_precio.pack(pady=10)

label_imagen = tk.Label(ventana, text="[ Ingrese código ]", font=("Arial", 12), fg="gray")
label_imagen.pack(pady=10)

if __name__ == '__main__':
    ventana.mainloop()