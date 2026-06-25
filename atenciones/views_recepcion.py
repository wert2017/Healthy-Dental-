from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Atencion, AtencionDetalle, Tratamiento
from tratamientos.models import Tratamiento
from pagos_clinica.models import Pago
from atenciones.models import AtencionDetalle, Atencion
from pacientes.models import Paciente
from doctores.models import Doctor
from django.http import JsonResponse
import json
from datetime import datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

@login_required
def recepcion_view(request):
    # 1. BÚSQUEDA DE PACIENTE
    query = request.GET.get('q')
    paciente_seleccionado = None
    saldo_paciente = 0
    saldo_paciente_abs = 0
    estado_saldo = "aldia"

    if paciente_id := request.GET.get('paciente_id'):
        paciente_seleccionado = get_object_or_404(Paciente, id=paciente_id)
    elif query:
        # Buscar por ID, Cédula o Nombre
        pacientes = Paciente.objects.filter(
            numero_identificacion__icontains=query
        ) | Paciente.objects.filter(
            nombres__icontains=query
        ) | Paciente.objects.filter(
            apellidos__icontains=query
        ) | Paciente.objects.filter(
             historia_clinica__icontains=query
        )

        if pacientes_encontrados := pacientes.first(): # Simplificación: tomamos el primero si hay coincidencias
             paciente_seleccionado = pacientes_encontrados
             
        # Correction:
        if pacientes.exists():
            paciente_seleccionado = pacientes.first()

    # Calcular Saldo del Paciente (Simulado o Real según modelos)
    # Aquí asumimos una propiedad en el modelo o un cálculo simple
    if paciente_seleccionado:
        # Lógica de ejemplo para saldo
        atenciones = Atencion.objects.filter(paciente=paciente_seleccionado)
        total_deuda = 0
        # Sumar saldos pendientes... (Implementar lógica real si existe)
        pass 

    # 2. CREAR NUEVA ATENCIÓN
    if request.method == 'POST':
        if paciente_seleccionado:
            nueva_atencion = Atencion.objects.create(
                paciente=paciente_seleccionado,
                estado='EN_PROCESO',
                fecha=timezone.now()
            )
            return redirect('editar_atencion', atencion_id=nueva_atencion.id)

    # 3. LISTAR ATENCIONES DE HOY
    hoy = timezone.localdate()
    
    # Robust date range filtering
    start_of_day = timezone.make_aware(datetime.combine(hoy, datetime.min.time()))
    end_of_day = timezone.make_aware(datetime.combine(hoy, datetime.max.time()))

    print(f"DEBUG RECEPCION: Hoy: {hoy}")
    print(f"DEBUG RECEPCION: Start: {start_of_day} | End: {end_of_day}")
    
    atenciones_hoy = Atencion.objects.filter(
        fecha__range=(start_of_day, end_of_day)
    ).order_by('-id').prefetch_related(
        'detalles', 'detalles__tratamiento', 'pagos'
    ).select_related('paciente', 'doctor')
    
    print(f"DEBUG RECEPCION: Found {atenciones_hoy.count()} atenciones")

    # CALCULAR TOTALES (Footer)
    def sum_or_0(val):
        return val or Decimal("0.00")

    total_valor = sum_or_0(AtencionDetalle.objects.filter(atencion__in=atenciones_hoy).aggregate(t=Sum('total_calculado'))['t'])
    
    # Pagos por tipo
    pagos_qs = Pago.objects.filter(atencion__in=atenciones_hoy)
    total_efectivo = sum_or_0(pagos_qs.filter(forma_pago='EF').aggregate(t=Sum('monto'))['t'])
    total_transferencia = sum_or_0(pagos_qs.filter(forma_pago='TR').aggregate(t=Sum('monto'))['t'])
    total_tarjeta = sum_or_0(pagos_qs.filter(forma_pago='TC') .aggregate(t=Sum('monto'))['t']) # TC solo? o TC+TD?
    # Revisando modelo Atencion, monto_tarjeta suma TC y TD. Hagamos lo mismo.
    total_tarjeta = sum_or_0(pagos_qs.filter(forma_pago__in=['TC', 'TD']).aggregate(t=Sum('monto'))['t'])
    total_abono = sum_or_0(pagos_qs.filter(forma_pago='AB').aggregate(t=Sum('monto'))['t'])

    # CXC Total
    total_pagado_global = sum_or_0(pagos_qs.aggregate(t=Sum('monto'))['t'])
    total_cxc = total_valor - total_pagado_global

    context = {
        'paciente_seleccionado': paciente_seleccionado,
        'saldo_paciente': saldo_paciente,
        'atenciones_hoy': atenciones_hoy,
        'estado_saldo': estado_saldo,
        # Totales Footer
        'total_valor': total_valor,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'total_tarjeta': total_tarjeta,
        'total_abono': total_abono,
        'total_cxc': total_cxc,
    }
    return render(request, 'recepcion/recepcion.html', context)


@login_required
def editar_atencion_view(request, atencion_id):
    atencion = get_object_or_404(Atencion, id=atencion_id)
    paciente = atencion.paciente
    
    tratamientos = Tratamiento.objects.all()
    doctores = Doctor.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- 1. ACTUALIZAR DOCTOR PRINCIPAL (DESDE ROW SUPERIOR) ---
        if action == "update_doctor_header":
             doctor_id = request.POST.get("doctor_id")
             if doctor_id:
                 atencion.doctor_id = doctor_id
                 atencion.save()
             return redirect("editar_atencion", atencion_id=atencion.id)

        # --- NEW: DELETE ATENTION ---
        elif action == "delete_atencion":
             atencion.delete()
             return redirect("recepcion")

        # --- 2. AGREGAR TRATAMIENTO ---
        elif action == "add_tratamiento":
            tratamiento_id = request.POST.get("tratamiento")
            doctor_id = request.POST.get("doctor") # Doctor específico del tratamiento
            
            # Helper to safely parse numbers
            comision_raw = request.POST.get("comision")
            if not comision_raw:
                comision_pct = 0
            else:
                comision_pct = comision_raw

            cantidad_raw = request.POST.get("cantidad")
            if not cantidad_raw:
                cantidad = 1
            else:
                try:
                    cantidad = int(cantidad_raw)
                except ValueError:
                    cantidad = 1

            precio = request.POST.get("precio")

            if tratamiento_id:
                tratamiento = Tratamiento.objects.get(id=tratamiento_id)
                
                # Si no se especifica precio, usar el base
                if not precio:
                    precio = tratamiento.precio_base
                
                # Si no se especifica doctor, usar el de la atención (si existe) o dejar vacío
                doctor_obj = None
                if doctor_id:
                     doctor_obj = Doctor.objects.get(id=doctor_id)
                elif atencion.doctor:
                     doctor_obj = atencion.doctor

                detalle = AtencionDetalle(
                    atencion=atencion,
                    tratamiento=tratamiento,
                    # El detalle NO tiene doctor propio en este modelo, hereda de la atención
                    # doctor=doctor_obj, 
                    porcentaje_comision=comision_pct,
                    cantidad=cantidad,
                    precio_base=precio
                )
                detalle.save()
            
            # Check if we should exit after adding
            if request.POST.get("save_and_exit") == "true":
                return redirect("recepcion")
                
            return redirect("editar_atencion", atencion_id=atencion.id)

        
        # --- 3. ELIMINAR TRATAMIENTO ---
        elif action == "delete_tratamiento":
            detalle_id = request.POST.get("detalle_id")
            AtencionDetalle.objects.filter(id=detalle_id, atencion=atencion).delete()

        # --- 4. FINALIZAR ATENCIÓN ---
        elif action == "finalizar_atencion":
            atencion.estado = "FINALIZADO"
            atencion.save()
            return redirect("recepcion")

        # --- 5. VALIDAR Y CERRAR (Rename to Save & Exit without locking) ---
        elif action == "validar_atencion":
            # Just redirect, but check if empty
            if not atencion.detalles.exists():
                 # Should be prevented by frontend, but safety check
                 return redirect("editar_atencion", atencion_id=atencion.id)
            
            # User requested NOT to lock/conciliate here.
            # atencion.validado = True  <-- REMOVED
            # atencion.save()
            return redirect("recepcion")

        return redirect("editar_atencion", atencion_id=atencion.id)

    # Calculos totales
    total_atencion = atencion.total_atencion_valor
    total_pagado = atencion.total_pagado
    saldo_pendiente_atencion = total_atencion - total_pagado

    context = {
        'atencion': atencion,
        'paciente': paciente,
        'tratamientos': tratamientos,
        'doctores': doctores,
        'total_atencion': total_atencion,
        'total_pagado': total_pagado,
        'saldo_pendiente_atencion': saldo_pendiente_atencion,
        'saldo_paciente': 0, # Placeholder
        'estado_saldo': 'aldia' # Placeholder
    }
    return render(request, 'recepcion/editar_atencion_final.html', context)


@login_required
def reportes_view(request):
    hoy = timezone.now().date()
    atenciones_hoy = Atencion.objects.filter(fecha__date=hoy).count()
    total_ingresos = 0 # Implementar
    
    context = {
        'atenciones_hoy': atenciones_hoy,
        'total_ingresos': total_ingresos
    }
    return render(request, 'reportes/reportes.html', context)

@login_required
def actualizar_pago_rapido(request, atencion_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            tipo = data.get('tipo')
            monto = data.get('monto')
            
            # Validar y convertir monto
            if monto == "" or monto is None:
                monto = 0
            monto = float(monto)

            atencion = Atencion.objects.get(id=atencion_id)
            
            if atencion.validado:
                return JsonResponse({'success': False, 'error': 'Atención cerrada, no se pueden editar pagos.'})

            # Actualizar el campo correspondiente
            # Logic for updating payments via Pago model
            # We assume one payment per type per attention for this simple interface
            from pagos_clinica.models import Pago

            if monto > 0:
                pago, created = Pago.objects.update_or_create(
                    atencion=atencion,
                    forma_pago=tipo,
                    defaults={'monto': monto}
                )
            else:
                # If amount is 0, delete the payment if it exists
                Pago.objects.filter(atencion=atencion, forma_pago=tipo).delete()
            
            # No need to call atencion.save() as properties are computed dynamically
            
            # Recalcular saldo pendiente para devolverlo
            nuevo_saldo = atencion.saldo_cxc
            
            return JsonResponse({'success': True, 'nuevo_saldo': nuevo_saldo})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def validar_atencion_rapida(request, atencion_id):
    if request.method == "POST":
        try:
            atencion = Atencion.objects.get(id=atencion_id)
            atencion.validado = True
            if atencion.estado != "FINALIZADO":
                atencion.estado = "FINALIZADO"
            atencion.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid Method'})
@login_required
def buscar_pacientes_ajax(request):
    """
    Retorna una lista JSON de pacientes que coinciden con 'q'.
    Se usa para el autocompletado en el buscador.
    """
    query = request.GET.get('q', '').strip()
    resultados = []
    
    if query and len(query) > 1: # Buscar solo si hay al menos 2 caracteres
        pacientes = Paciente.objects.filter(
            numero_identificacion__icontains=query
        ) | Paciente.objects.filter(
            nombres__icontains=query
        ) | Paciente.objects.filter(
            apellidos__icontains=query
        ) | Paciente.objects.filter(
             historia_clinica__icontains=query
        )
        
        # Limitar a 10 resultados para no saturar
        for p in pacientes[:10]: 
            resultados.append({
                'id': p.id,
                'nombre_mostrar': f"{p.nombres} {p.apellidos} ({p.numero_identificacion})",
                'historia_clinica': p.historia_clinica,
                'numero_identificacion': p.numero_identificacion
            })
            
    return JsonResponse({'results': resultados})

@csrf_exempt
@login_required
def update_detalle_tratamiento(request, detalle_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            field = data.get("field")
            value = data.get("value")

            detalle = get_object_or_404(AtencionDetalle, id=detalle_id)
            
            # Validar que la atención no esté cerrada
            if detalle.atencion.validado:
                return JsonResponse({"success": False, "error": "Atención cerrada/validada"})

            if field == "doctor":
                if value:
                    detalle.doctor = get_object_or_404(Doctor, id=value)
                else:
                    # Si no hay doctor específico, podemos dejarlo en None o asignar
                    # el de la atencion (aunque detalle.doctor es lo que cuenta)
                    detalle.doctor = None 
            elif field == "comision":
                detalle.porcentaje_comision = Decimal(value) if value else Decimal(0)
            elif field == "cantidad":
                detalle.cantidad = int(value) if value else 1
            elif field == "precio":
                detalle.precio_base = Decimal(value) if value else Decimal(0)
            elif field == "tratamiento":
                from tratamientos.models import Tratamiento
                nuevo_t = get_object_or_404(Tratamiento, id=value)
                detalle.tratamiento = nuevo_t
                detalle.precio_base = nuevo_t.precio_base # Update price automatically
            
            detalle.save()
            
            # Recalcular totales de atención (esto debería pasar en el save del modelo o aquí)
            detalle.atencion.save() 

            return JsonResponse({
                "success": True,
                "nuevo_total": float(detalle.total_calculado),
                "total_atencion": float(detalle.atencion.total_atencion_valor),
                "saldo_pendiente": float(detalle.atencion.saldo_cxc),
                "nuevo_saldo": float(detalle.atencion.saldo_cxc), # Alias
                "nuevo_precio": float(detalle.precio_base) # Para actualizar input si cambia trat
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método no permitido"})

@csrf_exempt
@login_required
def actualizar_observaciones(request, atencion_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            obs = data.get('observaciones', '')
            atencion = get_object_or_404(Atencion, id=atencion_id)
            
            if atencion.validado:
                return JsonResponse({'success': False, 'error': 'Atención cerrada, no se pueden modificar las observaciones.'})
            
            atencion.observaciones = obs
            atencion.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

