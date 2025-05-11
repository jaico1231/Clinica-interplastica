/**
 * survey_detail.js - JavaScript for Survey Detail functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips and popovers
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Get survey ID from URL
    const urlParts = window.location.pathname.split('/');
    const surveyId = urlParts[urlParts.indexOf('surveys') + 1];
    
    // Survey main actions
    setupMainActions(surveyId);
    
    // Question actions
    setupQuestionActions(surveyId);
    
    // Make the questions table sortable
    initSortableQuestions();
});

/**
 * Setup survey main action buttons
 * @param {string} surveyId - ID of the current survey
 */
function setupMainActions(surveyId) {
    // Edit Survey Button
    $('.EditSurveyBtn').click(function() {
        const btn = $(this)[0];
        loadModalAndHandleForm(btn, SURVEY_URLS.edit);
    });
    
    // Publish Button
    $('.PublishBtn').click(function() {
        const btn = $(this)[0];
        loadModalAndHandleForm(btn, SURVEY_URLS.publish);
    });
    
    // Unpublish Button
    $('.UnpublishBtn').click(function() {
        const btn = $(this)[0];
        loadModalAndHandleForm(btn, SURVEY_URLS.unpublish);
    });
    
    // Preview Button
    $('.PreviewBtn').click(function() {        
        window.open(SURVEY_URLS.preview, '_blank');
    });
    
    // Responses Button
    $('.ResponsesBtn').click(function() {
        const url = `/surveys/${surveyId}/responses/`;
        location.href = url;
    });
    
    // Export Button
    $('.ExportBtn').click(function() {
        const btn = $(this)[0];
        window.open(SURVEY_URLS.export, '_blank');
    });
    
    // Delete Button
    $('.DelBtn').click(function() {
        const url = `/surveys/${surveyId}/delete/`;
        const btn = $(this)[0];
        loadModalAndHandleForm(btn, url);
    });

    $('.AddQuestionBtn').click(function() {
        const btn = $(this)[0];
        loadModalAndHandleForm(btn, SURVEY_URLS.addQuestion);
    });
    $('.FirstQuestionBtn').click(function() {
        const btn = $(this)[0];
        loadModalAndHandleForm(btn, SURVEY_URLS.addQuestion);
    });
    $('.ViewChoicesBtn').click(function() {
        const questionId = $(this).data('question-id');
        // Construct the URL dynamically
        const url = `/questions/${questionId}/choices/`;
        location.href = url;
    });
}

/**
 * Initialize delete question buttons
 */
function setupDeleteQuestionButtons() {
    // For each button that opens a delete question modal
    $('[data-bs-target^="#deleteQuestionModal-"]').each(function() {
        const modalId = $(this).attr('data-bs-target');
        const questionId = modalId.split('-')[1];
        
        // Add confirm button event listener in the modal
        $(modalId).find('.btn-danger').click(function() {
            const url = `/surveys/questions/${questionId}/delete/`;
            const btn = $(this)[0];
            loadModalAndHandleForm(btn, url);
        });
    });
}

/**
 * Initialize view choices buttons
 */
function setupViewChoicesButtons() {
    $('[data-bs-target^="#choicesModal-"]').click(function(e) {
        e.preventDefault();
        const modalId = $(this).attr('data-bs-target');
        $(modalId).modal('show');
    });
}

/**
 * Load modal content and handle form submission
 * @param {Object} btn - Button element that triggered the action
 * @param {string} url - URL to load in the modal
 */

/**
 * Show validation errors in the modal
 * @param {Object} modalContainer - Modal element
 * @param {Object} response - Response data with errors
 */
function showModalErrors(modalContainer, response) {
    // Clear previous errors
    modalContainer.find('.is-invalid').removeClass('is-invalid');
    modalContainer.find('.invalid-feedback').remove();
    
    // Add new errors
    if (response.errors) {
        for (const field in response.errors) {
            const input = modalContainer.find(`[name="${field}"]`);
            input.addClass('is-invalid');
            
            // Add error message
            const errorMsg = response.errors[field].join(' ');
            input.after(`<div class="invalid-feedback">${errorMsg}</div>`);
        }
    }
    
    // Show general error if any
    if (response.message) {
        const alertDiv = `<div class="alert alert-danger">${response.message}</div>`;
        modalContainer.find('form').prepend(alertDiv);
    }
}

/**
 * Initialize sortable functionality for questions list
 */
function initSortableQuestions() {
    const questionsList = document.getElementById('questions-list');
    
    if (questionsList && typeof Sortable !== 'undefined') {
        new Sortable(questionsList, {
            handle: 'td:first-child',
            animation: 150,
            onEnd: function(evt) {
                updateQuestionOrder();
            }
        });
    }
}

/**
 * Update question order after drag and drop
 */
function updateQuestionOrder() {
    const orderData = [];
    
    $('#questions-list tr').each(function(index) {
        const questionId = $(this).attr('data-id');
        orderData.push({
            id: questionId,
            order: index + 1
        });
        
        // Update visible order number
        $(this).find('td:first-child').text(index + 1);
    });
    
    // Send order data to server
    $.ajax({
        url: '/api/surveys/questions/reorder/',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(orderData),
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        success: function(response) {
            if (response.success) {
                showNotification('Question order updated', 'success');
            } else {
                showNotification('Error updating question order', 'danger');
            }
        },
        error: function() {
            showNotification('Error updating question order', 'danger');
        }
    });
}

/**
 * Show a notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, danger, warning, info)
 */
function showNotification(message, type = 'info') {
    // Check if notification container exists, if not create it
    let notificationContainer = $('#notification-container');
    
    if (notificationContainer.length === 0) {
        $('body').append('<div id="notification-container" style="position: fixed; top: 20px; right: 20px; z-index: 9999;"></div>');
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
 * Get CSRF token from cookies
 * @returns {string} CSRF token
 */
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    return cookieValue;
}