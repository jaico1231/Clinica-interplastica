// / Esta función debe incluirse en el archivo JS base o en un archivo separado
// Asegúrate de que sea accesible globalmente

/**
 * Inicializa todos los elementos de formulario dentro de un contenedor (modal)
 * @param {HTMLElement} container - El contenedor donde se inicializarán los elementos
 */
function initializeModalFormElements(container) {
    var $container = $(container);
    
    // Inicializar Select2
    $container.find('.select2').each(function() {
        var $select = $(this);
        
        // Evitar inicializar dos veces
        if ($select.hasClass('select2-hidden-accessible')) {
            $select.select2('destroy');
        }
        
        $select.select2({
            dropdownParent: $container.hasClass('modal') ? $container : $('body'),
            theme: 'bootstrap-5',
            width: $select.data('width') || '100%',
            placeholder: $select.data('placeholder') || 'Seleccione una opción',
            allowClear: $select.data('allow-clear') || false
        });
    });
    
    // Inicializar DatePicker si existe
    if ($.fn.datepicker) {
        $container.find('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            language: 'es',
            todayHighlight: true,
            todayBtn: 'linked'
        });
    }
    
    // Inicializar selectores dependientes (país, estado, ciudad)
    initializeDependentSelectors($container);
    
    // Inicializar comportamiento según tipo de tercero
    initializeThirdPartyTypeToggle($container);
    
    // Inicializar previsualización de imagen
    initializeImagePreview($container);
    
    // Inicializar máscaras de entrada si existe inputmask
    if ($.fn.inputmask) {
        $container.find('.phone-mask').inputmask('(999) 999-9999');
        $container.find('.date-mask').inputmask('9999-99-99');
        $container.find('.document-mask').inputmask('999999999999');
        $container.find('.decimal-mask').inputmask('decimal', {
            radixPoint: '.',
            groupSeparator: ',',
            digits: 2,
            autoGroup: true
        });
    }
    
    // Inicializar validación de formularios si existe
    if ($.fn.validate) {
        $container.find('form').validate({
            errorElement: 'div',
            errorClass: 'invalid-feedback',
            highlight: function(element) {
                $(element).addClass('is-invalid').removeClass('is-valid');
            },
            unhighlight: function(element) {
                $(element).removeClass('is-invalid').addClass('is-valid');
            },
            errorPlacement: function(error, element) {
                error.insertAfter(element);
            }
        });
    }
}

/**
 * Inicializa selectores dependientes (país -> estado -> ciudad)
 * @param {jQuery} $container - El contenedor jQuery
 */
function initializeDependentSelectors($container) {
    // Manejar cambio en país para cargar departamentos
    $container.find('#id_country').change(function() {
        var countryId = $(this).val();
        if (countryId) {
            // Limpiar selects dependientes
            $container.find('#id_state').empty().append('<option value="">Seleccione departamento</option>');
            $container.find('#id_city').empty().append('<option value="">Seleccione ciudad</option>');
            
            // Cargar departamentos según país seleccionado
            $.ajax({
                url: '/common/ajax/load-states/',
                data: {
                    'country_id': countryId
                },
                dataType: 'json',
                success: function(data) {
                    $.each(data, function(key, value) {
                        $container.find('#id_state').append('<option value="' + value.id + '">' + value.name + '</option>');
                    });
                }
            });
        } else {
            // Si no hay país, vaciar departamentos y ciudades
            $container.find('#id_state').empty().append('<option value="">Seleccione departamento</option>');
            $container.find('#id_city').empty().append('<option value="">Seleccione ciudad</option>');
        }
    });
    
    // Manejar cambio en departamento para cargar ciudades
    $container.find('#id_state').change(function() {
        var stateId = $(this).val();
        if (stateId) {
            // Limpiar ciudad
            $container.find('#id_city').empty().append('<option value="">Seleccione ciudad</option>');
            
            // Cargar ciudades según departamento seleccionado
            $.ajax({
                url: '/common/ajax/load-cities/',
                data: {
                    'state_id': stateId
                },
                dataType: 'json',
                success: function(data) {
                    $.each(data, function(key, value) {
                        $container.find('#id_city').append('<option value="' + value.id + '">' + value.name + '</option>');
                    });
                }
            });
        } else {
            // Si no hay departamento, vaciar ciudades
            $container.find('#id_city').empty().append('<option value="">Seleccione ciudad</option>');
        }
    });
}

/**
 * Inicializa comportamiento según tipo de tercero
 * @param {jQuery} $container - El contenedor jQuery
 */
function initializeThirdPartyTypeToggle($container) {
    function toggleFieldsByType() {
        var thirdPartyType = $container.find('#id_third_party_type option:selected').text();
        
        if (thirdPartyType === 'Persona Natural') {
            // Mostrar campos de persona natural, ocultar campos de empresa
            $container.find('#div_id_first_name, #div_id_last_name').show();
            $container.find('#div_id_company_name, #div_id_trade_name').hide();
            
            // Hacer requeridos campos de persona natural
            $container.find('#id_first_name').prop('required', true);
            $container.find('#id_last_name').prop('required', true);
            
            // Hacer opcionales campos de empresa
            $container.find('#id_company_name, #id_trade_name').prop('required', false);
        } 
        else if (thirdPartyType === 'Persona Jurídica') {
            // Mostrar campos de empresa, ocultar campos de persona natural
            $container.find('#div_id_company_name, #div_id_trade_name').show();
            $container.find('#div_id_first_name, #div_id_last_name').hide();
            
            // Hacer requeridos campos de empresa
            $container.find('#id_company_name').prop('required', true);
            
            // Hacer opcionales campos de persona natural
            $container.find('#id_first_name, #id_last_name').prop('required', false);
        }
        else {
            // Para otros tipos, mostrar todos los campos
            $container.find('#div_id_first_name, #div_id_last_name, #div_id_company_name, #div_id_trade_name').show();
        }
    }
    
    // Ejecutar al inicializar y cuando cambie el tipo de tercero
    if ($container.find('#id_third_party_type').length) {
        toggleFieldsByType();
        $container.find('#id_third_party_type').change(toggleFieldsByType);
    }
}

/**
 * Inicializa previsualización de imagen
 * @param {jQuery} $container - El contenedor jQuery
 */
function initializeImagePreview($container) {
    $container.find('input[type="file"][accept*="image"]').change(function() {
        var input = this;
        if (input.files && input.files[0]) {
            var reader = new FileReader();
            
            reader.onload = function(e) {
                var previewElement = $container.find('#preview-image');
                
                // Si no existe el elemento de previsualización, crearlo
                if (previewElement.length === 0) {
                    previewElement = $('<img id="preview-image" class="img-fluid mt-2 mb-3 border rounded" alt="Vista previa de imagen" style="max-height: 200px;">');
                    $(input).after(previewElement);
                }
                
                // Mostrar la imagen
                previewElement.attr('src', e.target.result).show();
            }
            
            reader.readAsDataURL(input.files[0]);
        }
    });
}