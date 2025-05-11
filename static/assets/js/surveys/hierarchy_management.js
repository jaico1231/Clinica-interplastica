/**
 * hierarchy_management.js - Script para gestionar elementos de jerarquía
 * 
 * Este script maneja la interacción con elementos de jerarquía desde la vista de detalle
 * de la encuesta, incluyendo la carga, conteo y actualización de elementos.
 */

// Cuando el documento está listo, inicializamos los componentes
$(document).ready(function() {
    // Inicializar los contadores de elementos de jerarquía
    initHierarchyCounters();
    
    // Configurar manejadores de eventos para botones relacionados con la jerarquía
    setupHierarchyButtons();
});

/**
 * Inicializa los contadores de elementos de jerarquía para cada pregunta
 * Realiza una petición AJAX para obtener el conteo exacto de elementos activos
 */
function initHierarchyCounters() {
    // Para cada botón de visualización de elementos de jerarquía
    $('.ViewHierarchyItemsBtn').each(function() {
        const questionId = $(this).data('question-id');
        updateHierarchyItemCount(questionId);
    });
}

/**
 * Actualiza el contador de elementos de jerarquía para una pregunta específica
 * @param {number} questionId - ID de la pregunta
 */
function updateHierarchyItemCount(questionId) {
    // Construir la URL para obtener los elementos de jerarquía
    const url = SURVEY_URLS.getHierarchyItems.replace('{questionId}', questionId);
    
    // Realizar una petición AJAX para obtener los elementos activos
    $.ajax({
        url: url,
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            // Contar solo los elementos activos (no eliminados)
            const activeItemsCount = Array.isArray(response.items) ? response.items.length : 0;
            
            // Actualizar el contador en la interfaz
            $(`#hierarchy-count-${questionId}`).text(activeItemsCount);
        },
        error: function() {
            // En caso de error, mostrar 0 elementos
            $(`#hierarchy-count-${questionId}`).text('0');
        }
    });
}

/**
 * Configura los manejadores de eventos para los botones relacionados con elementos de jerarquía
 */
function setupHierarchyButtons() {
    // Manejador para el botón de visualización de elementos de jerarquía
    $(document).on('click', '.ViewHierarchyItemsBtn', function() {
        const questionId = $(this).data('question-id');
        openHierarchyItemsModal(questionId);
    });
    
    // Manejador para el botón de añadir elemento de jerarquía desde el modal
    $(document).on('click', '#addHierarchyItemBtn', function() {
        const questionId = $('#hierarchyItemsModal').data('question-id');
        addNewHierarchyItem(questionId);
    });
}

/**
 * Abre el modal de elementos de jerarquía para una pregunta específica
 * @param {number} questionId - ID de la pregunta
 */
function openHierarchyItemsModal(questionId) {
    const modal = $('#hierarchyItemsModal');
    
    // Almacenar el ID de la pregunta en el modal para referencia
    modal.data('question-id', questionId);
    
    // Mostrar indicador de carga
    $('#hierarchy-items-container').html('<div class="text-center py-4"><div class="spinner-border" role="status"></div></div>');
    
    // Construir la URL para obtener los elementos de jerarquía
    const url = SURVEY_URLS.getHierarchyItems.replace('{questionId}', questionId);
    
    // Cargar los elementos de jerarquía mediante AJAX
    $.ajax({
        url: url,
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            // Renderizar los elementos en el contenedor
            renderHierarchyItems(response.items);
            
            // Actualizar el contador en la vista principal
            updateHierarchyItemCount(questionId);
        },
        error: function() {
            // Mostrar mensaje de error
            $('#hierarchy-items-container').html('<div class="alert alert-danger">Error al cargar los elementos</div>');
        }
    });
    
    // Mostrar el modal
    modal.modal('show');
}

/**
 * Renderiza los elementos de jerarquía en el contenedor del modal
 * @param {Array} items - Lista de elementos de jerarquía
 */
function renderHierarchyItems(items) {
    const container = $('#hierarchy-items-container');
    
    // Si no hay elementos, mostrar mensaje
    if (!items || items.length === 0) {
        container.html(`
            <div class="text-center py-4">
                <div class="mb-3">
                    <i class="bi bi-diagram-3 text-muted" style="font-size: 3rem;"></i>
                </div>
                <h5>No hay elementos añadidos todavía</h5>
                <p class="text-muted">Comienza añadiendo elementos para la jerarquía.</p>
            </div>
        `);
        return;
    }
    
    // Construir tabla de elementos
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th width="5%">#</th>
                        <th width="65%">Texto</th>
                        <th width="15%">Posición por Defecto</th>
                        <th width="15%" class="text-end">Acciones</th>
                    </tr>
                </thead>
                <tbody id="modal-items-list" class="sortable">
    `;
    
    // Añadir filas para cada elemento
    items.forEach(function(item, index) {
        const helpTextHtml = item.help_text ? `<p class="text-muted small mb-0">${item.help_text}</p>` : '';
        
        tableHtml += `
            <tr id="modal-item-${item.id}" data-id="${item.id}">
                <td class="handle"><i class="bi bi-grip-vertical text-muted"></i> ${index + 1}</td>
                <td>
                    <strong>${item.text}</strong>
                    ${helpTextHtml}
                </td>
                <td>${item.default_position || '-'}</td>
                <td class="text-end">
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary edit-hierarchy-item" 
                                data-item-id="${item.id}">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button type="button" class="btn btn-outline-danger delete-hierarchy-item" 
                                data-item-id="${item.id}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    // Cerrar tabla
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    // Establecer el contenido HTML
    container.html(tableHtml);
    
    // Inicializar funcionalidad de arrastrar y soltar si está disponible
    if (typeof Sortable !== 'undefined') {
        const itemsList = document.getElementById('modal-items-list');
        if (itemsList) {
            new Sortable(itemsList, {
                handle: '.handle',
                animation: 150,
                onEnd: function() {
                    // Actualizar el orden después de arrastrar
                    updateModalItemOrder();
                }
            });
        }
    }
    
    // Configurar los botones de edición y eliminación
    setupModalItemButtons();
}

/**
 * Configura los botones de acciones para los elementos en el modal
 */
function setupModalItemButtons() {
    // Manejador para botones de editar
    $(document).on('click', '.edit-hierarchy-item', function() {
        const itemId = $(this).data('item-id');
        editHierarchyItem(itemId);
    });
    
    // Manejador para botones de eliminar
    $(document).on('click', '.delete-hierarchy-item', function() {
        const itemId = $(this).data('item-id');
        deleteHierarchyItem(itemId);
    });
}

/**
 * Actualiza el orden de los elementos después de una operación de arrastrar y soltar
 */
function updateModalItemOrder() {
    const questionId = $('#hierarchyItemsModal').data('question-id');
    const orderData = [];
    
    // Recopilar los nuevos datos de orden
    $('#modal-items-list tr').each(function(index) {
        const itemId = $(this).data('id');
        orderData.push({
            id: itemId,
            order: index + 1 // El orden comienza en 1
        });
        
        // Actualizar el número de orden visible en la tabla
        $(this).find('td:first-child').html('<i class="bi bi-grip-vertical text-muted"></i> ' + (index + 1));
    });
    
    // Construir la URL para actualizar el orden
    const url = SURVEY_URLS.reorderHierarchyItems.replace('{questionId}', questionId);
    
    // Obtener token CSRF de las cookies
    const csrfToken = getCsrfToken();
    
    // Enviar los datos de orden al servidor mediante AJAX
    $.ajax({
        url: url,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(orderData),
        headers: {
            'X-CSRFToken': csrfToken
        },
        success: function(response) {
            if (response.success) {
                // Actualizar el contador en la vista principal
                updateHierarchyItemCount(questionId);
                
                // Mostrar notificación de éxito
                showNotification('Orden de elementos actualizado', 'success');
            } else {
                // Mostrar notificación de error
                showNotification(response.message || 'Error al actualizar el orden', 'danger');
            }
        },
        error: function() {
            // Mostrar notificación de error
            showNotification('Error al actualizar el orden', 'danger');
        }
    });
}

/**
 * Obtiene el token CSRF de las cookies
 * @returns {string} El token CSRF
 */
function getCsrfToken() {
    let csrfToken = null;
    
    // Buscar la cookie con el token CSRF
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            csrfToken = cookie.substring('csrftoken='.length);
            break;
        }
    }
    
    return csrfToken;
}

/**
 * Edita un elemento de jerarquía existente
 * @param {number} itemId - ID del elemento
 */
function editHierarchyItem(itemId) {
    // Implementar lógica para editar un elemento
    // Se recomienda abrir un formulario modal
    
    // Ejemplo básico:
    const url = SURVEY_URLS.updateHierarchyItem.replace('{itemId}', itemId);
    
    // Mostrar un formulario modal para editar el elemento
    // Esta función dependerá de tu implementación específica
    showEditHierarchyItemForm(url);
}

/**
 * Elimina un elemento de jerarquía
 * @param {number} itemId - ID del elemento
 */
function deleteHierarchyItem(itemId) {
    if (!confirm('¿Estás seguro de que deseas eliminar este elemento?')) {
        return;
    }
    
    const questionId = $('#hierarchyItemsModal').data('question-id');
    const url = SURVEY_URLS.deleteHierarchyItem.replace('{itemId}', itemId);
    const csrfToken = getCsrfToken();
    
    $.ajax({
        url: url,
        type: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            if (response.success) {
                // Eliminar la fila de la tabla
                $(`#modal-item-${itemId}`).remove();
                
                // Actualizar el contador en la vista principal
                updateHierarchyItemCount(questionId);
                
                // Mostrar notificación de éxito
                showNotification('Elemento eliminado correctamente', 'success');
                
                // Si no quedan elementos, actualizar la vista
                if ($('#modal-items-list tr').length === 0) {
                    renderHierarchyItems([]);
                } else {
                    // Actualizar el orden de los elementos restantes
                    updateModalItemOrder();
                }
            } else {
                // Mostrar notificación de error
                showNotification(response.message || 'Error al eliminar el elemento', 'danger');
            }
        },
        error: function() {
            // Mostrar notificación de error
            showNotification('Error al eliminar el elemento', 'danger');
        }
    });
}

/**
 * Añade un nuevo elemento de jerarquía
 * @param {number} questionId - ID de la pregunta
 */
function addNewHierarchyItem(questionId) {
    // Implementar lógica para añadir un nuevo elemento
    // Se recomienda abrir un formulario modal
    
    // Ejemplo básico:
    const url = SURVEY_URLS.getHierarchyItems.replace('{questionId}', questionId) + 'create/';
    
    // Mostrar un formulario modal para añadir el elemento
    // Esta función dependerá de tu implementación específica
    showAddHierarchyItemForm(url);
}

/**
 * Muestra un mensaje de notificación temporal
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo de mensaje (success, danger, warning, info)
 */
function showNotification(message, type = 'info') {
    // Crear contenedor de notificaciones si no existe
    let notificationContainer = $('#notification-container');
    
    if (notificationContainer.length === 0) {
        $('body').append('<div id="notification-container" style="position:fixed; top:20px; right:20px; z-index:9999;"></div>');
        notificationContainer = $('#notification-container');
    }
    
    // Crear elemento de notificación con Bootstrap Alert
    const notification = $(`
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `);
    
    // Añadir al contenedor
    notificationContainer.append(notification);
    
    // Cerrar automáticamente después de 5 segundos
    setTimeout(function() {
        notification.alert('close');
    }, 5000);
}

/**
 * Muestra un formulario modal para añadir un nuevo elemento de jerarquía
 * @param {string} url - URL para cargar el formulario
 */
function showAddHierarchyItemForm(url) {
    // Crear/obtener modal para el formulario
    let formModal = $('#hierarchyItemFormModal');
    if (formModal.length === 0) {
        $('body').append(`
            <div class="modal fade" id="hierarchyItemFormModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Añadir Elemento de Jerarquía</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div id="hierarchy-item-form-container">
                                <!-- Form will be loaded here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
        formModal = $('#hierarchyItemFormModal');
    }
    
    // Actualizar título del modal
    formModal.find('.modal-title').text('Añadir Elemento de Jerarquía');
    
    // Mostrar indicador de carga
    $('#hierarchy-item-form-container').html('<div class="text-center py-4"><div class="spinner-border" role="status"></div></div>');
    
    // Cargar el formulario mediante AJAX
    $.ajax({
        url: url,
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            // Establecer el contenido del formulario
            $('#hierarchy-item-form-container').html(response);
            
            // Configurar el manejo del formulario
            setupHierarchyItemForm();
            
            // Mostrar el modal
            formModal.modal('show');
        },
        error: function() {
            // Mostrar mensaje de error
            $('#hierarchy-item-form-container').html('<div class="alert alert-danger">Error al cargar el formulario</div>');
            formModal.modal('show');
        }
    });
}

/**
 * Muestra un formulario modal para editar un elemento de jerarquía existente
 * @param {string} url - URL para cargar el formulario de edición
 */
function showEditHierarchyItemForm(url) {
    // Crear/obtener modal para el formulario
    let formModal = $('#hierarchyItemFormModal');
    if (formModal.length === 0) {
        $('body').append(`
            <div class="modal fade" id="hierarchyItemFormModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Editar Elemento de Jerarquía</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div id="hierarchy-item-form-container">
                                <!-- Form will be loaded here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
        formModal = $('#hierarchyItemFormModal');
    }
    
    // Actualizar título del modal
    formModal.find('.modal-title').text('Editar Elemento de Jerarquía');
    
    // Mostrar indicador de carga
    $('#hierarchy-item-form-container').html('<div class="text-center py-4"><div class="spinner-border" role="status"></div></div>');
    
    // Cargar el formulario mediante AJAX
    $.ajax({
        url: url,
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            // Establecer el contenido del formulario
            $('#hierarchy-item-form-container').html(response);
            
            // Configurar el manejo del formulario
            setupHierarchyItemForm();
            
            // Mostrar el modal
            formModal.modal('show');
        },
        error: function() {
            // Mostrar mensaje de error
            $('#hierarchy-item-form-container').html('<div class="alert alert-danger">Error al cargar el formulario</div>');
            formModal.modal('show');
        }
    });
}

/**
 * Configura el manejo de envío del formulario de elemento de jerarquía
 */
function setupHierarchyItemForm() {
    const form = $('#hierarchy-item-form-container form');
    if (!form.length) return;
    
    const questionId = $('#hierarchyItemsModal').data('question-id');
    const csrfToken = getCsrfToken();
    
    form.on('submit', function(e) {
        e.preventDefault();
        
        // Recopilar datos del formulario
        const formData = new FormData(this);
        
        // Enviar formulario mediante AJAX
        $.ajax({
            url: form.attr('action'),
            type: form.attr('method') || 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                if (response.success) {
                    // Cerrar el modal del formulario
                    $('#hierarchyItemFormModal').modal('hide');
                    
                    // Recargar los elementos de jerarquía en el modal principal
                    refreshHierarchyItems(questionId);
                    
                    // Mostrar notificación de éxito
                    showNotification(response.message || 'Elemento guardado correctamente', 'success');
                } else {
                    // Mostrar errores en el formulario
                    showFormErrors(form, response);
                }
            },
            error: function(xhr) {
                try {
                    // Intentar analizar la respuesta como JSON
                    const response = JSON.parse(xhr.responseText);
                    showFormErrors(form, response);
                } catch (e) {
                    // Si no es JSON válido, mostrar error genérico
                    form.prepend(`
                        <div class="alert alert-danger alert-dismissible fade show" role="alert">
                            Error al procesar el formulario. Por favor, inténtelo de nuevo.
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    `);
                }
            }
        });
    });
}

/**
 * Muestra errores de validación del formulario
 * @param {Object} form - Elemento jQuery del formulario
 * @param {Object} response - Datos de respuesta con errores
 */
function showFormErrors(form, response) {
    // Limpiar errores previos
    form.find('.is-invalid').removeClass('is-invalid');
    form.find('.invalid-feedback').remove();
    form.find('.alert-danger').remove();
    
    // Añadir mensaje de error general en la parte superior si existe
    if (response.message) {
        form.prepend(`
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${response.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `);
    }
    
    // Añadir errores específicos para cada campo
    if (response.errors) {
        for (const field in response.errors) {
            const input = form.find(`[name="${field}"]`);
            if (input.length) {
                // Marcar el campo como inválido
                input.addClass('is-invalid');
                
                // Añadir mensaje de error
                const errorMessages = Array.isArray(response.errors[field]) 
                    ? response.errors[field].join(' ') 
                    : response.errors[field];
                    
                input.after(`<div class="invalid-feedback">${errorMessages}</div>`);
            }
        }
    }
}

/**
 * Recarga los elementos de jerarquía en el modal principal
 * @param {number} questionId - ID de la pregunta
 */
function refreshHierarchyItems(questionId) {
    // Construir la URL para obtener los elementos de jerarquía
    const url = SURVEY_URLS.getHierarchyItems.replace('{questionId}', questionId);
    
    // Mostrar indicador de carga
    $('#hierarchy-items-container').html('<div class="text-center py-4"><div class="spinner-border" role="status"></div></div>');
    
    // Cargar los elementos de jerarquía mediante AJAX
    $.ajax({
        url: url,
        type: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(response) {
            // Renderizar los elementos en el contenedor
            renderHierarchyItems(response.items);
            
            // Actualizar el contador en la vista principal
            updateHierarchyItemCount(questionId);
        },
        error: function() {
            // Mostrar mensaje de error
            $('#hierarchy-items-container').html('<div class="alert alert-danger">Error al cargar los elementos</div>');
        }
    });
}