(function($) {
    'use strict';

    $(document).ready(function() {
        console.log('User inline location script loaded');

        // Buscar campos en el inline (tienen prefijos diferentes)
        var $estado = $('select[name$="-estado"]');
        var $municipio = $('select[name$="-municipio"]');
        var $parroquia = $('select[name$="-parroquia"]');

        console.log('Estado fields found:', $estado.length);
        console.log('Municipio fields found:', $municipio.length);
        console.log('Parroquia fields found:', $parroquia.length);

        if ($estado.length === 0) {
            // Intentar con IDs específicos del inline
            $estado = $('#id_userprofile-0-estado, #id_estado');
            $municipio = $('#id_userprofile-0-municipio, #id_municipio');
            $parroquia = $('#id_userprofile-0-parroquia, #id_parroquia');
            console.log('Retry - Estado:', $estado.length, 'Municipio:', $municipio.length, 'Parroquia:', $parroquia.length);
        }

        var estadoInicial = $estado.val();
        var municipioInicial = $municipio.val();

        // Cargar municipios cuando cambia el estado
        $estado.on('change', function() {
            var estadoId = $(this).val();
            console.log('Estado changed:', estadoId);

            $municipio.empty().append('<option value="">---------</option>');
            $parroquia.empty().append('<option value="">---------</option>');

            if (estadoId) {
                $.ajax({
                    url: '/registry/ajax/municipios/',
                    data: { estado_id: estadoId },
                    dataType: 'json',
                    success: function(data) {
                        console.log('Municipios loaded:', data.length);
                        $.each(data, function(i, item) {
                            $municipio.append($('<option>', {
                                value: item.id,
                                text: item.nombre
                            }));
                        });

                        if (municipioInicial) {
                            $municipio.val(municipioInicial);
                            $municipio.trigger('change');
                            municipioInicial = null;
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

            $parroquia.empty().append('<option value="">---------</option>');

            if (municipioId) {
                $.ajax({
                    url: '/registry/ajax/parroquias/',
                    data: { municipio_id: municipioId },
                    dataType: 'json',
                    success: function(data) {
                        console.log('Parroquias loaded:', data.length);
                        $.each(data, function(i, item) {
                            $parroquia.append($('<option>', {
                                value: item.id,
                                text: item.nombre
                            }));
                        });
                    },
                    error: function(xhr, status, error) {
                        console.error('Error loading parroquias:', error);
                    }
                });
            }
        });

        // Cargar datos iniciales si hay un estado seleccionado
        if (estadoInicial) {
            console.log('Triggering initial load for estado:', estadoInicial);
            $estado.trigger('change');
        }
    });
})(jQuery || django.jQuery);
