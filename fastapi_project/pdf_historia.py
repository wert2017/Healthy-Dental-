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
    edad = str(paciente.edad) if paciente.edad else "" 
    sexo = paciente.sexo[0].upper() if paciente.sexo else ""
    # No mostramos el celular por petición del usuario
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
        
        # y_from_top = 70 para la fila blanca debajo de las cabeceras
        y1 = 70
        draw_text(c1, 50, y1, apellido_paterno)
        draw_text(c1, 150, y1, apellido_materno)
        draw_text(c1, 250, y1, nombres)
        draw_text(c1, 360, y1, cedula)
        draw_text(c1, 435, y1, sexo)
        draw_text(c1, 460, y1, edad)
        
        # Reducir un punto el tamaño para el número de historia para que quepa bien
        c1.setFont("Helvetica", 7)
        draw_text(c1, 540, y1, historia_clinica)
        
        # Escribir los 4 últimos dígitos de la HC arriba a la derecha SOLO en la pagina 1
        if historia_clinica:
            hc_digits = historia_clinica.split('-')[-1]
            c1.setFont("Helvetica-Bold", 24)
            c1.drawString(520, page_height - 35, hc_digits)
            c1.setFont("Helvetica", 9)
            
        # Crear un parche blanco para tapar la palabra "LOGO", bajado (y=page_height-43) para tapar bien la palabra
        c1.setFillColorRGB(1, 1, 1)
        c1.rect(page_width/2 - 60, page_height - 43, 120, 40, stroke=0, fill=1)
        c1.setFillColorRGB(0, 0, 0)
        
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
                # Logo en pagina 1 (x=-20, y=page_height-45)
                c1.drawImage(logo_path, -20, page_height - 45, width=160, height=50, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
                
        c1.save()
        packet1.seek(0)
        overlay1 = PdfReader(packet1)
        page1_base.merge_page(overlay1.pages[0])

    # --- Header Overlay for PAGES 2, 3, 4 ---
    packet_header = BytesIO()
    c_header = canvas.Canvas(packet_header, pagesize=(page_width, page_height))
        
    if logo_path:
        try:
            # Logo bajado un poco en paginas 2, 3, 4 (y=page_height-65)
            c_header.drawImage(logo_path, -20, page_height - 65, width=160, height=50, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
            
    c_header.save()
    packet_header.seek(0)
    overlay_header = PdfReader(packet_header).pages[0]

    for i in range(len(reader.pages)):
        page = reader.pages[i]
        if i > 0:
            # Aplicar overlay solo a paginas 2, 3, 4
            page.merge_page(overlay_header)
        writer.add_page(page)
        
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output
