from sqlmodel import Session, select
from database import engine
from models import Paciente, Sucursal

def patch_historias():
    with Session(engine) as session:
        pacientes = session.exec(select(Paciente)).all()
        count = 0
        
        print(f"Total de pacientes a procesar: {len(pacientes)}")
        for p in pacientes:
            # Check what branch the patient is assigned to
            suc_prefix = "GEN"
            if p.sucursal_id:
                suc = session.get(Sucursal, p.sucursal_id)
                if suc and len(suc.nombre) >= 3:
                    suc_prefix = suc.nombre[:3].upper()

            # Ensure the number respects the new format HC-XXX-ID
            # If the ID is 15, the string needs to be HC-XXX-0015
            expected_hc = f"HC-{suc_prefix}-{p.id:04d}"
            
            if p.historia_clinica != expected_hc:
                p.historia_clinica = expected_hc
                session.add(p)
                count += 1
                
        if count > 0:
            session.commit()
            print(f"Éxito: Se han corregido {count} historias clínicas al nuevo formato profesional.")
        else:
            print("Todos los pacientes ya tienen un formato correcto.")

if __name__ == "__main__":
    patch_historias()
