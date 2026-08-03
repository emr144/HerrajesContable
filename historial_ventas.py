import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import ttkbootstrap as tb
import os
from fpdf import FPDF
import styles as st
import database # Importamos para obtener la ruta

def cargar_historial():
    """Refresca la tabla con las ventas de la base de datos"""
    for row in tabla.get_children():
        tabla.delete(row)
    
    conexion = database.conectar()
    cursor = conexion.cursor()
    # Traemos ID, Fecha, Cliente y Total
    cursor.execute("SELECT id, fecha, cliente_nombre, total FROM presupuestos ORDER BY id DESC")
    for venta in cursor.fetchall():
        v_lista = list(venta)
        # Formatear el TOTAL a 2 decimales
        try: v_lista[3] = f"{float(v_lista[3]):.2f}"
        except: pass
        tabla.insert("", "end", values=v_lista)
    conexion.close()

def generar_ticket_pdf(presupuesto_id):
    """Genera un PDF con el detalle de la venta y lo abre automáticamente"""
    try:
        conexion = database.conectar()
        cursor = conexion.cursor()
        
        # 1. Recuperamos datos de la cabecera
        cursor.execute("SELECT cliente_nombre, fecha, total, cliente_tipo FROM presupuestos WHERE id = %s", (presupuesto_id,))
        datos_venta = cursor.fetchone()
        
        # 2. Recuperamos los productos
        cursor.execute('''
            SELECT p.descripcion, d.cantidad, d.precio_unitario_congelado 
            FROM presupuesto_detalles d
            JOIN productos p ON d.producto_id = p.id
            WHERE d.presupuesto_id = %s
        ''', (presupuesto_id,))
        items = cursor.fetchall()
        conexion.close()
        
        if not datos_venta: return

        cliente, fecha, total, tipo_cliente = datos_venta
        
        # 3. Construimos el PDF (Formato Ticket 58mm)
        altura_ticket = 80 + (len(items) * 10)
        
        pdf = FPDF(orientation='P', unit='mm', format=(58, altura_ticket))
        pdf.set_margins(2, 2, 2)
        pdf.add_page()
        
        # Encabezado
        pdf.set_draw_color(60, 60, 60)
        pdf.set_line_width(0.3)
        pdf.rect(1.5, 1.5, 55, altura_ticket - 3)

        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 5, "Herrajes Santa Fe", ln=True, align="C")
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 4, "Comprobante de Venta", ln=True, align="C")
        pdf.line(5, 14, 53, 14)
        pdf.ln(1)
        
        # Datos Cliente
        pdf.set_font("Arial", "B", 7)
        pdf.cell(20, 4, "Ticket N:", 0, 0)
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 4, str(presupuesto_id), ln=True)
        pdf.set_font("Arial", "B", 7)
        pdf.cell(20, 4, "Fecha:", 0, 0)
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 4, str(fecha), ln=True)
        pdf.set_font("Arial", "B", 7)
        pdf.cell(20, 4, "Cliente:", 0, 0)
        pdf.set_font("Arial", "", 7)
        pdf.multi_cell(0, 4, str(cliente))
        pdf.ln(1)
        pdf.line(5, 30, 53, 30)
        
        # Tabla
        pdf.set_fill_color(235, 235, 235)
        pdf.set_font("Arial", "B", 6)
        pdf.cell(22, 5, "Desc", 1, 0, 'C', 1)
        pdf.cell(6, 5, "Cant", 1, 0, 'C', 1)
        pdf.cell(12, 5, "Precio", 1, 0, 'C', 1)
        pdf.cell(14, 5, "Total", 1, 1, 'C', 1)
        pdf.line(5, 36, 53, 36)
        
        pdf.set_font("Arial", size=6)
        for desc, cant, precio in items:
            subtotal = cant * precio
            desc_fmt = (desc[:16] + '..') if len(desc) > 17 else desc
            
            pdf.cell(22, 5, desc_fmt, 1)
            pdf.cell(6, 5, f"{cant:g}", 1, 0, 'C')
            pdf.cell(12, 5, f"{precio:.2f}", 1, 0, 'R')
            pdf.cell(14, 5, f"{subtotal:.2f}", 1, 1, 'R')
            
        # Total
        pdf.ln(2)
        pdf.set_draw_color(120, 120, 120)
        pdf.line(5, pdf.get_y(), 53, pdf.get_y())
        pdf.ln(1)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(0, 5, "TOTAL:", 0, 1, 'R')
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 7, f"$ {total:.2f}", 0, 1, 'R')
        pdf.set_text_color(0, 0, 0)

        # Mensaje condicional (Nuevo sistema de precios)
        if tipo_cliente and "Profesional" in tipo_cliente:
            pdf.ln(2)
            pdf.set_font("Arial", "I", 6)
            pdf.cell(0, 4, "** Descuento Cliente Frecuente / Gremio **", ln=True, align="C")

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
            conexion = database.conectar()
            cursor = conexion.cursor()
            
            # 1. Borramos los detalles de la venta (productos)
            cursor.execute("DELETE FROM presupuesto_detalles WHERE presupuesto_id = %s", (venta_id,))
            
            # 2. Borramos la cabecera de la venta
            cursor.execute("DELETE FROM presupuestos WHERE id = %s", (venta_id,))
            
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

    btn_refrescar = tb.Button(frame_botones, text="🔄 Actualizar Lista", command=cargar_historial, bootstyle="info")
    btn_refrescar.pack(side=tk.LEFT, padx=10)

    # BOTÓN REIMPRIMIR
    btn_imprimir = tb.Button(frame_botones, text="🖨️ VER TICKET", command=reimprimir_seleccionado, bootstyle="success")
    btn_imprimir.pack(side=tk.LEFT, padx=10)

    # BOTÓN ELIMINAR
    btn_eliminar = tb.Button(frame_botones, text="🗑️ ELIMINAR VENTA", command=eliminar_venta, bootstyle="danger-outline")
    btn_eliminar.pack(side=tk.LEFT, padx=10)

    cargar_historial()
    
    return ventana

if __name__ == '__main__':
    root = tk.Tk()
    st.aplicar_estilo_ventana(root)
    app = montar_interfaz(root)
    app.pack(fill="both", expand=True)
    root.mainloop()