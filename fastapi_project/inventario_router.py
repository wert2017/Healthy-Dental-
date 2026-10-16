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
    descuento: Optional[float] = 0.0
    tiene_iva: Optional[bool] = True
    iva_porcentaje: Optional[float] = 15.0
    subtotal: Optional[float] = None
    monto_iva: Optional[float] = None
    total_linea: Optional[float] = None

class CompraRequest(BaseModel):
    proveedor_id: int
    bodega_id: int
    usuario_id: int
    tipo_documento: str
    numero_documento: Optional[str] = None
    numero_autorizacion: Optional[str] = None
    metodo_pago: str = "TRANSFERENCIA"
    observaciones: Optional[str] = None
    subtotal_15: Optional[float] = 0.0
    subtotal_0: Optional[float] = 0.0
    subtotal_sin_impuestos: Optional[float] = 0.0
    iva_porcentaje: Optional[float] = 15.0
    monto_iva: Optional[float] = 0.0
    descuento: Optional[float] = 0.0
    monto_total: Optional[float] = None
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
        if key != "id":
            if isinstance(value, str):
                value = value.strip()
            setattr(proveedor, key, value)
        
    session.add(proveedor)
    session.commit()
    session.refresh(proveedor)
    return proveedor

@router.delete("/proveedores/{id}")
def delete_proveedor(id: int, session: Session = Depends(get_session)):
    proveedor = session.get(Proveedor, id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        
    compras_count = len(session.exec(select(Compra).where(Compra.proveedor_id == id)).all())
    if compras_count > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar: el proveedor tiene compras registradas en el historial. Puedes desactivarlo cambiando su estado a Inactivo.")
        
    insumos_count = len(session.exec(select(Insumo).where(Insumo.proveedor_id == id)).all())
    if insumos_count > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar: el proveedor está vinculado a productos del catálogo.")
        
    session.delete(proveedor)
    session.commit()
    return {"status": "ok", "message": "Proveedor eliminado exitosamente"}

# --- INSUMOS (Global Views) ---
@router.get("/insumos", response_model=List[Insumo])
def list_global_insumos(session: Session = Depends(get_session)):
    return session.exec(select(Insumo).order_by(Insumo.id.desc())).all()

@router.get("/insumos/siguiente-codigo")
def get_siguiente_codigo(session: Session = Depends(get_session)):
    # Buscar el último ID para sugerir INS-XXX
    total = session.exec(select(Insumo)).all()
    siguiente_num = len(total) + 1
    codigo_sugerido = f"INS-{siguiente_num:03d}"
    return {"siguiente_codigo": codigo_sugerido}

@router.post("/insumos", response_model=Insumo)
def create_insumo(insumo: Insumo, session: Session = Depends(get_session)):
    # Si no tiene código, autogenerar uno
    if not insumo.codigo or not insumo.codigo.strip():
        total = session.exec(select(Insumo)).all()
        insumo.codigo = f"INS-{len(total) + 1:03d}"
    else:
        insumo.codigo = insumo.codigo.strip().upper()
        
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
        if key != "id":
            if key == "codigo" and value:
                value = str(value).strip().upper()
            setattr(insumo, key, value)
        
    session.add(insumo)
    session.commit()
    session.refresh(insumo)
    return insumo

@router.delete("/insumos/{id}")
def delete_insumo(id: int, session: Session = Depends(get_session)):
    insumo = session.get(Insumo, id)
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
        
    # Verificar si está en recetas o detalles de compra
    recetas_count = len(session.exec(select(Receta).where(Receta.insumo_id == id)).all())
    if recetas_count > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar: el producto está asignado en recetas de tratamientos.")
        
    detalles_count = len(session.exec(select(DetalleCompra).where(DetalleCompra.insumo_id == id)).all())
    if detalles_count > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar: el producto tiene compras registradas en el historial.")
        
    # Eliminar inventarios asociados si los hay
    inv_bodegas = session.exec(select(InventarioBodega).where(InventarioBodega.insumo_id == id)).all()
    for ib in inv_bodegas:
        session.delete(ib)
        
    inv_doctores = session.exec(select(InventarioDoctor).where(InventarioDoctor.insumo_id == id)).all()
    for idoc in inv_doctores:
        session.delete(idoc)

    session.delete(insumo)
    session.commit()
    return {"status": "ok", "message": "Insumo eliminado exitosamente"}


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

@router.get("/compras")
def list_compras(session: Session = Depends(get_session)):
    compras = session.exec(select(Compra).order_by(Compra.fecha.desc())).all()
    res = []
    for c in compras:
        prov = session.get(Proveedor, c.proveedor_id)
        bod = session.get(Bodega, c.bodega_id)
        detalles_count = len(session.exec(select(DetalleCompra).where(DetalleCompra.compra_id == c.id)).all())
        res.append({
            "id": c.id,
            "fecha": c.fecha.strftime("%Y-%m-%d %H:%M") if c.fecha else "-",
            "proveedor": prov.nombre if prov else "Desconocido",
            "proveedor_ruc": prov.ruc if prov else "",
            "bodega": bod.nombre if bod else "Bodega Central",
            "tipo_documento": c.tipo_documento,
            "numero_documento": c.numero_documento or "-",
            "numero_autorizacion": c.numero_autorizacion or "",
            "subtotal_15": float(c.subtotal_15 or 0),
            "subtotal_0": float(c.subtotal_0 or 0),
            "subtotal_sin_impuestos": float(c.subtotal_sin_impuestos or 0),
            "monto_iva": float(c.monto_iva or 0),
            "descuento": float(c.descuento or 0),
            "monto_total": float(c.monto_total or 0),
            "items_count": detalles_count
        })
    return res

@router.post("/compras")
def registrar_compra(req: CompraRequest, session: Session = Depends(get_session)):
    proveedor = session.get(Proveedor, req.proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        
    bodega = session.get(Bodega, req.bodega_id)
    if not bodega:
        raise HTTPException(status_code=404, detail="Bodega no encontrada")
    
    sucursal_id = bodega.sucursal_id

    # 1. Calcular subtotales, IVA y total de la compra
    calc_subtotal_15 = 0.0
    calc_subtotal_0 = 0.0
    calc_monto_iva = 0.0
    detalles_procesados = []

    for d in req.detalles:
        insumo = session.get(Insumo, d.insumo_id)
        if not insumo:
            continue
            
        cant = float(d.cantidad)
        pu = float(d.precio_unitario)
        desc = float(d.descuento or 0.0)
        subt = max(0.0, (cant * pu) - desc)
        
        tiene_iva = d.tiene_iva if d.tiene_iva is not None else insumo.tiene_iva
        iva_pct = float(d.iva_porcentaje if d.iva_porcentaje is not None else (insumo.iva_porcentaje or 15.0))
        
        if tiene_iva and iva_pct > 0:
            m_iva = round(subt * (iva_pct / 100.0), 2)
            calc_subtotal_15 += subt
            calc_monto_iva += m_iva
        else:
            m_iva = 0.0
            calc_subtotal_0 += subt
            
        tot_lin = subt + m_iva
        
        detalles_procesados.append({
            "insumo_id": d.insumo_id,
            "cantidad": d.cantidad,
            "precio_unitario": pu,
            "descuento": desc,
            "subtotal": subt,
            "tiene_iva": tiene_iva,
            "iva_porcentaje": iva_pct,
            "monto_iva": m_iva,
            "total_linea": tot_lin
        })

    # Respetar valores enviados desde el frontend si el usuario los ajustó por redondeos exactos de factura física
    final_subtotal_15 = float(req.subtotal_15) if req.subtotal_15 is not None and req.subtotal_15 > 0 else round(calc_subtotal_15, 2)
    final_subtotal_0 = float(req.subtotal_0) if req.subtotal_0 is not None and req.subtotal_0 > 0 else round(calc_subtotal_0, 2)
    final_subtotal_sin_imp = round(final_subtotal_15 + final_subtotal_0, 2)
    final_monto_iva = float(req.monto_iva) if req.monto_iva is not None and req.monto_iva > 0 else round(calc_monto_iva, 2)
    final_descuento = float(req.descuento or 0.0)
    
    if req.monto_total is not None and req.monto_total > 0:
        final_monto_total = float(req.monto_total)
    else:
        final_monto_total = round(final_subtotal_sin_imp + final_monto_iva, 2)
    
    # 2. Crear el Gasto (Impacta el Flujo de Caja y Dashboards automáticamente)
    desc_doc = f"{req.tipo_documento} {req.numero_documento}" if req.numero_documento else req.tipo_documento
    detalle_tributario = f"(Subt: ${final_subtotal_sin_imp:.2f}, IVA: ${final_monto_iva:.2f}, Total: ${final_monto_total:.2f})"
    
    gasto = Gasto(
        descripcion=f"COMPRA INVENTARIO - {desc_doc} - {proveedor.nombre} {detalle_tributario}",
        monto=final_monto_total,
        metodo_pago=req.metodo_pago,
        categoria="COMPRA DE INVENTARIO",
        tipo="EGRESO",
        sucursal_id=sucursal_id,
        usuario_id=req.usuario_id
    )
    session.add(gasto)
    session.commit()
    session.refresh(gasto)
    
    # 3. Registrar la Compra en base de datos
    compra = Compra(
        proveedor_id=req.proveedor_id,
        bodega_id=req.bodega_id,
        usuario_id=req.usuario_id,
        tipo_documento=req.tipo_documento,
        numero_documento=req.numero_documento,
        numero_autorizacion=req.numero_autorizacion,
        gasto_id=gasto.id,
        subtotal_15=final_subtotal_15,
        subtotal_0=final_subtotal_0,
        subtotal_sin_impuestos=final_subtotal_sin_imp,
        iva_porcentaje=req.iva_porcentaje or 15.0,
        monto_iva=final_monto_iva,
        descuento=final_descuento,
        monto_total=final_monto_total,
        observaciones=req.observaciones
    )
    session.add(compra)
    session.commit()
    session.refresh(compra)
    
    # 4. Procesar Detalles y Actualizar Stock en Bodega (InventarioBodega)
    for det in detalles_procesados:
        detalle_db = DetalleCompra(
            compra_id=compra.id,
            insumo_id=det["insumo_id"],
            cantidad=det["cantidad"],
            precio_unitario=det["precio_unitario"],
            descuento=det["descuento"],
            subtotal=det["subtotal"],
            tiene_iva=det["tiene_iva"],
            iva_porcentaje=det["iva_porcentaje"],
            monto_iva=det["monto_iva"],
            total_linea=det["total_linea"]
        )
        session.add(detalle_db)
        
        # Aumentar stock en la sucursal (Bodega)
        inv_bodega = session.exec(select(InventarioBodega).where(
            InventarioBodega.bodega_id == req.bodega_id,
            InventarioBodega.insumo_id == det["insumo_id"]
        )).first()
        
        if not inv_bodega:
            inv_bodega = InventarioBodega(
                bodega_id=req.bodega_id,
                insumo_id=det["insumo_id"],
                stock_actual=0
            )
            session.add(inv_bodega)
            
        inv_bodega.stock_actual += det["cantidad"]
        session.add(inv_bodega)
        
    session.commit()
    return {
        "status": "ok", 
        "compra_id": compra.id, 
        "gasto_id": gasto.id, 
        "monto_total": final_monto_total,
        "subtotal_sin_impuestos": final_subtotal_sin_imp,
        "monto_iva": final_monto_iva,
        "mensaje": "Compra e inventario registrados exitosamente con desglose de IVA"
    }
