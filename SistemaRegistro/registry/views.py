from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Municipio

def registro_publico(request):
    """Vista temporal - redirige al nuevo sistema de registro"""
    return redirect('home')  # Redirige a la página principal

def registro_success(request):
    """Vista de éxito de registro"""
    return render(request, 'registry/registro_success.html')

def load_municipios(request):
    """Cargar municipios basados en el estado seleccionado"""
    estado_id = request.GET.get('estado_id')
    if estado_id:
        municipios = Municipio.objects.filter(estado_id=estado_id).order_by('nombre')
        return JsonResponse(list(municipios.values('id', 'nombre')), safe=False)
    return JsonResponse([], safe=False)