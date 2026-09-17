import os
from io import BytesIO
from datetime import datetime
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Definir la ruta de la plantilla base y logos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
PLANTILLA_PDF_PATH = os.path.join(STATIC_DIR, "historia_base.pdf")

def generar_historia_clinica_pdf(paciente, sucursal=None):
    """
    Genera un PDF de la historia clínica basado en una matriz.
    """
    if not os.path.exists(PLANTILLA_PDF_PATH):
        raise FileNotFoundError(f"No se encontró la plantilla en {PLANTILLA_PDF_PATH}. Debes exportar tu Excel como 'historia_base.pdf' y guardarlo en la carpeta static.")

    # Extraer datos del paciente
    apellidos = paciente.apellidos.split() if paciente.apellidos else ["", ""]
    apellido_paterno = apellidos[0] if len(apellidos) > 0 else ""
    apellido_materno = apellidos[1] if len(apellidos) > 1 else ""
    
    nombres = paciente.nombres or ""
    cedula = paciente.numero_identificacion or ""
    edad = "" 
    sexo = ""
    celular = paciente.telefono or ""
    historia_clinica = paciente.historia_clinica or ""
    
    # Abrir la plantilla
    reader = PdfReader(PLANTILLA_PDF_PATH)
    writer = PdfWriter()
    
    # Helpers
    def draw_text(c, x, y_from_top, text):
        # ReportLab origin is bottom-left, our coordinates are top-left
        c.drawString(x, page_height - y_from_top, str(text))
    
    # --- PÁGINA 3 (Índice 2) ---
    if len(reader.pages) >= 3:
        page3_base = reader.pages[2]
        page_width = float(page3_base.mediabox.width)
        page_height = float(page3_base.mediabox.height)
        
        packet3 = BytesIO()
        c3 = canvas.Canvas(packet3, pagesize=(page_width, page_height))
        c3.setFont("Helvetica", 10)
        
        # Coordenadas temporales a ajustar
        draw_text(c3, 50, 80, apellido_paterno)
        draw_text(c3, 150, 80, apellido_materno)
        draw_text(c3, 250, 80, nombres)
        draw_text(c3, 350, 80, cedula)
        draw_text(c3, 420, 80, sexo)
        draw_text(c3, 460, 80, edad)
        draw_text(c3, 500, 80, celular)
        draw_text(c3, 550, 80, historia_clinica)
        
        # Insertar Logo
        if sucursal and sucursal.nombre:
            logo_name = f"logo_{sucursal.nombre.lower().replace(' ', '_')}.png"
            logo_path = os.path.join(STATIC_DIR, logo_name)
            if os.path.exists(logo_path):
                # Reportlab drawImage: x, y is bottom-left corner
                # width 100, height 40. Top left is (50, 20) -> bottom_y = height - 60
                c3.drawImage(logo_path, 50, page_height - 60, width=100, height=40, preserveAspectRatio=True, mask='auto')
                
        c3.save()
        packet3.seek(0)
        overlay3 = PdfReader(packet3)
        page3_base.merge_page(overlay3.pages[0])

    # --- PÁGINA 4 (Índice 3) ---
    if len(reader.pages) >= 4:
        page4_base = reader.pages[3]
        page_width = float(page4_base.mediabox.width)
        page_height = float(page4_base.mediabox.height)
        
        packet4 = BytesIO()
        c4 = canvas.Canvas(packet4, pagesize=(page_width, page_height))
        c4.setFont("Helvetica", 10)
        
        draw_text(c4, 50, 80, "Healthy Dental")
        draw_text(c4, 200, 80, sucursal.nombre if sucursal else "")
        draw_text(c4, 550, 80, historia_clinica)
        draw_text(c4, 50, 120, apellido_paterno)
        draw_text(c4, 150, 120, apellido_materno)
        draw_text(c4, 250, 120, nombres)
        draw_text(c4, 450, 120, datetime.now().strftime("%Y-%m-%d"))
        draw_text(c4, 520, 120, datetime.now().strftime("%H:%M"))
        
        c4.save()
        packet4.seek(0)
        overlay4 = PdfReader(packet4)
        page4_base.merge_page(overlay4.pages[0])
        
    for i in range(len(reader.pages)):
        writer.add_page(reader.pages[i])
        
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output
