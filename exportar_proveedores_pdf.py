import os
import database
from fpdf import FPDF
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

class ReporteProveedores(FPDF):
    def header(self):
        # Título del reporte
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'REPORTE DE PROVEEDORES - HERRAJES SANTA FE', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 10, f'Generado el: {fecha}', 0, 1, 'R')
        self.ln(5)
        
        # Encabezados de la tabla
        self.set_fill_color(200, 200, 200)
        self.set_font('Arial', 'B', 11)
        self.cell(15, 10, 'ID', 1, 0, 'C', 1)
        self.cell(90, 10, 'NOMBRE / FABRICA', 1, 0, 'L', 1)
        self.cell(35, 10, 'ULT. MODIF.', 1, 0, 'C', 1)
        self.cell(25, 10, 'DESC. %', 1, 0, 'C', 1)
        self.cell(25, 10, 'INC. %', 1, 1, 'C', 1)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf():
    try:
        conexion = database.conectar()
        cursor = conexion.cursor()
        
        # Obtenemos los proveedores
        query = "SELECT id, nombre, fecha_modif_coeficiente, descuento_global, incremento_global FROM proveedores ORDER BY nombre ASC"
        cursor.execute(query)
        proveedores = cursor.fetchall()
        conexion.close()

        if not proveedores:
            print("No hay proveedores para exportar.")
            return

        pdf = ReporteProveedores()
        pdf.add_page()
        pdf.set_font('Arial', '', 10)

        for p in proveedores:
            p_id, nombre, fecha_mod, desc, inc = p
            
            fecha_txt = str(fecha_mod) if fecha_mod else "---"
            # Formatear fecha si viene en AAAA-MM-DD de la DB
            if fecha_mod and "-" in str(fecha_mod):
                try:
                    f_obj = datetime.strptime(str(fecha_mod), "%Y-%m-%d")
                    fecha_txt = f_obj.strftime("%d/%m/%Y")
                except: pass
            
            # Truncar nombre si es muy largo para que no rompa la tabla
            nombre_txt = (nombre[:42] + '..') if len(nombre) > 44 else nombre
            
            pdf.cell(15, 8, str(p_id), 1, 0, 'C')
            pdf.cell(90, 8, nombre_txt, 1, 0, 'L')
            pdf.cell(35, 8, fecha_txt, 1, 0, 'C')
            pdf.cell(25, 8, f"{desc*100:.2f}%", 1, 0, 'C')
            pdf.cell(25, 8, f"{inc*100:.2f}%", 1, 1, 'C')

        # Crear carpeta si no existe
        if not os.path.exists("reportes"):
            os.makedirs("reportes")

        ruta_archivo = os.path.abspath("reportes/lista_proveedores.pdf")
        pdf.output(ruta_archivo)
        
        # Abrir el archivo automáticamente
        os.startfile(ruta_archivo)
        print(f"✅ PDF generado con éxito en: {ruta_archivo}")

    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"No se pudo generar el PDF: {e}")

if __name__ == "__main__":
    generar_pdf()