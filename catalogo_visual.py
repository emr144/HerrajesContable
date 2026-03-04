import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
import os
from PIL import Image, ImageTk
import styles as st # Importamos los estilos

def obtener_productos(filtro=""):
    """Consulta la DB buscando por código o por descripción"""
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    query = "SELECT codigo_proveedor, descripcion FROM productos WHERE (codigo_proveedor LIKE ? OR descripcion LIKE ?) AND estado = 'ACTIVO' LIMIT 10"
    cursor.execute(query, (f'%{filtro}%', f'%{filtro}%'))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

def actualizar_sugerencias(event=None):
    """Se ejecuta cada vez que el usuario escribe en la caja de búsqueda"""
    texto = entrada_busqueda.get().strip()
    lista_sugerencias.delete(0, tk.END)
    
    if len(texto) < 2:
        lista_sugerencias.place_forget()
        return

    productos = obtener_productos(texto)
    
    if productos:
        for p in productos:
            lista_sugerencias.insert(tk.END, f"{p[0]} - {p[1]}")
        
        # Posicionamiento dinámico de la lista
        lista_sugerencias.place(x=entrada_busqueda.winfo_x(), 
                                 y=entrada_busqueda.winfo_y() + entrada_busqueda.winfo_height())
        lista_sugerencias.lift()
    else:
        lista_sugerencias.place_forget()

def seleccionar_producto(event=None):
    """Carga el producto seleccionado de la lista"""
    if not lista_sugerencias.curselection():
        return
    
    seleccion = lista_sugerencias.get(lista_sugerencias.curselection())
    codigo = seleccion.split(" - ")[0]
    
    entrada_busqueda.delete(0, tk.END)
    entrada_busqueda.insert(0, codigo)
    lista_sugerencias.place_forget()
    mostrar_detalle(codigo)

def mostrar_detalle(codigo_buscado=None):
    """Muestra la info y la foto en tamaño grande"""
    if not codigo_buscado:
        codigo_buscado = entrada_busqueda.get().strip().upper()

    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT descripcion, costo_base, coeficiente_ganancia, iva 
        FROM productos WHERE codigo_proveedor = ?
    ''', (codigo_buscado,))
    producto = cursor.fetchone()
    conexion.close()

    if producto:
        desc, costo, coef, iva = producto
        precio_final = costo * coef * (1 + iva)
        
        label_desc.config(text=desc)
        label_codigo_info.config(text=f"Código: {codigo_buscado}")
        label_precio.config(text=f"Precio Venta: $ {precio_final:.2f}")

        # --- GESTIÓN DE IMAGEN ---
        ruta_imagen = f"imagenes_productos/{codigo_buscado}.jpg"
        if os.path.exists(ruta_imagen):
            try:
                img = Image.open(ruta_imagen)
                # Redimensionar a 500px manteniendo proporción y alta calidad
                img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                
                label_imagen.config(image=img_tk, text="") 
                label_imagen.image = img_tk 
            except Exception as e:
                label_imagen.config(image='', text=f"[ Error: {e} ]", fg="red")
        else:
            label_imagen.config(image='', text="[ Sin imagen disponible ]", fg="gray")
    else:
        messagebox.showwarning("No encontrado", f"El código '{codigo_buscado}' no existe.")

# --- INTERFAZ GRÁFICA ---
def montar_interfaz(parent):
    global entrada_busqueda, lista_sugerencias, label_desc, label_codigo_info, label_precio, label_imagen
    
    ventana = tk.Frame(parent, bg=st.BG_MAIN)
    ventana.config(padx=25, pady=25) # Mantenemos el padding

    tk.Label(ventana, text="Buscar por Nombre o Código:", font=st.FONT_LABEL, 
             bg=st.BG_MAIN, fg=st.TEXT_SECONDARY).pack(anchor="w")

    frame_busqueda = tk.Frame(ventana, bg=st.BG_MAIN)
    frame_busqueda.pack(fill=tk.X, pady=5)

    entrada_busqueda = tk.Entry(frame_busqueda, font=st.FONT_NORMAL, bg=st.BG_CARD, fg="white", 
                                bd=0, insertbackground="white", width=40)
    entrada_busqueda.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    entrada_busqueda.bind('<KeyRelease>', actualizar_sugerencias)
    entrada_busqueda.bind('<Return>', lambda e: mostrar_detalle())

    btn_buscar = tk.Button(frame_busqueda, text=" 🔍 BUSCAR ", command=mostrar_detalle, **st.estilo_boton(st.ACCENT))
    st.configurar_hover(btn_buscar, st.ACCENT, st.BG_CARD)
    btn_buscar.pack(side=tk.RIGHT)

    # Sugerencias flotantes
    lista_sugerencias = tk.Listbox(ventana, font=st.FONT_NORMAL, height=5, width=60, 
                                   bg=st.BG_CARD, fg="white", selectbackground=st.ACCENT, bd=0)
    lista_sugerencias.bind('<<ListboxSelect>>', seleccionar_producto)

    tk.Frame(ventana, height=2, bg=st.BG_CARD).pack(fill=tk.X, pady=20)

    # Datos del producto
    label_desc = tk.Label(ventana, text="Esperando búsqueda...", font=st.FONT_TITLE, wraplength=550,
                          bg=st.BG_MAIN, fg=st.TEXT_PRIMARY)
    label_desc.pack(pady=5)

    label_codigo_info = tk.Label(ventana, text="Código: ---", font=st.FONT_LABEL, 
                                 bg=st.BG_MAIN, fg=st.TEXT_SECONDARY)
    label_codigo_info.pack()

    label_precio = tk.Label(ventana, text="$ 0.00", font=("Inter", 24, "bold"), 
                            bg=st.BG_MAIN, fg=st.ACCENT)
    label_precio.pack(pady=15)

    # Contenedor de Imagen (Sin anchos fijos para que la imagen mande)
    label_imagen = tk.Label(ventana, text="[ Imagen del Producto ]", font=st.FONT_NORMAL, 
                            bg=st.BG_CARD, fg=st.TEXT_SECONDARY, relief="flat")
    label_imagen.pack(pady=10, fill=tk.BOTH, expand=True)
    
    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()