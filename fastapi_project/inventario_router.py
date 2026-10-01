from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from database import get_session
from models import Proveedor, Insumo, InventarioBodega, Sucursal, Bodega, InventarioDoctor, Compra, DetalleCompra, Gasto, Receta, Tratamiento

router = APIRouter(prefix="/api/inventario", tags=["inventario"])

# --- SCHEMAS ---
class MovimientoRequest(BaseModel):
    tipo: str # "COMPRA", "DISTRIBUCION", "TRANSFERENCIA", "DEVOLUCION", "A_DOCTOR"
    insumo_id: int
    cantidad: int
    
    # Origen / Destino IDs (Contextual)
    proveedor_id: Optional[int] = None
    bodega_origen_id: Optional[int] = None
    bodega_origen_id: Optional[int] = None
    bodega_destino_id: Optional[int] = None
    bodega_destino_id: Optional[int] = None
    doctor_destino_id: Optional[int] = None
    
    costo_unitario: Optional[float] = None # Para compras
    motivo: Optional[str] = None

class DetalleCompraRequest(BaseModel):
    insumo_id: int
    cantidad: int
    precio_unitario: float

class CompraRequest(BaseModel):
    proveedor_id: int
    bodega_id: int
    usuario_id: int
    tipo_documento: str
    numero_documento: Optional[str] = None
    metodo_pago: str = "TRANSFERENCIA"
    observaciones: Optional[str] = None
    detalles: List[DetalleCompraRequest]

class RecetaRequest(BaseModel):
    insumo_id: int
    cantidad_requerida: int

# --- BODEGAS ---
@router.get("/bodegas", response_model=List[Bodega])
def list_bodegas(sucursal_id: Optional[int] = None, session: Session = Depends(get_session)):
    query = select(Bodega)
    if sucursal_id:
        query = query.where(Bodega.sucursal_id == sucursal_id)
    return session.exec(query).all()

@router.post("/bodegas", response_model=Bodega)
def create_bodega(bodega: Bodega, session: Session = Depends(get_session)):
    session.add(bodega)
    session.commit()
    session.refresh(bodega)
    return bodega

@router.get("/bodegas/{bodega_id}/stock")
def list_stock_bodega(bodega_id: int, session: Session = Depends(get_session)):
    inventario = session.exec(select(InventarioBodega).where(InventarioBodega.bodega_id == bodega_id)).all()
    res = []
    for inv in inventario:
        insumo = session.get(Insumo, inv.insumo_id)
        res.append({
            "id": inv.id,
            "insumo_id": inv.insumo_id,
            "nombre_insumo": insumo.nombre if insumo else "Desconocido",
            "unidad_medida": insumo.unidad_medida if insumo else "-",
            "stock_actual": inv.stock_actual,
            "stock_minimo": inv.stock_minimo
        })
    return res

# --- RECETAS (KITS DE TRATAMIENTO) ---
@router.get("/tratamientos/{tratamiento_id}/recetas")
def get_recetas(tratamiento_id: int, session: Session = Depends(get_session)):
    recetas = session.exec(select(Receta).where(Receta.tratamiento_id == tratamiento_id)).all()
    res = []
    for r in recetas:
        insumo = session.get(Insumo, r.insumo_id)
        if insumo:
            res.append({
                "id": r.id,
                "insumo_id": r.insumo_id,
                "nombre_insumo": insumo.nombre,
                "unidad_medida": insumo.unidad_medida,
                "cantidad_requerida": r.cantidad_requerida
            })
    return res

@router.post("/tratamientos/{tratamiento_id}/recetas")
def save_recetas(tratamiento_id: int, recetas_req: List[RecetaRequest], session: Session = Depends(get_session)):
    if not session.get(Tratamiento, tratamiento_id):
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
        
    old_recetas = session.exec(select(Receta).where(Receta.tratamiento_id == tratamiento_id)).all()
    for o in old_recetas:
        session.delete(o)
        
    for r in recetas_req:
        new_receta = Receta(
            tratamiento_id=tratamiento_id,
            insumo_id=r.insumo_id,
            cantidad_requerida=r.cantidad_requerida
        )
        session.add(new_receta)
        
    session.commit()
    return {"status": "ok", "message": "Recetas actualizadas correctamente"}

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

@router.post("/insumos", response_model=Insumo)
def create_insumo(insumo: Insumo, session: Session = Depends(get_session)):
    session.add(insumo)
    session.commit()
    session.refresh(insumo)
    return insumo

@router.put("/insumos/{id}", response_model=Insumo)
def update_insumo(id: int, data: Insumo, session: Session = Depends(get_session)):
    insumo = session.get(Insumo, id)
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    
    insumo_data = data.dict(exclude_unset=True)
    for key, value in insumo_data.items():
        setattr(insumo, key, value)
        
    session.add(insumo)
    session.commit()
    session.refresh(insumo)
    return insumo

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
        if req.bodega_destino_id:
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
        if not req.bodega_destino_id:
            raise HTTPException(status_code=400, detail="Falta sucursal destino")
            
        if insumo.stock_actual < req.cantidad:
            raise HTTPException(status_code=400, detail="Stock insuficiente en Bodega Central")
            
        # Restar de Bodega
        insumo.stock_actual -= req.cantidad
        session.add(insumo)
        
        # Sumar a Sucursal
        inventario = session.exec(select(InventarioBodega).where(
            InventarioBodega.bodega_id == req.bodega_destino_id,
            InventarioBodega.insumo_id == req.insumo_id
        )).first()
        
        if not inventario:
            inventario = InventarioBodega(
                bodega_id=req.bodega_destino_id,
                insumo_id=req.insumo_id,
                stock_actual=0
            )
            
        inventario.stock_actual += req.cantidad
        session.add(inventario)

    # 3. TRANSFERENCIA (Sucursal A -> Sucursal B)
    elif req.tipo == "TRANSFERENCIA":
        if not req.bodega_origen_id or not req.bodega_destino_id:
             raise HTTPException(status_code=400, detail="Se requiere origen y destino")
             
        # Origen
        inv_origen = session.exec(select(InventarioBodega).where(
            InventarioBodega.bodega_id == req.bodega_origen_id,
            InventarioBodega.insumo_id == req.insumo_id
        )).first()
        
        if not inv_origen or inv_origen.stock_actual < req.cantidad:
            raise HTTPException(status_code=400, detail="Stock insuficiente en Sucursal Origen")
            
        inv_origen.stock_actual -= req.cantidad
        session.add(inv_origen)
        
        # Destino
        inv_destino = session.exec(select(InventarioBodega).where(
            InventarioBodega.bodega_id == req.bodega_destino_id,
            InventarioBodega.insumo_id == req.insumo_id
        )).first()
        
        if not inv_destino:
            inv_destino = InventarioBodega(
                bodega_id=req.bodega_destino_id,
                insumo_id=req.insumo_id,
                stock_actual=0
            )
        inv_destino.stock_actual += req.cantidad
        session.add(inv_destino)

    # 4. DEVOLUCION (Sucursal -> Bodega)
    elif req.tipo == "DEVOLUCION":
        if not req.bodega_origen_id:
             raise HTTPException(status_code=400, detail="Falta sucursal origen")
             
        inv_origen = session.exec(select(InventarioBodega).where(
            InventarioBodega.bodega_id == req.bodega_origen_id,
            InventarioBodega.insumo_id == req.insumo_id
        )).first()
        
        if not inv_origen or inv_origen.stock_actual < req.cantidad:
             raise HTTPException(status_code=400, detail="Stock insuficiente para devolver")
             
        inv_origen.stock_actual -= req.cantidad
        session.add(inv_origen)
        
        insumo.stock_actual += req.cantidad
        session.add(insumo)

    # 5. A_DOCTOR (Sucursal -> Doctor)
    elif req.tipo == "A_DOCTOR":
        if not req.bodega_origen_id or not req.doctor_destino_id:
            raise HTTPException(status_code=400, detail="Falta sucursal origen o doctor destino")
            
        inv_sucursal = session.exec(select(InventarioBodega).where(
            InventarioBodega.bodega_id == req.bodega_origen_id,
            InventarioBodega.insumo_id == req.insumo_id
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

@router.get("/sucursal/{sucursal_id}", response_model=List[InventarioBodega])
def list_inventario_sucursal(sucursal_id: int, session: Session = Depends(get_session)):
    """List stock for a specific branch"""
    # Join with Insumo to ensure we get details (although response_model might restrict if not careful with lazy loading)
    # Ideally should return a custom DTO with Insumo name. 
    # For now, let's rely on SQLModel relationship loading if configured, or just return the link.
    # To be safe and useful for frontend, we should include Insumo data.
    return session.exec(select(InventarioBodega).where(InventarioBodega.bodega_id == sucursal_id)).all()

@router.get("/sucursales", response_model=List[Sucursal])
def list_sucursales(session: Session = Depends(get_session)):
    return session.exec(select(Sucursal)).all()

# --- COMPRAS E INVENTARIO DIRECTO ---

@router.post("/compras")
def registrar_compra(req: CompraRequest, session: Session = Depends(get_session)):
    proveedor = session.get(Proveedor, req.proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        
    bodega = session.get(Bodega, req.bodega_id)
    if not bodega:
        raise HTTPException(status_code=404, detail="Bodega no encontrada")
    
    sucursal_id = bodega.sucursal_id

    # 1. Calcular el total
    monto_total = sum(d.cantidad * d.precio_unitario for d in req.detalles)
    
    # 2. Crear el Gasto (Impacta el Dashboard Automáticamente)
    desc_doc = f"{req.tipo_documento} {req.numero_documento}" if req.numero_documento else req.tipo_documento
    gasto = Gasto(
        descripcion=f"COMPRA INVENTARIO - {desc_doc} - Proveedor: {proveedor.nombre} - Bodega: {bodega.nombre}",
        monto=monto_total,
        metodo_pago=req.metodo_pago,
        categoria="COMPRA DE INVENTARIO",
        tipo="EGRESO",
        sucursal_id=sucursal_id,
        usuario_id=req.usuario_id
    )
    session.add(gasto)
    session.commit()
    session.refresh(gasto)
    
    # 3. Registrar la Compra
    compra = Compra(
        proveedor_id=req.proveedor_id,
        bodega_id=req.bodega_id,
        usuario_id=req.usuario_id,
        tipo_documento=req.tipo_documento,
        numero_documento=req.numero_documento,
        gasto_id=gasto.id,
        monto_total=monto_total,
        observaciones=req.observaciones
    )
    session.add(compra)
    session.commit()
    session.refresh(compra)
    
    # 4. Procesar Detalles y Actualizar Bodega (InventarioBodega)
    for det in req.detalles:
        insumo = session.get(Insumo, det.insumo_id)
        if not insumo:
            continue
            
        detalle_db = DetalleCompra(
            compra_id=compra.id,
            insumo_id=det.insumo_id,
            cantidad=det.cantidad,
            precio_unitario=det.precio_unitario
        )
        session.add(detalle_db)
        
        # Aumentar stock en la sucursal (Bodega)
        inv_bodega = session.exec(select(InventarioBodega).where(
            InventarioBodega.bodega_id == req.bodega_id,
            InventarioBodega.insumo_id == det.insumo_id
        )).first()
        
        if not inv_bodega:
            inv_bodega = InventarioBodega(
                bodega_id=req.bodega_id,
                insumo_id=det.insumo_id,
                stock_actual=0
            )
            session.add(inv_bodega)
            
        inv_bodega.stock_actual += det.cantidad
        session.add(inv_bodega)
        
    session.commit()
    return {"status": "ok", "compra_id": compra.id, "gasto_id": gasto.id, "mensaje": "Compra e inventario registrados exitosamente"}
