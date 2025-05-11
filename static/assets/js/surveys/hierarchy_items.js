// Cuando el documento HTML está completamente cargado, inicializamos los componentes
$(document).ready(function() {
    // Obtener el token CSRF desde una cookie para usar en peticiones AJAX
    const CSRF_TOKEN = getCsrfToken();
    
    // Configurar los manejadores de eventos para los botones
    setupItemButtons();
    
    // Inicializar la funcionalidad de arrastrar y soltar para reordenar elementos
    initSortableItems();
});

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
 * Obtiene el ID de la pregunta actual desde la URL
 * @returns {number} El ID de la pregunta
 */
function getCurrentQuestionId() {
    // Intentar obtener el ID desde la URL utilizando una expresión regular
    const urlPattern = /\/questions\/(\d+)/;
    const matches = window.location.pathname.match(urlPattern);
    
    if (matches && matches.length > 1) {
        return matches[1];
    }
    
    // Si no se encuentra en la URL, verificar si está disponible como variable global (definida en la plantilla)
    if (typeof questionId !== 'undefined') {
        return questionId;
    }
    
    // Como último recurso, extraer de los datos del formulario o de otro elemento
    const questionIdFromDOM = $('[data-question-id]').first().data('question-id');
    if (questionIdFromDOM) {
        return questionIdFromDOM;
    }
    
    console.error('No se pudo determinar el ID de la pregunta');
    return null;
}

/**
 * Configura los manejadores de eventos para los botones de elementos jerárquicos
 */
function setupItemButtons() {
    // Manejador para el botón de añadir elemento
    $('.addItemBtn').click(function() {
        const btn = $(this)[0];
        // Utilizamos la función para cargar el formulario en un modal
        loadModalAndHandleForm(btn, ITEM_URLS.create);
    });
    
    // Manejador para botones de editar
    $(document).on('click', '.edit-item', function() {
        const btn = $(this)[0];
        const itemId = $(this).data('item-id');
        const questionId = getCurrentQuestionId();
        const updateUrl = ITEM_URLS.update(questionId, itemId);
        loadModalAndHandleForm(btn, updateUrl);
    });
    
    // Manejador para botones de eliminar
    $(document).on('click', '.delete-item', function() {
        const btn = $(this)[0];
        const itemId = $(this).data('item-id');
        const questionId = getCurrentQuestionId();
        const deleteUrl = ITEM_URLS.delete(questionId, itemId);
        loadModalAndHandleForm(btn, deleteUrl);                  
    });
}

/**
 * Inicializa la funcionalidad de arrastrar y soltar para la lista de elementos
 */
function initSortableItems() {
    const itemsList = document.getElementById('items-list');
    
    // Verificar que existe la lista y que la biblioteca Sortable está disponible
    if (itemsList && typeof Sortable !== 'undefined') {
        // Crear una instancia de Sortable para la lista
        new Sortable(itemsList, {
            handle: '.handle', // El elemento que sirve como "manija" para arrastrar
            animation: 150,    // Duración de la animación en milisegundos
            onEnd: function() {
                // Cuando termina una operación de arrastre, actualizamos el orden
                updateItemOrder();
            }
        });
    }
}
/*
 * Actualiza el orden de los elementos después de una operación de arrastrar y soltar
 */
function updateItemOrder() {
    const orderData = [];
    const CSRF_TOKEN = getCsrfToken();
    
    // Recopilar los nuevos datos de orden
    $('#items-list tr').each(function(index) {
        const itemId = $(this).data('id');
        orderData.push({
            id: itemId,
            order: index + 1 // El orden comienza en 1
        });
        
        // Actualizar el número de orden visible en la tabla
        $(this).find('td:first-child').html('<i class="bi bi-grip-vertical text-muted"></i> ' + (index + 1));
    });
    
    // Enviar los datos de orden al servidor mediante AJAX
    $.ajax({
        url: ITEM_URLS.reorder,
        type: 'POST',
        contentType: 'application/json', // Indicamos que enviamos JSON
        data: JSON.stringify(orderData), // Convertimos el array a JSON
        headers: {
            'X-CSRFToken': CSRF_TOKEN // Token CSRF para seguridad
        },
        success: function(response) {
            if (response.success) {
                // Mostrar mensaje de éxito
                showNotification(gettext('Orden de elementos actualizado'), 'success');
            } else {
                // Mostrar mensaje de error
                showNotification(response.message || gettext('Error al actualizar el orden de elementos'), 'danger');
            }
        },
        error: function() {
            // Mostrar mensaje de error en caso de fallo en la comunicación
            showNotification(gettext('Error al actualizar el orden de elementos'), 'danger');
        }
    });
}
// /**
//  * Obtiene la traducción de un texto
//  * 
//  * @param {string} text - Texto a traducir
//  * @returns {string} Texto traducido
//  */
// function gettext(text) {
//     // Este es un marcador de posición simple. En una aplicación real, 
//     // se integraría con Django gettext
//     return text;
// }