import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import ttkbootstrap as tb
import os
from datetime import datetime
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
        try: 
            v_lista[3] = f"{float(v_lista[3]):.2f}"
        except: 
            pass
        tabla.insert("", "end", values=v_lista)
    conexion.close()

def generar_ticket_pdf(presupuesto_id):
    """Genera un PDF limpio en formato ticket 58mm sin bordes rígidos y con descripciones multilínea."""
    try:
        conexion = database.conectar()
        cursor = conexion.cursor()
        
        # 1. Recuperamos datos de la cabecera (Cambiado %s por ?)
        cursor.execute("SELECT cliente_nombre, fecha, total, cliente_tipo FROM presupuestos WHERE id = ?", (presupuesto_id,))
        datos_venta = cursor.fetchone()
        
        # 2. Recuperamos los productos (Cambiado %s por ?)
        cursor.execute('''
            SELECT p.descripcion, d.cantidad, d.precio_unitario_congelado 
            FROM presupuesto_detalles d
            JOIN productos p ON d.producto_id = p.id
            WHERE d.presupuesto_id = ?
        ''', (presupuesto_id,))
        items = cursor.fetchall()
        conexion.close()
        
        if not datos_venta: 
            return

        cliente, fecha, total, tipo_cliente = datos_venta
        
        # 3. Formato Ticket 58mm sin recuadros y con alto dinámico
        altura_ticket = 85 + (len(items) * 12)
        
        pdf = FPDF(orientation='P', unit='mm', format=(58, altura_ticket))
        pdf.set_margins(1.5, 2, 1.5)
        pdf.set_auto_page_break(auto=True, margin=2)
        pdf.add_page()
        
        # Encabezado
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 4, "HERRAJES SANTA FE", ln=True, align="C")
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 4, "Comprobante de Venta", ln=True, align="C")
        
        # Línea separadora limpia
        pdf.cell(0, 3, "- " * 22, ln=True, align="C")
        
        # Datos Cliente
        pdf.set_font("Arial", "B", 7)
        pdf.cell(14, 3.5, "Ticket N°:", 0, 0)
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 3.5, str(presupuesto_id), ln=True)
        
        pdf.set_font("Arial", "B", 7)
        pdf.cell(14, 3.5, "Fecha:", 0, 0)
        pdf.set_font("Arial", "", 7)
        pdf.cell(0, 3.5, str(fecha), ln=True)
        
        pdf.set_font("Arial", "B", 7)
        pdf.cell(14, 3.5, "Cliente:", 0, 0)
        pdf.set_font("Arial", "", 7)
        pdf.multi_cell(0, 3.5, str(cliente))
        
        # Línea separadora limpia
        pdf.cell(0, 3, "- " * 22, ln=True, align="C")
        
        # Cabecera Tabla
        pdf.set_font("Arial", "B", 7)
        pdf.cell(8, 4, "Cant", 0, 0, 'L')
        pdf.cell(32, 4, "Descripción", 0, 0, 'L')
        pdf.cell(15, 4, "Total", 0, 1, 'R')
        pdf.cell(0, 2, "- " * 22, ln=True, align="C")
        
        # Detalle de Productos
        pdf.set_font("Arial", "", 7)
        for desc, cant, precio in items:
            subtotal = cant * precio
            y_inicial = pdf.get_y()
            
            # Cantidad a la izquierda
            pdf.cell(8, 3.5, f"{cant:g}", 0, 0, 'L')
            
            # Descripción multilínea sin cortar el texto
            pdf.multi_cell(32, 3.5, str(desc), border=0, align='L')
            y_final_desc = pdf.get_y()
            
            # Subtotal a la derecha
            pdf.set_xy(41.5, y_inicial)
            pdf.cell(15, 3.5, f"${subtotal:.2f}", 0, 1, 'R')
            
            # Ajustar cursor para el siguiente producto si el texto ocupó varias líneas
            if y_final_desc > pdf.get_y():
                pdf.set_y(y_final_desc)
                
            pdf.ln(1)
            
        # Pie de página y Totales
        pdf.cell(0, 2, "- " * 22, ln=True, align="C")
        pdf.ln(1)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(25, 4, "TOTAL:", 0, 0, 'L')
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 4, f"$ {total:.2f}", 0, 1, 'R')

        if tipo_cliente and "Profesional" in tipo_cliente:
            pdf.ln(1)
            pdf.set_font("Arial", "I", 6)
            pdf.cell(0, 3, "* Descuento Gremio Aplicado *", ln=True, align="C")

        pdf.ln(3)
        pdf.set_font("Arial", "I", 7)
        pdf.cell(0, 4, "¡Gracias por su compra!", ln=True, align="C")
        
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
    
    item = tabla.item(seleccion)
    venta_id = item['values'][0]
    
    generar_ticket_pdf(venta_id)

def eliminar_venta():
    """Borra la venta seleccionada y sus productos asociados"""
    seleccion = tabla.selection()
    if not seleccion:
        messagebox.showwarning("Atención", "Por favor, seleccione una venta de la lista para eliminar.")
        return

    item = tabla.item(seleccion)
    venta_id = item['values'][0]
    cliente = item['values'][2]

    confirmar = messagebox.askyesno("Confirmar Eliminación", 
                                    f"¿Está seguro de que desea eliminar la Venta N° {venta_id} de '{cliente}'?\n\nEsta acción no se puede deshacer.")
    
    if confirmar:
        try:
            conexion = database.conectar()
            cursor = conexion.cursor()
            
            # Cambiado %s por ? para compatibilidad SQLite
            cursor.execute("DELETE FROM presupuesto_detalles WHERE presupuesto_id = ?", (venta_id,))
            cursor.execute("DELETE FROM presupuestos WHERE id = ?", (venta_id,))
            
            conexion.commit()
            conexion.close()
            
            messagebox.showinfo("Eliminado", f"La venta N° {venta_id} ha sido eliminada correctamente.")
            cargar_historial()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar la venta: {e}")

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

    btn_imprimir = tb.Button(frame_botones, text="🖨️ VER TICKET", command=reimprimir_seleccionado, bootstyle="success")
    btn_imprimir.pack(side=tk.LEFT, padx=10)

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