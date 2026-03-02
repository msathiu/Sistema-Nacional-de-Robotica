from django.shortcuts import render
from pathlib import Path
from django.conf import settings
from users.decorators import admin_access_required


@admin_access_required
def ver_logs_sistema(request):
    """Vista para ver los logs del sistema en el admin"""
    log_file = Path(settings.BASE_DIR) / 'logs' / 'django.log'
    
    # Leer últimas 500 líneas
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            logs = lines[-500:]  # Últimas 500 líneas
            logs.reverse()  # Más recientes primero
    except FileNotFoundError:
        logs = ['No se encontró el archivo de logs']
    except Exception as e:
        logs = [f'Error al leer logs: {str(e)}']
    
    return render(request, 'admin/logs_sistema.html', {
        'logs': logs,
        'total_lines': len(logs)
    })
