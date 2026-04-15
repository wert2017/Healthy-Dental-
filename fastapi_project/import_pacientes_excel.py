import pandas as pd
from sqlmodel import Session, select
from database import engine
from models import Paciente
import math

def clean_str(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    return s if s else None

def import_data():
    file_path = r'c:\HD\HISTORIA HD SUR.xlsx'
    df = pd.read_excel(file_path)
    df.columns = df.columns.astype(str).str.strip()
    
    with Session(engine) as session:
        # Get count of existing patients to start HC indexing
        existing_count = session.exec(select(Paciente)).all()
        hc_counter = len(existing_count) + 1
        prov_counter = 1
        
        # Track inserted to avoid duplicated provisional
        inserted = 0
        skipped = 0
        
        for index, row in df.iterrows():
            apellidos = clean_str(row.get('APELLIDOS'))
            nombres = clean_str(row.get('NOMBRE'))
            
            # If both names are empty, skip row
            if not apellidos and not nombres:
                skipped += 1
                continue
                
            apellidos = apellidos or "Desconocido"
            nombres = nombres or ""
            
            sexo = clean_str(row.get('SEXO'))
            
            edad_val = row.get('EDAD')
            edad = None
            if not pd.isna(edad_val):
                try:
                    edad = int(float(edad_val))
                except:
                    pass
                    
            telefono = clean_str(row.get('TELEFONO'))
            if not telefono:
                telefono = "0999999999"
                
            cedula = clean_str(row.get('CEDULA'))
            if not cedula or len(cedula) < 4:
                cedula = f"PROV-{prov_counter:05d}"
                prov_counter += 1
                
            # ensure cedula uniqueness
            existing = session.exec(select(Paciente).where(Paciente.numero_identificacion == cedula)).first()
            if existing:
                skipped += 1
                continue
                
            ciudad = clean_str(row.get('CIUDAD'))
            
            historia_clinica = f"HC-{hc_counter:05d}"
            hc_counter += 1
            
            nuevo_paciente = Paciente(
                tipo_identificacion="CED" if not cedula.startswith("PROV") else "PROV",
                numero_identificacion=cedula,
                nombres=nombres,
                apellidos=apellidos,
                historia_clinica=historia_clinica,
                telefono=telefono,
                email=None,
                sexo=sexo,
                edad=edad,
                ciudad=ciudad,
                activo=True
            )
            
            session.add(nuevo_paciente)
            inserted += 1
            
        try:
            session.commit()
            print(f"Successfully inserted {inserted} patients. Skipped {skipped}.")
        except Exception as e:
            session.rollback()
            print(f"Error during bulk insert: {e}")

if __name__ == "__main__":
    import_data()
