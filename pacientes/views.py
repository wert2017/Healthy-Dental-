from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from .models import Paciente, FotoPaciente
from .forms import PacienteForm, FotoPacienteForm

@login_required
def crear_paciente_view(request):
    if request.method == "POST":
        form = PacienteForm(request.POST)
        if form.is_valid():
            paciente = form.save()
            # Redirigir a Recepción buscando por la cédula o ID para seleccionarlo
            return redirect(f"/recepcion/?q={paciente.numero_identificacion}")
    else:
        form = PacienteForm()
    
    return render(request, 'pacientes/crear_paciente.html', {'form': form})

@login_required
def lista_pacientes(request):
    q = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.all().order_by('apellidos', 'nombres')

    if q:
        pacientes = pacientes.filter(
            Q(historia_clinica__icontains=q) |
            Q(nombres__icontains=q) |
            Q(apellidos__icontains=q) |
            Q(numero_identificacion__icontains=q)
        )

    return render(request, 'pacientes/lista_pacientes.html', {
        'pacientes': pacientes,
        'q': q
    })

# ==========================================
# MÓDULO INDEPENDIENTE DE FOTOGRAFÍA CLÍNICA
# ==========================================

@login_required
def modulo_fotos_view(request):
    """
    Vista principal del Módulo de Fotografía Clínica.
    Permite buscar rápida y cómodamente a un paciente desde el móvil o PC.
    """
    q = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.filter(activo=True).annotate(total_fotos=Count('fotos')).order_by('-fecha_creacion')

    if q:
        pacientes = pacientes.filter(
            Q(historia_clinica__icontains=q) |
            Q(nombres__icontains=q) |
            Q(apellidos__icontains=q) |
            Q(numero_identificacion__icontains=q)
        )

    # Si la búsqueda devuelve exactamente 1 paciente, redirigir directamente a su galería
    if q and pacientes.count() == 1:
        return redirect('fotos_paciente', paciente_id=pacientes.first().id)

    # Pacientes con fotos recientes para acceso rápido
    pacientes_recientes = Paciente.objects.filter(fotos__isnull=False).distinct().order_by('-fotos__fecha_registro')[:10]

    return render(request, 'pacientes/modulo_fotos.html', {
        'pacientes': pacientes[:30],  # Limitar a los 30 más relevantes
        'pacientes_recientes': pacientes_recientes,
        'q': q,
    })


@login_required
def fotos_paciente_detalle_view(request, paciente_id):
    """
    Vista detallada del Historial Fotográfico de un Paciente.
    Incluye formulario de subida/captura desde móvil, filtro por categoría y comparador de evolución.
    """
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if request.method == 'POST':
        form = FotoPacienteForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.paciente = paciente
            foto.save()
            messages.success(request, f"📸 Fotografía guardada exitosamente para {paciente.nombre_mostrar()}.")
            return redirect('fotos_paciente', paciente_id=paciente.id)
        else:
            messages.error(request, "Error al guardar la fotografía. Por favor verifica el archivo ingresado.")
    else:
        form = FotoPacienteForm()

    # Filtros opcionales
    categoria_filtro = request.GET.get('categoria', '')
    etapa_filtro = request.GET.get('etapa', '')

    fotos = paciente.fotos.all()

    if categoria_filtro:
        fotos = fotos.filter(categoria=categoria_filtro)
    if etapa_filtro:
        fotos = fotos.filter(etapa=etapa_filtro)

    # Opciones de choices para filtros
    categorias = FotoPaciente.CATEGORIA_CHOICES
    etapas = FotoPaciente.ETAPA_CHOICES

    return render(request, 'pacientes/fotos_paciente.html', {
        'paciente': paciente,
        'fotos': fotos,
        'form': form,
        'categorias': categorias,
        'etapas': etapas,
        'categoria_filtro': categoria_filtro,
        'etapa_filtro': etapa_filtro,
    })


@login_required
def eliminar_foto_view(request, foto_id):
    """
    Eliminar una fotografía del historial.
    """
    foto = get_object_or_404(FotoPaciente, id=foto_id)
    paciente_id = foto.paciente.id
    if request.method == 'POST':
        foto.imagen.delete(save=False)  # Borrar archivo físico
        foto.delete()
        messages.success(request, "Fotografía eliminada del historial.")
    return redirect('fotos_paciente', paciente_id=paciente_id)

