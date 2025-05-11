// Función para cargar el contenido en la modal y manejar el formulario
function loadModalAndHandleForm(btn, url) {
    var contratoId = btn.getAttribute('data-id');
    var modalBody = document.querySelector('#editModal .modal-body');
    modalBody.innerHTML = '<p>Cargando...</p>';

    // Mostrar la modal de edición
    $('#editModal').modal('show');

    // Cargar el contenido del formulario en la modal de edición
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url.replace('0', contratoId));
    xhr.onload = function() {
        if (xhr.status === 200) {
            modalBody.innerHTML = xhr.responseText;

            // Manejar el envío del formulario dentro de la modal de edición
            var form = modalBody.querySelector('form');
            form.addEventListener('submit', function(event) {
                event.preventDefault();

                // Mostrar la modal de carga
                $('#loadingModal').modal('show');

                var formData = new FormData(form);
                var saveXhr = new XMLHttpRequest();
                saveXhr.open('POST', url.replace('0', contratoId));
                saveXhr.setRequestHeader('X-CSRFToken', document.querySelector('[name=csrfmiddlewaretoken]').value); // Asegúrate de pasar el CSRF token correctamente
                saveXhr.onload = function() {
                    // Ocultar la modal de carga
                    $('#loadingModal').modal('hide');

                    if (saveXhr.status === 200) {
                        try {
                            var response = JSON.parse(saveXhr.responseText);
                            
                            if (response.success) {
                                // Cerrar la modal de edición
                                $('#editModal').modal('hide');
                                // Actualizar la lista de contratos (si es necesario)
                                // updateContractList();
                            } else {
                                // Mostrar mensaje de error en la modal de edición
                                modalBody.innerHTML = saveXhr.responseText;
                            }
                        } catch (e) {
                            // Mostrar mensaje de error en la modal de edición
                            modalBody.innerHTML = '<p>Error al procesar la respuesta.</p>';
                        }
                    } else {
                        // Mostrar mensaje de error en la modal de edición
                        modalBody.innerHTML = '<p>Error al guardar la información.</p>';
                    }
                };
                saveXhr.send(formData);
            });
        } else {
            // Mostrar mensaje de error en la modal de edición
            modalBody.innerHTML = '<p>Error al cargar la vista.</p>';
        }
    };
    xhr.send();
}

// Función auxiliar para inicializar todos los elementos del formulario en el modal
function initializeModalFormElements(modalElement) {
    var $modal = $(modalElement);
    
    // Inicializar Select2
    $modal.find('.select2').select2({
        dropdownParent: $modal,
        theme: 'bootstrap-5',
        width: '100%'
    });
    
    // Inicializar DatePicker si existe
    if ($.fn.datepicker) {
        $modal.find('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            language: 'es'
        });
    }
    
    // Inicializar selectores dependientes (país, estado, ciudad)
    initializeDependentSelectors($modal);
    
    // Inicializar comportamiento según tipo de tercero
    initializeThirdPartyTypeToggle($modal);
    
    // Inicializar previsualización de imagen
    initializeImagePreview($modal);
}

// Función para inicializar selectores dependientes
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

// Función para inicializar comportamiento según tipo de tercero
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
    toggleFieldsByType();
    $container.find('#id_third_party_type').change(toggleFieldsByType);
}

// Función para inicializar previsualización de imagen
function initializeImagePreview($container) {
    $container.find('#id_image').change(function() {
        var input = this;
        if (input.files && input.files[0]) {
            var reader = new FileReader();
            
            reader.onload = function(e) {
                var previewElement = $container.find('#preview-image');
                
                // Si no existe el elemento de previsualización, crearlo
                if (previewElement.length === 0) {
                    previewElement = $('<img id="preview-image" class="img-fluid mt-2 mb-3" alt="Vista previa de imagen" style="max-height: 200px;">');
                    $(input).after(previewElement);
                }
                
                // Mostrar la imagen
                previewElement.attr('src', e.target.result).show();
            }
            
            reader.readAsDataURL(input.files[0]);
        }
    });
}

function handleModalActions() {
    // Inicializar eventos de cierre
    $('.modal').on('hidden.bs.modal', function() {
        $(this).find('form').trigger('reset');
        $(this).find('.is-invalid').removeClass('is-invalid');
        $(this).find('.invalid-feedback').remove();
    });

    // Manejar recarga de DataTable
    window.addEventListener('reload-datatable', function() {
        if ($.fn.DataTable.isDataTable('#main-table')) {
            $('#main-table').DataTable().ajax.reload(null, false);
        }
    });

    // Manejar cierre forzado
    window.modalCleanup = function() {
        $('.modal').modal('hide');
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();
    };
}

// Inicializar al cargar la página
$(document).ready(function() {
    handleModalActions();
});