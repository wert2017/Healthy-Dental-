from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Paciente
from .forms import PacienteForm

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
