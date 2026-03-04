import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os
from fpdf import FPDF
import styles as st # Importamos los estilos

def cargar_historial():
    """Refresca la tabla con las ventas de la base de datos"""
    for row in tabla.get_children():
        tabla.delete(row)
    
    conexion = sqlite3.connect('herrajes.db')
    cursor = conexion.cursor()
    # Traemos ID, Fecha, Cliente y Total
    cursor.execute("SELECT id, fecha, cliente_nombre, total FROM presupuestos ORDER BY id DESC")
    for venta in cursor.fetchall():
        tabla.insert("", "end", values=venta)
    conexion.close()

def generar_ticket_pdf(presupuesto_id):
    """Genera un PDF con el detalle de la venta y lo abre automáticamente"""
    try:
        conexion = sqlite3.connect('herrajes.db')
        cursor = conexion.cursor()
        
        # 1. Recuperamos datos de la cabecera
        cursor.execute("SELECT cliente_nombre, fecha, total FROM presupuestos WHERE id = ?", (presupuesto_id,))
        datos_venta = cursor.fetchone()
        
        # 2. Recuperamos los productos
        cursor.execute('''
            SELECT p.descripcion, d.cantidad, d.precio_unitario_congelado 
            FROM presupuesto_detalles d
            JOIN productos p ON d.producto_id = p.id
            WHERE d.presupuesto_id = ?
        ''', (presupuesto_id,))
        items = cursor.fetchall()
        conexion.close()
        
        if not datos_venta: return

        cliente, fecha, total = datos_venta
        
        # 3. Construimos el PDF (Formato Ticket 80mm)
        altura_ticket = 80 + (len(items) * 10)
        
        pdf = FPDF(orientation='P', unit='mm', format=(80, altura_ticket))
        pdf.set_margins(3, 3, 3)
        pdf.add_page()
        
        # Encabezado
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 5, "Herrajes Santa Fe", ln=True, align="C")
        pdf.set_font("Arial", size=8)
        pdf.cell(0, 5, "Comprobante de Venta", ln=True, align="C")
        pdf.ln(2)
        
        # Datos Cliente
        pdf.set_font("Arial", "B", 8)
        pdf.cell(0, 4, f"Ticket N: {presupuesto_id}", ln=True)
        pdf.cell(0, 4, f"Fecha: {fecha}", ln=True)
        pdf.multi_cell(0, 4, f"Cliente: {cliente}")
        pdf.ln(2)
        
        # Tabla
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Arial", "B", 7)
        pdf.cell(32, 5, "Descripcion", 1, 0, 'C', 1)
        pdf.cell(8, 5, "Cant", 1, 0, 'C', 1)
        pdf.cell(15, 5, "Precio", 1, 0, 'C', 1)
        pdf.cell(17, 5, "Total", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", size=7)
        for desc, cant, precio in items:
            subtotal = cant * precio
            desc_fmt = (desc[:18] + '..') if len(desc) > 20 else desc
            
            pdf.cell(32, 5, desc_fmt, 1)
            pdf.cell(8, 5, str(cant), 1, 0, 'C')
            pdf.cell(15, 5, f"{precio:.2f}", 1, 0, 'R')
            pdf.cell(17, 5, f"{subtotal:.2f}", 1, 1, 'R')
            
        # Total
        pdf.ln(4)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(45, 6, "TOTAL:", 0, 0, 'R')
        pdf.cell(27, 6, f"$ {total:.2f}", 0, 1, 'R')

        # Pie
        pdf.ln(4)
        pdf.set_font("Arial", "I", 7)
        pdf.cell(0, 4, "Gracias por su compra", ln=True, align="C")
        
        # 4. Guardar y Abrir
        if not os.path.exists("comprobantes"):
            os.makedirs("comprobantes")
            
        ruta_pdf = os.path.abspath(f"comprobantes/ticket_{presupuesto_id}.pdf")
        pdf.output(ruta_pdf)
        os.startfile(ruta_pdf)
            
    except Exception as e:
        messagebox.showerror("Error PDF", f"No se pudo generar el PDF: {e}")

def reimprimir_seleccionado():
    seleccion = tabla.selection()
    if not seleccion:
        messagebox.showwarning("Atención", "Por favor, seleccione una venta de la lista para ver el ticket.")
        return
    
    # Obtenemos el ID de la venta desde la columna 0
    item = tabla.item(seleccion)
    venta_id = item['values'][0]
    
    generar_ticket_pdf(venta_id)

def eliminar_venta():
    """Borra la venta seleccionada y sus productos asociados"""
    seleccion = tabla.selection()
    if not seleccion:
        messagebox.showwarning("Atención", "Por favor, seleccione una venta de la lista para eliminar.")
        return

    # Obtenemos el ID de la venta desde la columna 0
    item = tabla.item(seleccion)
    venta_id = item['values'][0]
    cliente = item['values'][2]

    # Pedir confirmación para evitar accidentes
    confirmar = messagebox.askyesno("Confirmar Eliminación", 
                                    f"¿Está seguro de que desea eliminar la Venta N° {venta_id} de '{cliente}'?\n\nEsta acción no se puede deshacer.")
    
    if confirmar:
        try:
            conexion = sqlite3.connect('herrajes.db')
            cursor = conexion.cursor()
            
            # 1. Borramos los detalles de la venta (productos)
            cursor.execute("DELETE FROM presupuesto_detalles WHERE presupuesto_id = ?", (venta_id,))
            
            # 2. Borramos la cabecera de la venta
            cursor.execute("DELETE FROM presupuestos WHERE id = ?", (venta_id,))
            
            conexion.commit()
            conexion.close()
            
            messagebox.showinfo("Eliminado", f"La venta N° {venta_id} ha sido eliminada correctamente.")
            cargar_historial() # Recargamos la lista
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar la venta: {e}")

def ver_detalles(event=None):
    """Muestra qué productos tenía la venta seleccionada (Opcional)"""
    seleccion = tabla.selection()
    if not seleccion: return
    venta_id = tabla.item(seleccion)['values'][0]
    # Aquí podrías abrir una ventanita extra con los productos si quisieras
    pass

# --- INTERFAZ ---
def montar_interfaz(parent):
    global tabla
    
    ventana = tk.Frame(parent, bg=st.BG_MAIN)

    tk.Label(ventana, text="Historial de Presupuestos / Ventas", font=st.FONT_TITLE, 
             bg=st.BG_MAIN, fg=st.TEXT_PRIMARY).pack(pady=20)

    # Tabla de Historial
    style_tabla = ttk.Style()
    style_tabla.theme_use("clam")
    style_tabla.configure("Treeview", background=st.BG_CARD, foreground="white", fieldbackground=st.BG_CARD, borderwidth=0, rowheight=25)
    style_tabla.map("Treeview", background=[('selected', st.ACCENT)])
    style_tabla.configure("Treeview.Heading", background=st.BG_CARD, foreground=st.TEXT_SECONDARY, font=st.FONT_LABEL, padding=10)

    columnas = ("id", "fecha", "cliente", "total")
    tabla = ttk.Treeview(ventana, columns=columnas, show="headings", style="Treeview")
    tabla.heading("id", text="N° TICKET")
    tabla.heading("fecha", text="FECHA")
    tabla.heading("cliente", text="CLIENTE")
    tabla.heading("total", text="TOTAL ($)")

    tabla.column("id", width=100, anchor="center")
    tabla.column("fecha", width=180, anchor="center")
    tabla.column("cliente", width=300)
    tabla.column("total", width=150, anchor="e")
    tabla.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # Botonera
    frame_botones = tk.Frame(ventana, bg=st.BG_MAIN)
    frame_botones.pack(pady=15)

    btn_refrescar = tk.Button(frame_botones, text="🔄 Actualizar Lista", command=cargar_historial, **st.estilo_boton(st.ACCENT))
    st.configurar_hover(btn_refrescar, st.ACCENT, st.BG_CARD)
    btn_refrescar.pack(side=tk.LEFT, padx=10)

    # BOTÓN REIMPRIMIR
    btn_imprimir = tk.Button(frame_botones, text="🖨️ VER TICKET", command=reimprimir_seleccionado, **st.estilo_boton(st.ACCENT))
    st.configurar_hover(btn_imprimir, st.ACCENT, st.BG_CARD)
    btn_imprimir.pack(side=tk.LEFT, padx=10)

    # BOTÓN ELIMINAR
    btn_eliminar = tk.Button(frame_botones, text="🗑️ ELIMINAR VENTA", command=eliminar_venta, **st.estilo_boton(st.RED_ERROR))
    st.configurar_hover(btn_eliminar, st.RED_ERROR, st.BG_CARD)
    btn_eliminar.pack(side=tk.LEFT, padx=10)

    cargar_historial()
    
    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()