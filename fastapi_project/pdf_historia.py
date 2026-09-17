import fitz  # PyMuPDF
import os
from io import BytesIO
from datetime import datetime

# Definir la ruta de la plantilla base y logos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
PLANTILLA_PDF_PATH = os.path.join(STATIC_DIR, "historia_base.pdf")

def generar_historia_clinica_pdf(paciente, sucursal=None):
    """
    Genera un PDF de la historia clínica basado en una matriz.
    Si la plantilla no existe, se lanzará una excepción.
    """
    if not os.path.exists(PLANTILLA_PDF_PATH):
        raise FileNotFoundError(f"No se encontró la plantilla en {PLANTILLA_PDF_PATH}. Debes exportar tu Excel como 'historia_base.pdf' y guardarlo en la carpeta static.")

    # Abrir la plantilla
    doc = fitz.open(PLANTILLA_PDF_PATH)
    
    # Extraer datos del paciente
    # Dividir nombres y apellidos (básico, asumiendo un espacio)
    apellidos = paciente.apellidos.split() if paciente.apellidos else ["", ""]
    apellido_paterno = apellidos[0] if len(apellidos) > 0 else ""
    apellido_materno = apellidos[1] if len(apellidos) > 1 else ("" if len(apellidos)>0 else "")
    
    nombres = paciente.nombres or ""
    cedula = paciente.numero_identificacion or ""
    
    # Calcular edad de forma sencilla si tuviéramos fecha de nacimiento, 
    # pero como el modelo Paciente no tiene fecha_nacimiento, podemos dejarlo en blanco 
    # o sacar la edad de otra parte si la tuvieras.
    edad = "" 
    sexo = ""
    celular = paciente.telefono or ""
    historia_clinica = paciente.historia_clinica or ""
    
    # --- PÁGINA 3 (Índice 2 en PyMuPDF) ---
    # COORDENADAS TEMPORALES (x, y) - ¡SE DEBERÁN AJUSTAR CON EL PDF REAL!
    if len(doc) >= 3:
        page3 = doc[2] 
        
        # Insertar texto (ajustar las coordenadas x, y según el PDF)
        # Ejemplo: page3.insert_text((x, y), texto, fontsize=10, fontname="helv", color=(0,0,0))
        page3.insert_text((50, 80), apellido_paterno, fontsize=10)
        page3.insert_text((150, 80), apellido_materno, fontsize=10)
        page3.insert_text((250, 80), nombres, fontsize=10)
        page3.insert_text((350, 80), cedula, fontsize=10)
        page3.insert_text((420, 80), sexo, fontsize=10)
        page3.insert_text((460, 80), edad, fontsize=10)
        page3.insert_text((500, 80), celular, fontsize=10)
        page3.insert_text((550, 80), historia_clinica, fontsize=10)
        
        # Insertar Logo
        if sucursal and sucursal.nombre:
            # Aquí asumimos que los logos se llaman logo_{nombre_sucursal_limpio}.png
            logo_name = f"logo_{sucursal.nombre.lower().replace(' ', '_')}.png"
            logo_path = os.path.join(STATIC_DIR, logo_name)
            if os.path.exists(logo_path):
                # Coordenadas del rectángulo donde irá el logo (x0, y0, x1, y1)
                rect = fitz.Rect(50, 20, 150, 60)
                page3.insert_image(rect, filename=logo_path)

    # --- PÁGINA 4 (Índice 3 en PyMuPDF) ---
    if len(doc) >= 4:
        page4 = doc[3]
        
        # Ejemplo de coordenadas para la página 4
        page4.insert_text((50, 80), "Healthy Dental", fontsize=10)
        page4.insert_text((200, 80), sucursal.nombre if sucursal else "", fontsize=10)
        page4.insert_text((550, 80), historia_clinica, fontsize=10)
        
        # Segunda fila
        page4.insert_text((50, 120), apellido_paterno, fontsize=10)
        page4.insert_text((150, 120), apellido_materno, fontsize=10)
        page4.insert_text((250, 120), nombres, fontsize=10)
        page4.insert_text((450, 120), datetime.now().strftime("%Y-%m-%d"), fontsize=10)
        page4.insert_text((520, 120), datetime.now().strftime("%H:%M"), fontsize=10)

    # Guardar en memoria
    pdf_bytes = doc.write()
    doc.close()
    
    return BytesIO(pdf_bytes)
