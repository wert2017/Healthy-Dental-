from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from database import get_session # Assuming this exists or I need to check main.py imports
from models import Proveedor, Insumo, InventarioSucursal, Sucursal, InventarioDoctor

router = APIRouter(prefix="/api/inventario", tags=["inventario"])

# --- SCHEMAS ---
class MovimientoRequest(BaseModel):
    tipo: str # "COMPRA", "DISTRIBUCION", "TRANSFERENCIA", "DEVOLUCION", "A_DOCTOR"
    insumo_id: int
    cantidad: int
    
    # Origen / Destino IDs (Contextual)
    proveedor_id: Optional[int] = None
    sucursal_origen_id: Optional[int] = None
    sucursal_destino_id: Optional[int] = None
    doctor_destino_id: Optional[int] = None
    
    costo_unitario: Optional[float] = None # Para compras
    motivo: Optional[str] = None

# --- PROVEEDORES CRUD ---

@router.get("/proveedores", response_model=List[Proveedor])
def list_proveedores(session: Session = Depends(get_session)):
    return session.exec(select(Proveedor)).all()

@router.post("/proveedores", response_model=Proveedor)
def create_proveedor(proveedor: Proveedor, session: Session = Depends(get_session)):
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    return proveedor

@router.put("/proveedores/{id}", response_model=Proveedor)
def update_proveedor(id: int, data: Proveedor, session: Session = Depends(get_session)):
    proveedor = session.get(Proveedor, id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    proveedor_data = data.dict(exclude_unset=True)
    for key, value in proveedor_data.items():
        setattr(proveedor, key, value)
        
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    return proveedor

# --- INSUMOS (Global Views) ---
@router.get("/insumos", response_model=List[Insumo])
def list_global_insumos(session: Session = Depends(get_session)):
    return session.exec(select(Insumo)).all()

# --- MOVIMIENTOS ---

@router.post("/movimiento")
def registro_movimiento(req: MovimientoRequest, session: Session = Depends(get_session)):
    """
    Central Logic for Inventory Movements
    1. COMPRA: Proveedor -> Bodega Central (o Sucursal directo)
    2. DISTRIBUCION: Bodega Central -> Sucursal
    3. TRANSFERENCIA: Sucursal A -> Sucursal B
    4. DEVOLUCION: Sucursal -> Bodega Central
    """
    insumo = session.get(Insumo, req.insumo_id)
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    # 1. COMPRA
    if req.tipo == "COMPRA":
        if req.sucursal_destino_id:
            # Compra directo a Sucursal not supported in V1 or treat as Distribucion logic?
            # Let's simple: Compra increases Bodega Central first usually, or direct.
            # If direct:
            pass # TODO: Implement direct purchase
        else:
            # Compra normal a Bodega Central
            insumo.stock_actual += req.cantidad
            session.add(insumo)
            
    # 2. DISTRIBUCION (Bodega -> Sucursal)
    elif req.tipo == "DISTRIBUCION":
        if not req.sucursal_destino_id:
            raise HTTPException(status_code=400, detail="Falta sucursal destino")
            
        if insumo.stock_actual < req.cantidad:
            raise HTTPException(status_code=400, detail="Stock insuficiente en Bodega Central")
            
        # Restar de Bodega
        insumo.stock_actual -= req.cantidad
        session.add(insumo)
        
        # Sumar a Sucursal
        inventario = session.exec(select(InventarioSucursal).where(
            InventarioSucursal.sucursal_id == req.sucursal_destino_id,
            InventarioSucursal.insumo_id == req.insumo_id
        )).first()
        
        if not inventario:
            inventario = InventarioSucursal(
                sucursal_id=req.sucursal_destino_id,
                insumo_id=req.insumo_id,
                stock_actual=0
            )
            
        inventario.stock_actual += req.cantidad
        session.add(inventario)

    # 3. TRANSFERENCIA (Sucursal A -> Sucursal B)
    elif req.tipo == "TRANSFERENCIA":
        if not req.sucursal_origen_id or not req.sucursal_destino_id:
             raise HTTPException(status_code=400, detail="Se requiere origen y destino")
             
        # Origen
        inv_origen = session.exec(select(InventarioSucursal).where(
            InventarioSucursal.sucursal_id == req.sucursal_origen_id,
            InventarioSucursal.insumo_id == req.insumo_id
        )).first()
        
        if not inv_origen or inv_origen.stock_actual < req.cantidad:
            raise HTTPException(status_code=400, detail="Stock insuficiente en Sucursal Origen")
            
        inv_origen.stock_actual -= req.cantidad
        session.add(inv_origen)
        
        # Destino
        inv_destino = session.exec(select(InventarioSucursal).where(
            InventarioSucursal.sucursal_id == req.sucursal_destino_id,
            InventarioSucursal.insumo_id == req.insumo_id
        )).first()
        
        if not inv_destino:
            inv_destino = InventarioSucursal(
                sucursal_id=req.sucursal_destino_id,
                insumo_id=req.insumo_id,
                stock_actual=0
            )
        inv_destino.stock_actual += req.cantidad
        session.add(inv_destino)

    # 4. DEVOLUCION (Sucursal -> Bodega)
    elif req.tipo == "DEVOLUCION":
        if not req.sucursal_origen_id:
             raise HTTPException(status_code=400, detail="Falta sucursal origen")
             
        inv_origen = session.exec(select(InventarioSucursal).where(
            InventarioSucursal.sucursal_id == req.sucursal_origen_id,
            InventarioSucursal.insumo_id == req.insumo_id
        )).first()
        
        if not inv_origen or inv_origen.stock_actual < req.cantidad:
             raise HTTPException(status_code=400, detail="Stock insuficiente para devolver")
             
        inv_origen.stock_actual -= req.cantidad
        session.add(inv_origen)
        
        insumo.stock_actual += req.cantidad
        session.add(insumo)

    # 5. A_DOCTOR (Sucursal -> Doctor)
    elif req.tipo == "A_DOCTOR":
        if not req.sucursal_origen_id or not req.doctor_destino_id:
            raise HTTPException(status_code=400, detail="Falta sucursal origen o doctor destino")
            
        inv_sucursal = session.exec(select(InventarioSucursal).where(
            InventarioSucursal.sucursal_id == req.sucursal_origen_id,
            InventarioSucursal.insumo_id == req.insumo_id
        )).first()
        
        if not inv_sucursal or inv_sucursal.stock_actual < req.cantidad:
            raise HTTPException(status_code=400, detail="Stock insuficiente en Sucursal para asignar al doctor")
            
        inv_sucursal.stock_actual -= req.cantidad
        session.add(inv_sucursal)
        
        inv_doctor = session.exec(select(InventarioDoctor).where(
            InventarioDoctor.doctor_id == req.doctor_destino_id,
            InventarioDoctor.insumo_id == req.insumo_id
        )).first()
        
        if not inv_doctor:
            inv_doctor = InventarioDoctor(
                doctor_id=req.doctor_destino_id,
                insumo_id=req.insumo_id,
                stock_actual=0
            )
        
        inv_doctor.stock_actual += req.cantidad
        session.add(inv_doctor)

    session.commit()
    return {"status": "ok", "nuevo_stock_central": insumo.stock_actual}

@router.get("/doctor/{doctor_id}", response_model=List[InventarioDoctor])
def list_inventario_doctor(doctor_id: int, session: Session = Depends(get_session)):
    """List personal stock for a specific doctor"""
    return session.exec(select(InventarioDoctor).where(InventarioDoctor.doctor_id == doctor_id)).all()

@router.get("/sucursal/{sucursal_id}", response_model=List[InventarioSucursal])
def list_inventario_sucursal(sucursal_id: int, session: Session = Depends(get_session)):
    """List stock for a specific branch"""
    # Join with Insumo to ensure we get details (although response_model might restrict if not careful with lazy loading)
    # Ideally should return a custom DTO with Insumo name. 
    # For now, let's rely on SQLModel relationship loading if configured, or just return the link.
    # To be safe and useful for frontend, we should include Insumo data.
    return session.exec(select(InventarioSucursal).where(InventarioSucursal.sucursal_id == sucursal_id)).all()

@router.get("/sucursales", response_model=List[Sucursal])
def list_sucursales(session: Session = Depends(get_session)):
    return session.exec(select(Sucursal)).all()
