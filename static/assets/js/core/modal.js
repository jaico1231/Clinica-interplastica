function loadModalAndHandleForm(btn, url) {
    // Limpiar cualquier modal o backdrop existente
    $('.modal-backdrop').remove();
    $('body').removeClass('modal-open').css({
        'overflow': '',
        'padding-right': ''
    });
    
    var contratoId = btn.getAttribute('data-id');
    var modalBody = document.querySelector('#editModal .modal-body');
    modalBody.innerHTML = '<p>Cargando...</p>';

    // SOLUCIÓN: Modificar la manera en que se construye la URL
    // En lugar de reemplazar directamente '0', usamos un enfoque más seguro
    if (url.includes('/0/')) {
        // Reemplazar solo cuando el 0 está entre barras /0/
        // Esto evita reemplazar ceros que son parte de los IDs
        var urlParts = url.split('/0/');
        if (urlParts.length === 2) {
            url = urlParts[0] + '/' + contratoId + '/' + urlParts[1];
        } else {
            // Si por alguna razón hay múltiples /0/, usar una expresión regular
            url = url.replace(/\/0\//, '/' + contratoId + '/');
        }
    } else {
        // En caso de que la URL no tenga el formato esperado,
        // simplemente registramos para depuración y continuamos
        console.log("URL sin placeholder /0/:", url);
    }

    // Primera llamada AJAX para cargar el contenido del modal
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url);
    console.log("URL final utilizada:", url);
    
    // Agregar cabeceras necesarias
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.setRequestHeader('Accept', 'application/json, text/html');
    
    xhr.onload = function() {
        if (xhr.status === 200) {
            modalBody.innerHTML = xhr.responseText;
            $('#editModal').modal('show');

            // Inicializar Select2 después de cargar el contenido
            setTimeout(function() {
                $(modalBody).find('select.select2').each(function() {
                    $(this).select2({
                        dropdownParent: $('#editModal'),
                        width: '100%'
                    });
                });
            }, 100);

            var form = modalBody.querySelector('form');
            if (form) {
                form.addEventListener('submit', function(event) {
                    event.preventDefault();

                    // Deshabilitar el botón de envío para evitar múltiples envíos
                    var submitButton = form.querySelector('[type="submit"]');
                    if (submitButton) {
                        submitButton.disabled = true;
                        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Procesando...';
                    }

                    var formData = new FormData(form);
                    
                    // Segunda llamada AJAX para enviar el formulario
                    var saveXhr = new XMLHttpRequest();
                    
                    // SOLUCIÓN: Tratar la URL de acción del formulario de manera similar
                    var formAction = form.getAttribute('action');
                    if (!formAction) {
                        if (url.includes('/0/')) {
                            var urlParts = url.split('/0/');
                            if (urlParts.length === 2) {
                                formAction = urlParts[0] + '/' + contratoId + '/' + urlParts[1];
                            } else {
                                formAction = url.replace(/\/0\//, '/' + contratoId + '/');
                            }
                        } else {
                            formAction = url;
                        }
                    }
                    
                    saveXhr.open('POST', formAction);
                    
                    // Agregar cabeceras necesarias
                    saveXhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                    saveXhr.setRequestHeader('Accept', 'application/json');
                    
                    // Agregar token CSRF
                    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                    if (csrfToken) {
                        saveXhr.setRequestHeader('X-CSRFToken', csrfToken.value);
                    }
                    
                    saveXhr.onload = function() {
                        try {
                            var contentType = saveXhr.getResponseHeader("Content-Type");
                            if (contentType && contentType.indexOf("application/json") !== -1) {
                                // La respuesta es JSON
                                var response = JSON.parse(saveXhr.responseText);
                                
                                if (response.success) {
                                    // Operación exitosa
                                    $('#editModal').modal('hide');
                                    
                                    // Limpiar cualquier backdrop
                                    setTimeout(function() {
                                        $('.modal-backdrop').remove();
                                        $('body').removeClass('modal-open').css({
                                            'overflow': '',
                                            'padding-right': ''
                                        });
                                    }, 300);
                                    
                                    // Mostrar mensaje de éxito
                                    if (typeof toastr !== 'undefined') {
                                        toastr.success(response.message || 'Operación exitosa');
                                    } else {
                                        // alert(response.message || 'Operación exitosa');
                                        
                                    }
                                    
                                    // Redireccionar o actualizar datos
                                    if (response.redirect) {
                                        setTimeout(function() {
                                            window.location.href = response.redirect;
                                        }, 500);
                                    } else if (typeof updateContractList === 'function') {
                                        updateContractList();
                                    } else {
                                        setTimeout(function() {
                                            location.reload();
                                        }, 500);
                                    }
                                } else {
                                    // La operación no fue exitosa
                                    if (submitButton) {
                                        submitButton.disabled = false;
                                        submitButton.innerHTML = 'Guardar';
                                    }
                                    
                                    if (response.errors) {
                                        // Manejar errores de validación
                                        Object.keys(response.errors).forEach(function(field) {
                                            var input = form.querySelector('[name="' + field + '"]');
                                            if (input) {
                                                input.classList.add('is-invalid');
                                                var errorMessage = Array.isArray(response.errors[field]) ? 
                                                    response.errors[field][0] : response.errors[field];
                                                var feedbackElement = document.createElement('div');
                                                feedbackElement.className = 'invalid-feedback';
                                                feedbackElement.textContent = errorMessage;
                                                input.parentNode.appendChild(feedbackElement);
                                            }
                                        });
                                        
                                        // Mostrar primer error en toastr
                                        var firstError = Object.values(response.errors)[0];
                                        if (Array.isArray(firstError)) firstError = firstError[0];
                                        
                                        if (typeof toastr !== 'undefined') {
                                            toastr.error(firstError);
                                        } else {
                                            alert(firstError);
                                        }
                                    } else if (response.message) {
                                        // Mostrar mensaje de error
                                        if (typeof toastr !== 'undefined') {
                                            toastr.error(response.message);
                                        } else {
                                            alert(response.message);
                                        }
                                    }
                                }
                            } else {
                                // La respuesta no es JSON, probablemente HTML
                                
                                // Primero habilitamos el botón de nuevo
                                if (submitButton) {
                                    submitButton.disabled = false;
                                    submitButton.innerHTML = 'Guardar';
                                }
                                
                                // Si la respuesta contiene un mensaje de éxito, asumimos que funcionó
                                if (saveXhr.responseText.indexOf('success') !== -1 || 
                                    saveXhr.responseText.indexOf('éxito') !== -1 ||
                                    saveXhr.status === 302) {
                                    
                                    // Cerrar el modal
                                    $('#editModal').modal('hide');
                                    
                                    // Limpiar backdrops
                                    setTimeout(function() {
                                        $('.modal-backdrop').remove();
                                        $('body').removeClass('modal-open').css({
                                            'overflow': '',
                                            'padding-right': ''
                                        });
                                    }, 300);
                                    
                                    // Mostrar mensaje de éxito
                                    if (typeof toastr !== 'undefined') {
                                        toastr.success('Operación completada');
                                    } else {
                                        // alert('Operación completada');
                                    }
                                    
                                    // Recargar la página después de un breve retraso
                                    setTimeout(function() {
                                        location.reload();
                                    }, 500);
                                } else {
                                    // Parece ser un formulario con errores, actualizar el contenido
                                    modalBody.innerHTML = saveXhr.responseText;
                                    
                                    // Reinicializar Select2 después de actualizar el contenido
                                    setTimeout(function() {
                                        $(modalBody).find('select.select2').each(function() {
                                            $(this).select2({
                                                dropdownParent: $('#editModal'),
                                                width: '100%'
                                            });
                                        });
                                    }, 100);
                                }
                            }
                        } catch (e) {
                            // Error al procesar la respuesta
                            if (submitButton) {
                                submitButton.disabled = false;
                                submitButton.innerHTML = 'Guardar';
                            }
                            
                            // Intentamos determinar si la operación fue exitosa a pesar del error
                            if (saveXhr.status === 200 || saveXhr.status === 302) {
                                // Cerrar el modal asumiendo que fue exitoso
                                $('#editModal').modal('hide');
                                
                                // Limpiar backdrops
                                setTimeout(function() {
                                    $('.modal-backdrop').remove();
                                    $('body').removeClass('modal-open').css({
                                        'overflow': '',
                                        'padding-right': ''
                                    });
                                }, 300);
                                
                                // Mostrar mensaje
                                if (typeof toastr !== 'undefined') {
                                    toastr.success('Operación completada');
                                } else {
                                    alert('Operación completada');
                                }
                                
                                // Recargar la página
                                setTimeout(function() {
                                    location.reload();
                                }, 500);
                            } else {
                                // Mostrar la respuesta en la modal
                                modalBody.innerHTML = saveXhr.responseText;
                                
                                // Reinicializar Select2
                                setTimeout(function() {
                                    $(modalBody).find('select.select2').each(function() {
                                        $(this).select2({
                                            dropdownParent: $('#editModal'),
                                            width: '100%'
                                        });
                                    });
                                }, 100);
                            }
                        }
                    };
                    
                    saveXhr.onerror = function() {
                        // Error de red
                        if (submitButton) {
                            submitButton.disabled = false;
                            submitButton.innerHTML = 'Guardar';
                        }
                        
                        if (typeof toastr !== 'undefined') {
                            toastr.error('Error de conexión. Por favor, verifique su conexión e inténtelo nuevamente.');
                        } else {
                            alert('Error de conexión. Por favor, verifique su conexión e inténtelo nuevamente.');
                        }
                    };
                    
                    saveXhr.send(formData);
                });
            }
        } else {
            // Error al cargar la vista
            if (typeof toastr !== 'undefined') {
                toastr.error('Error al cargar la vista.');
            } else {
                alert('Error al cargar la vista.');
            }
            
            modalBody.innerHTML = '<p>Error al cargar la vista. Por favor, inténtelo nuevamente.</p>';
        }
    };
    
    xhr.onerror = function() {
        if (typeof toastr !== 'undefined') {
            toastr.error('Error de conexión. Por favor, verifique su conexión e inténtelo nuevamente.');
        } else {
            alert('Error de conexión. Por favor, verifique su conexión e inténtelo nuevamente.');
        }
        
        modalBody.innerHTML = '<p>Error de conexión. Por favor, verifique su conexión e inténtelo nuevamente.</p>';
    };
    
    xhr.send();
}