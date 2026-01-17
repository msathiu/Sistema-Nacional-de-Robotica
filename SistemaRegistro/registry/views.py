from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Municipio
from django.contrib import messages
from .forms import InstitucionForm

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

def registro_institucion(request):   # Argenis agregado como prueba Guardamos la institución (estará inactiva por defecto)
    if request.method == 'POST':
        form = InstitucionForm(request.POST)
        if form.is_valid():
            institucion = form.save() # Guardamos la institución (estará inactiva por defecto)
            # Renderizamos la página de espera pasando el nombre, Mostramos un mensaje de espera
            return render(request, 'registro_exitoso_espera.html', {
                'nombre_institucion': institucion.nombre
            })
    else:
        form = InstitucionForm()
    
    return render(request, 'registry/registro_institucion.html', {'form': form})
