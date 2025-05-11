/**
 * question_choices.js - JavaScript for managing question choices
 */
$(document).ready(function() {
    // Setup button handlers
    setupChoiceButtons();
    
    // Initialize sortable list
    initSortableChoices();
});

/**
 * Set up button event handlers for choices
 */
function setupChoiceButtons() {
    // Add choice button
    $('.AddChoiceBtn').click(function() {
        const btn = $(this)[0];
        loadModalAndHandleForm(btn, CHOICE_URLS.add);
    });
    
    // Edit choice button
    $(document).on('click', '.EditChoiceBtn', function() {
        const btn = $(this);
        const choiceId = btn.data('id');
        const url = `/choices/${choiceId}/edit/`;
        loadModal(btn, url);
    });
    
    // Delete choice button
    $(document).on('click', '.DeleteChoiceBtn', function() {
        const btn = $(this);
        const choiceId = btn.data('id');
        const url = `/choices/${choiceId}/delete/`;
        
        // Confirm deletion
        if (confirm(gettext('Are you sure you want to delete this choice?'))) {
            // Send delete request
            $.ajax({
                url: url,
                type: 'POST',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                success: function(response) {
                    if (response.success) {
                        // Remove the row
                        $(`#choice-${choiceId}`).fadeOut(300, function() {
                            $(this).remove();
                            
                            // Check if there are choices left
                            if ($('#choices-list tr').length === 0) {
                                // Reload the page to show the empty state
                                window.location.reload();
                            } else {
                                // Update order
                                updateChoiceOrder();
                            }
                        });
                        
                        // Show success message
                        showNotification(response.message, 'success');
                    } else {
                        showNotification(response.message || gettext('Error deleting choice'), 'danger');
                    }
                },
                error: function() {
                    showNotification(gettext('Error deleting choice'), 'danger');
                }
            });
        }
    });
}

/**
 * Initialize sortable functionality for choices list
 */
function initSortableChoices() {
    const choicesList = document.getElementById('choices-list');
    
    if (choicesList && typeof Sortable !== 'undefined') {
        new Sortable(choicesList, {
            handle: 'td:first-child',
            animation: 150,
            onEnd: function() {
                updateChoiceOrder();
            }
        });
    }
}

/**
 * Update choice order after drag and drop
 */
function updateChoiceOrder() {
    const orderData = [];
    
    // Collect new order data
    $('#choices-list tr').each(function(index) {
        const choiceId = $(this).data('id');
        orderData.push({
            id: choiceId,
            order: index + 1
        });
        
        // Update visible order
        $(this).find('td:first-child').text(index + 1);
        $(this).find('td:nth-child(4)').text(index + 1);
    });
    
    // Send order data to server
    $.ajax({
        url: CHOICE_URLS.reorder,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(orderData),
        headers: {
            'X-CSRFToken': CSRF_TOKEN
        },
        success: function(response) {
            if (response.success) {
                showNotification(gettext('Choice order updated'), 'success');
            } else {
                showNotification(response.message || gettext('Error updating choice order'), 'danger');
            }
        },
        error: function() {
            showNotification(gettext('Error updating choice order'), 'danger');
        }
    });
}

/**
 * Set up form submission handling in modal
 * @param {Object} modalContainer - Modal container jQuery element
 */
function setupModalForm(modalContainer) {
    const form = modalContainer.find('form');
    
    if (form.length) {
        form.on('submit', function(e) {
            e.preventDefault();
            
            // Show loading spinner
            showLoadingOverlay(true);
            
            // Collect form data
            const formData = new FormData(this);
            
            // Submit form via AJAX
            $.ajax({
                url: form.attr('action'),
                type: form.attr('method') || 'POST',
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': CSRF_TOKEN
                },
                success: function(response) {
                    // Hide loading spinner
                    showLoadingOverlay(false);
                    
                    if (response.success) {
                        // Close the modal
                        const modalEl = document.getElementById('dynamicModal');
                        const modalInstance = bootstrap.Modal.getInstance(modalEl);
                        modalInstance.hide();
                        
                        // Show success message
                        showNotification(response.message, 'success');
                        
                        // Update the choices list
                        updateChoicesList(response);
                    } else {
                        // Show form errors
                        showFormErrors(form, response);
                    }
                },
                error: function(xhr) {
                    // Hide loading spinner
                    showLoadingOverlay(false);
                    
                    try {
                        // Try to parse response as JSON
                        const response = JSON.parse(xhr.responseText);
                        showFormErrors(form, response);
                    } catch (e) {
                        // Show generic error
                        showNotification(gettext('Error processing form. Please try again.'), 'danger');
                    }
                }
            });
        });
    }
}

/**
 * Update the choices list after adding or editing a choice
 * @param {Object} response - Response data with choice info
 */
function updateChoicesList(response) {
    const choiceId = response.id;
    const choiceText = response.text;
    const choiceValue = response.value;
    const choiceOrder = response.order;
    
    // Check if we're editing an existing choice
    const existingRow = $(`#choice-${choiceId}`);
    
    if (existingRow.length) {
        // Update existing row
        existingRow.find('td:nth-child(2)').text(choiceText);
        existingRow.find('td:nth-child(3)').text(choiceValue);
        existingRow.find('td:nth-child(4)').text(choiceOrder);
    } else {
        // Add new row
        const newRow = `
            <tr id="choice-${choiceId}" data-id="${choiceId}">
                <td>${choiceOrder}</td>
                <td>${choiceText}</td>
                <td>${choiceValue}</td>
                <td>${choiceOrder}</td>
                <td class="text-end">
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary EditChoiceBtn" 
                                data-id="${choiceId}">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button type="button" class="btn btn-outline-danger DeleteChoiceBtn" 
                                data-id="${choiceId}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        
        // Check if we need to add the first row
        if ($('#choices-list').length === 0) {
            // Reload the page to show the table
            window.location.reload();
        } else {
            // Append to the existing table
            $('#choices-list').append(newRow);
        }
    }
    
    // Update order
    updateChoiceOrder();
}

/**
 * Show form validation errors
 * @param {Object} form - Form jQuery element
 * @param {Object} response - Response data with errors
 */
function showFormErrors(form, response) {
    // Clear any previous errors
    form.find('.is-invalid').removeClass('is-invalid');
    form.find('.invalid-feedback').remove();
    form.find('.alert-danger').remove();
    
    // Add error message at the top if provided
    if (response.message) {
        form.prepend(`
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${response.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `);
    }
    
    // Add field-specific errors
    if (response.errors) {
        for (const field in response.errors) {
            const input = form.find(`[name="${field}"]`);
            if (input.length) {
                input.addClass('is-invalid');
                
                // Add error message
                const errorMessages = Array.isArray(response.errors[field]) 
                    ? response.errors[field].join(' ') 
                    : response.errors[field];
                    
                input.after(`<div class="invalid-feedback">${errorMessages}</div>`);
            }
        }
    }
}

/**
 * Show/hide loading overlay
 * @param {boolean} show - Whether to show or hide the overlay
 */
function showLoadingOverlay(show) {
    let overlay = $('#loadingOverlay');
    
    if (overlay.length === 0) {
        $('body').append(`
            <div id="loadingOverlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; 
                background:rgba(0,0,0,0.3); z-index:9999; justify-content:center; align-items:center;">
                <div class="spinner-border text-light" role="status">
                    <span class="visually-hidden">${gettext('Loading...')}</span>
                </div>
            </div>
        `);
        overlay = $('#loadingOverlay');
    }
    
    if (show) {
        overlay.css('display', 'flex');
    } else {
        overlay.css('display', 'none');
    }
}

/**
 * Show notification message
 * @param {string} message - Message to display
 * @param {string} type - Message type (success, danger, warning, info)
 */
function showNotification(message, type = 'info') {
    // Create notification container if it doesn't exist
    let notificationContainer = $('#notification-container');
    
    if (notificationContainer.length === 0) {
        $('body').append('<div id="notification-container" style="position:fixed; top:20px; right:20px; z-index:9999;"></div>');
        notificationContainer = $('#notification-container');
    }
    
    // Create notification element
    const notification = $(`
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `);
    
    // Add to container
    notificationContainer.append(notification);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        notification.alert('close');
    }, 5000);
}

/**
 * Get translation for a string
 * @param {string} text - Text to translate
 * @returns {string} Translated text
 */
function gettext(text) {
    // This is a simple placeholder. In a real app, you'd integrate with Django's gettext
    return text;
}