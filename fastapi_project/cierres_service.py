from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlmodel import Session, select, func
from models import CierreMes, ConfiguracionCierre, Atencion, Pago, Gasto, User

MESES_NOMBRES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

def parse_fecha(fecha: Any) -> Optional[datetime]:
    if not fecha:
        return None
    if isinstance(fecha, datetime):
        return fecha
    if isinstance(fecha, date):
        return datetime.combine(fecha, datetime.min.time())
    if isinstance(fecha, str):
        fecha_clean = fecha.strip()
        # Try ISO format
        try:
            return datetime.fromisoformat(fecha_clean)
        except Exception:
            pass
        # Try standard formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
            try:
                return datetime.strptime(fecha_clean, fmt)
            except Exception:
                continue
    return None

def is_periodo_cerrado(session: Session, fecha: Optional[Any]) -> Tuple[bool, str]:
    """
    Verifica si la fecha dada corresponde a un periodo (mes/año) que se encuentra CERRADO.
    Retorna una tupla: (esta_cerrado: bool, mensaje_error: str)
    """
    dt = parse_fecha(fecha)
    if not dt:
        return False, ""

    anio = dt.year
    mes = dt.month
    nombre_mes = MESES_NOMBRES[mes] if 1 <= mes <= 12 else str(mes)

    # 1. Prioridad: Registro explícito en CierreMes
    cierre = session.exec(
        select(CierreMes).where(CierreMes.anio == anio, CierreMes.mes == mes)
    ).first()

    if cierre:
        if cierre.estado == "CERRADO":
            detalles_cierre = ""
            if cierre.fecha_cierre:
                detalles_cierre = f" (cerrado el {cierre.fecha_cierre.strftime('%d/%m/%Y')})"
            return True, f"El periodo de {nombre_mes} {anio} se encuentra CERRADO{detalles_cierre}. No se pueden registrar, modificar ni eliminar operaciones en este mes cerrado."
        elif cierre.estado == "ABIERTO":
            # Si el administrador abrió explícitamente el mes, se permite operar
            return False, ""

    # 2. Regla global de cierre automático por fecha de corte
    config = session.exec(select(ConfiguracionCierre)).first()
    if config and config.cierre_automatico_activo and config.fecha_corte_automatica:
        corte = config.fecha_corte_automatica
        # Si el mes es anterior o igual al mes de la fecha de corte
        if (anio < corte.year) or (anio == corte.year and mes <= corte.month):
            return True, (
                f"El periodo de {nombre_mes} {anio} está CERRADO automáticamente por fecha de corte "
                f"({corte.strftime('%d/%m/%Y')}). Debe reabrir el mes desde 'Cierres de Mes' con contraseña de administrador para realizar transacciones."
            )

    return False, ""

def check_periodo_abierto(session: Session, fecha: Optional[Any]):
    """
    Lanza HTTPException 400 si el periodo está cerrado.
    Usar en todos los endpoints transaccionales (creación, edición, eliminación).
    """
    cerrado, msg = is_periodo_cerrado(session, fecha)
    if cerrado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

def cerrar_periodo_manual(
    session: Session,
    anio: int,
    mes: int,
    user_id: int,
    notas: Optional[str] = None
) -> CierreMes:
    if not (1 <= mes <= 12):
        raise HTTPException(status_code=400, detail="Mes inválido (debe ser de 1 a 12)")

    cierre = session.exec(
        select(CierreMes).where(CierreMes.anio == anio, CierreMes.mes == mes)
    ).first()

    now = datetime.now()
    if not cierre:
        cierre = CierreMes(
            anio=anio,
            mes=mes,
            estado="CERRADO",
            fecha_cierre=now,
            usuario_cierre_id=user_id,
            notas=notas
        )
        session.add(cierre)
    else:
        cierre.estado = "CERRADO"
        cierre.fecha_cierre = now
        cierre.usuario_cierre_id = user_id
        if notas is not None:
            cierre.notas = notas
        session.add(cierre)

    session.commit()
    session.refresh(cierre)
    return cierre

def abrir_periodo_manual(
    session: Session,
    anio: int,
    mes: int,
    user_id: int,
    motivo: Optional[str] = None
) -> CierreMes:
    if not (1 <= mes <= 12):
        raise HTTPException(status_code=400, detail="Mes inválido (debe ser de 1 a 12)")

    cierre = session.exec(
        select(CierreMes).where(CierreMes.anio == anio, CierreMes.mes == mes)
    ).first()

    now = datetime.now()
    if not cierre:
        cierre = CierreMes(
            anio=anio,
            mes=mes,
            estado="ABIERTO",
            fecha_reapertura=now,
            usuario_reapertura_id=user_id,
            motivo_reapertura=motivo or "Reapertura autorizada por administrador"
        )
        session.add(cierre)
    else:
        cierre.estado = "ABIERTO"
        cierre.fecha_reapertura = now
        cierre.usuario_reapertura_id = user_id
        cierre.motivo_reapertura = motivo or "Reapertura autorizada por administrador"
        session.add(cierre)

    session.commit()
    session.refresh(cierre)
    return cierre

def aplicar_cierre_por_fecha(
    session: Session,
    fecha_corte: datetime,
    user_id: int,
    cerrar_todos_anteriores: bool = True,
    activar_bloqueo_permanente: bool = True
) -> Tuple[int, ConfiguracionCierre]:
    """
    Aplica cierre automático hasta una fecha determinada.
    Actualiza la configuración global y los registros de CierreMes de todos los meses anteriores.
    """
    now = datetime.now()

    # 1. Guardar/actualizar configuración global
    config = session.exec(select(ConfiguracionCierre)).first()
    if not config:
        config = ConfiguracionCierre(
            fecha_corte_automatica=fecha_corte,
            cierre_automatico_activo=activar_bloqueo_permanente,
            usuario_id=user_id,
            ultima_actualizacion=now
        )
        session.add(config)
    else:
        config.fecha_corte_automatica = fecha_corte
        config.cierre_automatico_activo = activar_bloqueo_permanente
        config.usuario_id = user_id
        config.ultima_actualizacion = now
        session.add(config)

    meses_afectados = 0
    if cerrar_todos_anteriores:
        corte_year = fecha_corte.year
        corte_month = fecha_corte.month

        # Identificar el año más antiguo con transacciones
        earliest_atencion = session.exec(select(func.min(Atencion.fecha))).one_or_none()
        earliest_gasto = session.exec(select(func.min(Gasto.fecha))).one_or_none()
        dates = [d for d in [earliest_atencion, earliest_gasto] if d is not None]
        start_year = min([d.year for d in dates]) if dates else (corte_year - 1)

        for y in range(start_year, corte_year + 1):
            max_m = corte_month if y == corte_year else 12
            for m in range(1, max_m + 1):
                rec = session.exec(
                    select(CierreMes).where(CierreMes.anio == y, CierreMes.mes == m)
                ).first()
                nota_corte = f"Cierre automático aplicado al corte {fecha_corte.strftime('%d/%m/%Y')}"
                if not rec:
                    rec = CierreMes(
                        anio=y,
                        mes=m,
                        estado="CERRADO",
                        fecha_cierre=now,
                        usuario_cierre_id=user_id,
                        notas=nota_corte
                    )
                    session.add(rec)
                    meses_afectados += 1
                else:
                    rec.estado = "CERRADO"
                    rec.fecha_cierre = now
                    rec.usuario_cierre_id = user_id
                    rec.notas = nota_corte
                    session.add(rec)
                    meses_afectados += 1

    session.commit()
    session.refresh(config)
    return meses_afectados, config

def obtener_resumen_periodos(
    session: Session,
    anio: Optional[int] = None
) -> Dict[str, Any]:
    """
    Retorna la configuración actual, los periodos del año con estado contable y estadísticas.
    """
    now = datetime.now()
    anio_target = anio if anio is not None else now.year

    # Obtener configuración
    config = session.exec(select(ConfiguracionCierre)).first()
    config_dict = {
        "fecha_corte_automatica": config.fecha_corte_automatica.isoformat() if config and config.fecha_corte_automatica else None,
        "cierre_automatico_activo": bool(config.cierre_automatico_activo) if config else False,
        "ultima_actualizacion": config.ultima_actualizacion.isoformat() if config and config.ultima_actualizacion else None,
    }

    # Años disponibles
    earliest_atencion = session.exec(select(func.min(Atencion.fecha))).one_or_none()
    earliest_gasto = session.exec(select(func.min(Gasto.fecha))).one_or_none()
    earliest_cierre = session.exec(select(func.min(CierreMes.anio))).one_or_none()
    valid_years = [now.year, anio_target]
    if earliest_atencion: valid_years.append(earliest_atencion.year)
    if earliest_gasto: valid_years.append(earliest_gasto.year)
    if earliest_cierre: valid_years.append(earliest_cierre)
    min_year = min(valid_years)
    anios_disponibles = sorted(list(range(min_year, max(valid_years) + 2)), reverse=True)

    # Cierres existentes para este año
    cierres_db = session.exec(
        select(CierreMes).where(CierreMes.anio == anio_target)
    ).all()
    cierres_map = {c.mes: c for c in cierres_db}

    # Usuarios para mapear nombres
    users_db = session.exec(select(User)).all()
    users_map = {u.id: u.username for u in users_db}

    periodos = []
    for m in range(1, 13):
        start_dt = datetime(anio_target, m, 1, 0, 0, 0)
        if m == 12:
            end_dt = datetime(anio_target + 1, 1, 1, 0, 0, 0)
        else:
            end_dt = datetime(anio_target, m + 1, 1, 0, 0, 0)

        cierre = cierres_map.get(m)
        estado = "ABIERTO"
        tipo_cierre = "NINGUNO"
        fecha_cierre_str = None
        usuario_cierre_nombre = None
        fecha_reapertura_str = None
        usuario_reapertura_nombre = None
        motivo_reapertura = None
        notas = None

        if cierre:
            estado = cierre.estado
            tipo_cierre = "MANUAL"
            if cierre.fecha_cierre:
                fecha_cierre_str = cierre.fecha_cierre.strftime("%d/%m/%Y %H:%M")
            if cierre.usuario_cierre_id:
                usuario_cierre_nombre = users_map.get(cierre.usuario_cierre_id, "Admin")
            if cierre.fecha_reapertura:
                fecha_reapertura_str = cierre.fecha_reapertura.strftime("%d/%m/%Y %H:%M")
            if cierre.usuario_reapertura_id:
                usuario_reapertura_nombre = users_map.get(cierre.usuario_reapertura_id, "Admin")
            motivo_reapertura = cierre.motivo_reapertura
            notas = cierre.notas
        else:
            # Evaluar cierre automático
            if config and config.cierre_automatico_activo and config.fecha_corte_automatica:
                corte = config.fecha_corte_automatica
                if (anio_target < corte.year) or (anio_target == corte.year and m <= corte.month):
                    estado = "CERRADO"
                    tipo_cierre = "AUTOMATICO"
                    notas = f"Corte automático al {corte.strftime('%d/%m/%Y')}"

        # Estadísticas del mes
        atenciones_cnt = session.exec(
            select(func.count(Atencion.id)).where(Atencion.fecha >= start_dt, Atencion.fecha < end_dt)
        ).one() or 0

        total_ingresos = session.exec(
            select(func.coalesce(func.sum(Pago.monto), 0)).where(Pago.fecha >= start_dt, Pago.fecha < end_dt)
        ).one() or Decimal("0.00")

        total_egresos = session.exec(
            select(func.coalesce(func.sum(Gasto.monto), 0)).where(
                Gasto.fecha >= start_dt,
                Gasto.fecha < end_dt,
                Gasto.tipo != "INGRESO",
                Gasto.categoria != "RETIRO SOCIOS"
            )
        ).one() or Decimal("0.00")

        periodos.append({
            "anio": anio_target,
            "mes": m,
            "nombre_mes": MESES_NOMBRES[m],
            "periodo_label": f"{MESES_NOMBRES[m]} {anio_target}",
            "estado": estado,
            "tipo_cierre": tipo_cierre,
            "fecha_cierre": fecha_cierre_str,
            "usuario_cierre": usuario_cierre_nombre,
            "fecha_reapertura": fecha_reapertura_str,
            "usuario_reapertura": usuario_reapertura_nombre,
            "motivo_reapertura": motivo_reapertura,
            "notas": notas,
            "es_mes_actual": (anio_target == now.year and m == now.month),
            "es_mes_futuro": (anio_target > now.year or (anio_target == now.year and m > now.month)),
            "stats": {
                "atenciones": int(atenciones_cnt),
                "ingresos": float(total_ingresos),
                "egresos": float(total_egresos),
                "balance": float(total_ingresos - total_egresos)
            }
        })

    return {
        "anio_seleccionado": anio_target,
        "anios_disponibles": anios_disponibles,
        "configuracion": config_dict,
        "periodos": periodos
    }
