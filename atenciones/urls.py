from django.urls import path
from .views_recepcion import (
    recepcion_view, editar_atencion_view, reportes_view, 
    actualizar_pago_rapido, validar_atencion_rapida, 
    buscar_pacientes_ajax, update_detalle_tratamiento, 
    actualizar_observaciones
)

urlpatterns = [
    path('recepcion/', recepcion_view, name='recepcion'),
    path('recepcion/editar/<int:atencion_id>/', editar_atencion_view, name='editar_atencion'),
    path('atencion/<int:atencion_id>/', editar_atencion_view, name='editar_atencion_legacy'), # Alias para evitar 404s
    path('recepcion/update_payment/<int:atencion_id>/', actualizar_pago_rapido, name='actualizar_pago_rapido'),
    path('recepcion/update_observaciones/<int:atencion_id>/', actualizar_observaciones, name='actualizar_observaciones'),
    path('recepcion/validar/<int:atencion_id>/', validar_atencion_rapida, name='validar_atencion_rapida'),
    path('recepcion/update_detalle/<int:detalle_id>/', update_detalle_tratamiento, name='update_detalle_tratamiento'),
    path('buscar_pacientes/', buscar_pacientes_ajax, name='buscar_pacientes_ajax'),
    path('reportes/', reportes_view, name='reportes'),
]

