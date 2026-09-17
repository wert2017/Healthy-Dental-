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
    
    # --- PÁGINA 1 (Índice 0) ---
    if len(reader.pages) >= 1:
        page1_base = reader.pages[0]
        page_width = float(page1_base.mediabox.width)
        page_height = float(page1_base.mediabox.height)
        
        packet1 = BytesIO()
        c1 = canvas.Canvas(packet1, pagesize=(page_width, page_height))
        c1.setFont("Helvetica", 9)
        
        # y_from_top = 115 approx for the yellow row under LOGO
        y1 = 115
        draw_text(c1, 40, y1, apellido_paterno)
        draw_text(c1, 140, y1, apellido_materno)
        draw_text(c1, 250, y1, nombres)
        draw_text(c1, 380, y1, cedula)
        draw_text(c1, 440, y1, sexo)
        draw_text(c1, 465, y1, edad)
        draw_text(c1, 495, y1, celular)
        draw_text(c1, 545, y1, historia_clinica)
        
        # Insertar Logo en la Página 1
        logo_path = None
        if sucursal and sucursal.nombre:
            norm_name = sucursal.nombre.strip().lower().replace(' ', '_')
            logo_name = f"logo_{norm_name}.png"
            test_path = os.path.join(STATIC_DIR, logo_name)
            if os.path.exists(test_path):
                logo_path = test_path
                
        if not logo_path:
            # Fallback al logo general
            test_path = os.path.join(STATIC_DIR, "logo.png")
            if os.path.exists(test_path):
                logo_path = test_path
                
        if logo_path:
            try:
                # Centrado arriba
                c1.drawImage(logo_path, page_width/2 - 75, page_height - 60, width=150, height=50, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
                
        c1.save()
        packet1.seek(0)
        overlay1 = PdfReader(packet1)
        page1_base.merge_page(overlay1.pages[0])

    # --- PÁGINA 3 (Índice 2) ---
    if len(reader.pages) >= 3:
        page3_base = reader.pages[2]
        page_width = float(page3_base.mediabox.width)
        page_height = float(page3_base.mediabox.height)
        
        packet3 = BytesIO()
        c3 = canvas.Canvas(packet3, pagesize=(page_width, page_height))
        c3.setFont("Helvetica", 9)
        
        # Fila 1 (y=75)
        draw_text(c3, 40, 75, "Healthy Dental")
        draw_text(c3, 150, 75, sucursal.nombre if sucursal else "")
        draw_text(c3, 510, 75, historia_clinica)
        
        # Fila 2 (y=105)
        draw_text(c3, 30, 105, apellido_paterno)
        draw_text(c3, 110, 105, apellido_materno)
        draw_text(c3, 210, 105, nombres)
        draw_text(c3, 500, 105, datetime.now().strftime("%Y-%m-%d"))
        draw_text(c3, 550, 105, datetime.now().strftime("%H:%M"))
                
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
        c4.setFont("Helvetica", 9)
        
        # Header (y=80)
        draw_text(c4, 50, 80, "Healthy Dental")
        draw_text(c4, 200, 80, sucursal.nombre if sucursal else "")
        draw_text(c4, 550, 80, historia_clinica)
        
        # Data row (y=140)
        draw_text(c4, 40, 140, datetime.now().strftime("%Y-%m-%d"))
        draw_text(c4, 110, 140, f"Paciente: {nombres} {apellido_paterno} {apellido_materno}")
        
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
