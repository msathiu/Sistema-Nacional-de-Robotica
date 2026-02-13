(function($) {
    'use strict';
    
    $(document).ready(function() {
        console.log('UserProfile location script loaded');
        
        var $estado = $('#id_estado');
        var $municipio = $('#id_municipio');
        var $parroquia = $('#id_parroquia');
        
        var estadoInicial = $estado.val();
        var municipioInicial = $municipio.val();
        var parroquiaInicial = $parroquia.val();
        var cargaInicial = true;
        
        console.log('Valores iniciales - Estado:', estadoInicial, 'Municipio:', municipioInicial, 'Parroquia:', parroquiaInicial);
        
        // Cargar municipios cuando cambia el estado
        $estado.on('change', function() {
            var estadoId = $(this).val();
            console.log('Estado changed:', estadoId);
            
            // Solo limpiar si no es la carga inicial
            if (!cargaInicial) {
                $municipio.empty().append('<option value="">---------</option>');
                $parroquia.empty().append('<option value="">---------</option>');
            }
            
            if (estadoId) {
                $.ajax({
                    url: '/registry/ajax/municipios/',
                    data: { estado_id: estadoId },
                    dataType: 'json',
                    success: function(data) {
                        console.log('Municipios loaded:', data.length);
                        
                        if (!cargaInicial) {
                            $municipio.empty().append('<option value="">---------</option>');
                        }
                        
                        $.each(data, function(i, item) {
                            var exists = $municipio.find('option[value="' + item.id + '"]').length > 0;
                            if (!exists) {
                                $municipio.append($('<option>', {
                                    value: item.id,
                                    text: item.nombre
                                }));
                            }
                        });
                        
                        // Restaurar valor inicial
                        if (cargaInicial && municipioInicial) {
                            $municipio.val(municipioInicial);
                            $municipio.trigger('change');
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error('Error loading municipios:', error);
                    }
                });
            }
        });
        
        // Cargar parroquias cuando cambia el municipio
        $municipio.on('change', function() {
            var municipioId = $(this).val();
            console.log('Municipio changed:', municipioId);
            
            // Solo limpiar si no es la carga inicial
            if (!cargaInicial) {
                $parroquia.empty().append('<option value="">---------</option>');
            }
            
            if (municipioId) {
                $.ajax({
                    url: '/registry/ajax/parroquias/',
                    data: { municipio_id: municipioId },
                    dataType: 'json',
                    success: function(data) {
                        console.log('Parroquias loaded:', data.length);
                        
                        if (!cargaInicial) {
                            $parroquia.empty().append('<option value="">---------</option>');
                        }
                        
                        $.each(data, function(i, item) {
                            var exists = $parroquia.find('option[value="' + item.id + '"]').length > 0;
                            if (!exists) {
                                $parroquia.append($('<option>', {
                                    value: item.id,
                                    text: item.nombre
                                }));
                            }
                        });
                        
                        // Restaurar valor inicial
                        if (cargaInicial && parroquiaInicial) {
                            $parroquia.val(parroquiaInicial);
                        }
                        
                        cargaInicial = false;
                    },
                    error: function(xhr, status, error) {
                        console.error('Error loading parroquias:', error);
                    }
                });
            } else {
                cargaInicial = false;
            }
        });
        
        // Cargar datos iniciales solo si hay un estado seleccionado
        if (estadoInicial) {
            console.log('Triggering initial load for estado:', estadoInicial);
            $estado.trigger('change');
        } else {
            cargaInicial = false;
        }
    });
})(jQuery || django.jQuery);
