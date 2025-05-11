/**
 * hierarchy_items.js - JavaScript para gestionar elementos jerárquicos
 * 
 * Este archivo contiene todas las funciones necesarias para administrar elementos 
 * jerárquicos en una interfaz web, incluyendo la creación, edición, eliminación 
 * y reordenamiento de elementos mediante arrastrar y soltar.
 */

// Cuando el documento HTML está completamente cargado, inicializamos los componentes
$(document).ready(function() {
    // Configurar los manejadores de eventos para los botones
    setupItemButtons();
    
    // Inicializar la funcionalidad de arrastrar y soltar para reordenar elementos
    initSortableItems();
});

/**
 * Configura los manejadores de eventos para los botones de elementos jerárquicos
 * 
 * Esta función establece tres tipos principales de eventos:
 * 1. Botón para añadir nuevos elementos
 * 2. Botones para editar elementos existentes (usando delegación de eventos)
 * 3. Botones para eliminar elementos (usando delegación de eventos)
 */
function setupItemButtons() {
    // Manejador para el botón de añadir elemento
    // Carga un formulario modal para crear un nuevo elemento
    $('.addItemBtn').click(function() {
        const btn = $(this)[0];
        // Utilizamos la función para cargar el formulario en un modal
        loadModalAndHandleForm(btn, ITEM_URLS.create);
    });
    
    // Manejador para botones de editar (usando delegación de eventos para capturar elementos creados dinámicamente)
    // Cuando se hace clic en un botón de edición, carga un formulario modal con los datos del elemento existente
     $(document).on('click', '.edit-item', function() {
        const btn = $(this)[0];
        const itemId = $(this).data('item-id'); // Asegúrate de que cada botón tenga este atributo
        const updateUrl = getItemUpdateUrl(itemId);
        loadModalAndHandleForm(btn, updateUrl);
    });
    
    // Manejador para botones de eliminar (usando delegación de eventos)
    // Muestra un diálogo de confirmación y elimina el elemento si se confirma
    $(document).on('click', '.delete-item', function() {
        const btn = $(this)[0];
        const itemId = $(this).data('item-id'); // Asegúrate de que cada botón tenga este atributo
        const deleteUrl = getItemDeleteUrl(itemId);
        loadModalAndHandleForm(btn, deleteUrl);                  
    });
}
function getItemUpdateUrl(itemId) {
    return `/questions/{{ question.id }}/hierarchy-items/${itemId}/update/`;
}

function getItemDeleteUrl(itemId) {
    return `/questions/{{ question.id }}/hierarchy-items/${itemId}/delete/`;
}
// /**
//  * Inicializa la funcionalidad de arrastrar y soltar para la lista de elementos
//  * 
//  * Utiliza la biblioteca Sortable.js para permitir que los usuarios reordenen 
//  * los elementos de la lista arrastrándolos y soltándolos.
//  */
// function initSortableItems() {
//     const itemsList = document.getElementById('items-list');
    
//     // Verificar que existe la lista y que la biblioteca Sortable está disponible
//     if (itemsList && typeof Sortable !== 'undefined') {
//         // Crear una instancia de Sortable para la lista
//         new Sortable(itemsList, {
//             handle: '.handle', // El elemento que sirve como "manija" para arrastrar
//             animation: 150,    // Duración de la animación en milisegundos
//             onEnd: function() {
//                 // Cuando termina una operación de arrastre, actualizamos el orden
//                 updateItemOrder();
//             }
//         });
//     }
// }

// /**
//  * Actualiza el orden de los elementos después de una operación de arrastrar y soltar
//  * 
//  * Esta función:
//  * 1. Recopila los nuevos datos de orden de todos los elementos
//  * 2. Actualiza visualmente los números de orden en la tabla
//  * 3. Envía los datos actualizados al servidor
//  */
// function updateItemOrder() {
//     const orderData = [];
    
//     // Recopilar los nuevos datos de orden
//     $('#items-list tr').each(function(index) {
//         const itemId = $(this).data('id');
//         orderData.push({
//             id: itemId,
//             order: index + 1 // El orden comienza en 1
//         });
        
//         // Actualizar el número de orden visible en la tabla
//         $(this).find('td:first-child').html('<i class="bi bi-grip-vertical text-muted"></i> ' + (index + 1));
//     });
    
//     // Enviar los datos de orden al servidor mediante AJAX
//     $.ajax({
//         url: ITEM_URLS.reorder,
//         type: 'POST',
//         contentType: 'application/json', // Indicamos que enviamos JSON
//         data: JSON.stringify(orderData), // Convertimos el array a JSON
//         headers: {
//             'X-CSRFToken': CSRF_TOKEN // Token CSRF para seguridad
//         },
//         success: function(response) {
//             if (response.success) {
//                 // Mostrar mensaje de éxito
//                 showNotification(gettext('Orden de elementos actualizado'), 'success');
//             } else {
//                 // Mostrar mensaje de error
//                 showNotification(response.message || gettext('Error al actualizar el orden de elementos'), 'danger');
//             }
//         },
//         error: function() {
//             // Mostrar mensaje de error en caso de fallo en la comunicación
//             showNotification(gettext('Error al actualizar el orden de elementos'), 'danger');
//         }
//     });
// }

// /**
//  * Carga un formulario en un modal
//  * 
//  * @param {Object} button - Elemento botón que desencadenó la acción
//  * @param {string} url - URL para cargar el contenido del modal
//  */
// function loadModal(button, url) {
//     // Mostrar indicador de carga
//     showLoadingOverlay(true);
    
//     // Solicitar el contenido del formulario mediante AJAX
//     $.ajax({
//         url: url,
//         type: 'GET',
//         headers: {
//             'X-Requested-With': 'XMLHttpRequest' // Indica que es una solicitud AJAX
//         },
//         success: function(response) {
//             // Ocultar indicador de carga
//             showLoadingOverlay(false);
            
//             // Crear el modal si no existe
//             let modalContainer = $('#dynamicModal');
//             if (modalContainer.length === 0) {
//                 $('body').append(`
//                     <div class="modal fade" id="dynamicModal" tabindex="-1" aria-hidden="true">
//                         <div class="modal-dialog modal-lg">
//                             <div class="modal-content">
//                                 <!-- El contenido se cargará aquí -->
//                             </div>
//                         </div>
//                     </div>
//                 `);
//                 modalContainer = $('#dynamicModal');
//             }
            
//             // Establecer el contenido del modal
//             modalContainer.find('.modal-content').html(response);
            
//             // Configurar el formulario dentro del modal
//             setupModalForm(modalContainer);
            
//             // Mostrar el modal
//             const modalEl = document.getElementById('dynamicModal');
//             const modal = new bootstrap.Modal(modalEl);
//             modal.show();
//         },
//         error: function() {
//             // Ocultar indicador de carga
//             showLoadingOverlay(false);
            
//             // Mostrar mensaje de error
//             showNotification(gettext('Error al cargar el formulario'), 'danger');
//         }
//     });
// }

// /**
//  * Carga un modal y configura el formulario
//  * 
//  * Esta función es un wrapper de loadModal para mantener la consistencia
//  * en la API, permitiendo potenciales extensiones futuras.
//  * 
//  * @param {Object} button - Elemento botón que desencadenó la acción
//  * @param {string} url - URL para cargar el contenido del modal
//  */
// function loadModalAndHandleForm(button, url) {
//     loadModal(button, url);
// }

// /**
//  * Configura el manejo de envío de formularios en un modal
//  * 
//  * Esta función:
//  * 1. Previene el envío normal del formulario
//  * 2. Recoge los datos del formulario
//  * 3. Envía los datos mediante AJAX
//  * 4. Maneja la respuesta (éxito o errores)
//  * 
//  * @param {Object} modalContainer - Elemento jQuery del contenedor del modal
//  */
// function setupModalForm(modalContainer) {
//     const form = modalContainer.find('form');
    
//     if (form.length) {
//         form.on('submit', function(e) {
//             e.preventDefault(); // Prevenir el envío normal del formulario
            
//             // Mostrar indicador de carga
//             showLoadingOverlay(true);
            
//             // Recopilar datos del formulario (incluidos archivos si los hay)
//             const formData = new FormData(this);
            
//             // Enviar formulario mediante AJAX
//             $.ajax({
//                 url: form.attr('action'),
//                 type: form.attr('method') || 'POST',
//                 data: formData,
//                 processData: false, // No procesar los datos (necesario para FormData)
//                 contentType: false, // No establecer contentType (necesario para FormData)
//                 headers: {
//                     'X-Requested-With': 'XMLHttpRequest', // Indica que es una solicitud AJAX
//                     'X-CSRFToken': CSRF_TOKEN // Token CSRF para seguridad
//                 },
//                 success: function(response) {
//                     // Ocultar indicador de carga
//                     showLoadingOverlay(false);
                    
//                     if (response.success) {
//                         // Si la operación fue exitosa, cerrar el modal
//                         const modalEl = document.getElementById('dynamicModal');
//                         const modalInstance = bootstrap.Modal.getInstance(modalEl);
//                         modalInstance.hide();
                        
//                         // Mostrar mensaje de éxito
//                         showNotification(response.message, 'success');
                        
//                         // Actualizar la lista de elementos
//                         updateItemsList(response);
//                     } else {
//                         // Si hay errores, mostrarlos en el formulario
//                         showFormErrors(form, response);
//                     }
//                 },
//                 error: function(xhr) {
//                     // Ocultar indicador de carga
//                     showLoadingOverlay(false);
                    
//                     try {
//                         // Intentar analizar la respuesta como JSON
//                         const response = JSON.parse(xhr.responseText);
//                         showFormErrors(form, response);
//                     } catch (e) {
//                         // Si no es JSON válido, mostrar error genérico
//                         showNotification(gettext('Error al procesar el formulario. Por favor, inténtelo de nuevo.'), 'danger');
//                     }
//                 }
//             });
//         });
//     }
// }

// /**
//  * Actualiza la lista de elementos después de añadir o editar un elemento
//  * 
//  * Esta función:
//  * 1. Identifica si es una edición o una creación
//  * 2. Actualiza la fila existente o añade una nueva
//  * 3. Actualiza el orden de los elementos
//  * 
//  * @param {Object} response - Datos de respuesta con información del elemento
//  */
// function updateItemsList(response) {
//     const itemId = response.id;
//     const itemText = response.text;
//     const helpText = response.help_text || '';
//     const defaultPosition = response.default_position;
//     const order = response.order;
    
//     // Verificar si estamos editando un elemento existente
//     const existingRow = $(`#item-${itemId}`);
    
//     if (existingRow.length) {
//         // Si el elemento ya existe, actualizar la fila existente
//         const helpTextHtml = helpText ? `<p class="text-muted small mb-0">${helpText}</p>` : '';
        
//         existingRow.find('td:nth-child(2)').html(`
//             <strong>${itemText}</strong>
//             ${helpTextHtml}
//         `);
//         existingRow.find('td:nth-child(3)').text(defaultPosition);
//     } else {
//         // Si es un nuevo elemento, añadir una nueva fila
//         const helpTextHtml = helpText ? `<p class="text-muted small mb-0">${helpText}</p>` : '';
        
//         const newRow = `
//             <tr id="item-${itemId}" data-id="${itemId}">
//                 <td class="handle"><i class="bi bi-grip-vertical text-muted"></i> ${order}</td>
//                 <td>
//                     <strong>${itemText}</strong>
//                     ${helpTextHtml}
//                 </td>
//                 <td>${defaultPosition}</td>
//                 <td class="text-end">
//                     <div class="btn-group btn-group-sm">
//                         <button type="button" class="btn btn-outline-primary edit-item" 
//                                 data-item-id="${itemId}">
//                             <i class="bi bi-pencil"></i>
//                         </button>
//                         <button type="button" class="btn btn-outline-danger delete-item" 
//                                 data-item-id="${itemId}">
//                             <i class="bi bi-trash"></i>
//                         </button>
//                     </div>
//                 </td>
//             </tr>
//         `;
        
//         // Verificar si necesitamos añadir la primera fila (si la tabla aún no existe)
//         if ($('#items-list').length === 0) {
//             // Si no existe la tabla, recargar la página para mostrarla completa
//             window.location.reload();
//         } else {
//             // Si la tabla ya existe, añadir la nueva fila
//             $('#items-list').append(newRow);
//         }
//     }
    
//     // Actualizar el orden de los elementos
//     updateItemOrder();
// }

// /**
//  * Muestra errores de validación del formulario
//  * 
//  * Esta función:
//  * 1. Limpia errores previos
//  * 2. Añade mensaje de error general si existe
//  * 3. Añade mensajes de error específicos junto a cada campo con problemas
//  * 
//  * @param {Object} form - Elemento jQuery del formulario
//  * @param {Object} response - Datos de respuesta con errores
//  */
// function showFormErrors(form, response) {
//     // Limpiar errores previos
//     form.find('.is-invalid').removeClass('is-invalid');
//     form.find('.invalid-feedback').remove();
//     form.find('.alert-danger').remove();
    
//     // Añadir mensaje de error general en la parte superior si existe
//     if (response.message) {
//         form.prepend(`
//             <div class="alert alert-danger alert-dismissible fade show" role="alert">
//                 ${response.message}
//                 <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
//             </div>
//         `);
//     }
    
//     // Añadir errores específicos para cada campo
//     if (response.errors) {
//         for (const field in response.errors) {
//             const input = form.find(`[name="${field}"]`);
//             if (input.length) {
//                 // Marcar el campo como inválido
//                 input.addClass('is-invalid');
                
//                 // Añadir mensaje de error
//                 const errorMessages = Array.isArray(response.errors[field]) 
//                     ? response.errors[field].join(' ') // Si es un array, unir todos los mensajes
//                     : response.errors[field]; // Si no, usar directamente
                    
//                 input.after(`<div class="invalid-feedback">${errorMessages}</div>`);
//             }
//         }
//     }
// }

// /**
//  * Muestra u oculta un indicador de carga superpuesto
//  * 
//  * Esta función crea (si no existe) y muestra/oculta una capa semitransparente
//  * con un indicador de carga centrado que cubre toda la pantalla.
//  * 
//  * @param {boolean} show - Indica si se debe mostrar (true) u ocultar (false) el indicador
//  */
// function showLoadingOverlay(show) {
//     let overlay = $('#loadingOverlay');
    
//     // Crear el overlay si no existe
//     if (overlay.length === 0) {
//         $('body').append(`
//             <div id="loadingOverlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; 
//                 background:rgba(0,0,0,0.3); z-index:9999; justify-content:center; align-items:center;">
//                 <div class="spinner-border text-light" role="status">
//                     <span class="visually-hidden">${gettext('Cargando...')}</span>
//                 </div>
//             </div>
//         `);
//         overlay = $('#loadingOverlay');
//     }
    
//     // Mostrar u ocultar según el parámetro
//     if (show) {
//         overlay.css('display', 'flex'); // Usar flex para centrar el spinner
//     } else {
//         overlay.css('display', 'none');
//     }
// }

// /**
//  * Muestra un mensaje de notificación temporal
//  * 
//  * Esta función crea notificaciones flotantes que se muestran en la esquina
//  * superior derecha y desaparecen automáticamente después de un tiempo.
//  * 
//  * @param {string} message - Mensaje a mostrar
//  * @param {string} type - Tipo de mensaje (success, danger, warning, info)
//  */
// function showNotification(message, type = 'info') {
//     // Crear contenedor de notificaciones si no existe
//     let notificationContainer = $('#notification-container');
    
//     if (notificationContainer.length === 0) {
//         $('body').append('<div id="notification-container" style="position:fixed; top:20px; right:20px; z-index:9999;"></div>');
//         notificationContainer = $('#notification-container');
//     }
    
//     // Crear elemento de notificación con Bootstrap Alert
//     const notification = $(`
//         <div class="alert alert-${type} alert-dismissible fade show" role="alert">
//             ${message}
//             <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
//         </div>
//     `);
    
//     // Añadir al contenedor
//     notificationContainer.append(notification);
    
//     // Cerrar automáticamente después de 5 segundos
//     setTimeout(function() {
//         notification.alert('close');
//     }, 5000);
// }

// /**
//  * Obtiene la traducción de un texto
//  * 
//  * Esta es una función simplificada para traducción. En una aplicación real,
//  * se integraría con el sistema de internacionalización de Django.
//  * 
//  * @param {string} text - Texto a traducir
//  * @returns {string} Texto traducido
//  */
// function gettext(text) {
//     // Este es un marcador de posición simple. En una aplicación real, 
//     // se integraría con Django gettext
//     return text;
// }