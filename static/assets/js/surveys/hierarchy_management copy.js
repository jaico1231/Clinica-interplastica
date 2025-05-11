/**
 * hierarchy_management.js - JavaScript for handling hierarchy questions in surveys
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the hierarchy management functionality
    initHierarchyManagement();
});

/**
 * Initialize hierarchy management functionality
 */
function initHierarchyManagement() {
    // This will be called if hierarchy items are loaded via AJAX
    document.addEventListener('hierarchyItemsLoaded', function(event) {
        const questionId = event.detail.questionId;
        
        // Initialize drag and drop for hierarchy items
        initHierarchyDragDrop(questionId);
        
        // Set up event handlers for hierarchy actions
        setupHierarchyItemEventHandlers(questionId);
    });
}

/**
 * Initialize drag and drop for hierarchy items
 * @param {string} questionId - ID of the question
 */
function initHierarchyDragDrop(questionId) {
    // Find all hierarchy containers for this question
    const hierarchyContainers = document.querySelectorAll(`.hierarchy-container[data-question-id="${questionId}"] .hierarchy-items`);
    
    hierarchyContainers.forEach(container => {
        new Sortable(container, {
            group: 'hierarchy-items',
            animation: 150,
            handle: '.drag-handle',
            ghostClass: 'hierarchy-item-ghost',
            onEnd: function(evt) {
                // Update the order of items after drag and drop
                updateHierarchyItemsOrder(questionId);
            }
        });
    });
}

/**
 * Update the order of hierarchy items after drag and drop
 * @param {string} questionId - ID of the question
 */
function updateHierarchyItemsOrder(questionId) {
    const container = document.querySelector(`.hierarchy-container[data-question-id="${questionId}"]`);
    const items = container.querySelectorAll('.hierarchy-item');
    
    const orderData = [];
    
    items.forEach((item, index) => {
        const itemId = item.dataset.itemId;
        const parentItem = item.closest('.hierarchy-child-items')?.closest('.hierarchy-item');
        const parentId = parentItem ? parentItem.dataset.itemId : null;
        
        orderData.push({
            id: itemId,
            order: index + 1,
            parent_id: parentId
        });
    });
    
    // Send the order data to the server
    const url = SURVEY_URLS.reorderHierarchyItems.replace('{questionId}', questionId);
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ items: orderData })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Hierarchy item order updated successfully', 'success');
        } else {
            showNotification(data.message || 'Error updating hierarchy item order', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating hierarchy item order', 'danger');
    });
}

/**
 * Set up event handlers for hierarchy item actions
 * @param {string} questionId - ID of the question
 */
function setupHierarchyItemEventHandlers(questionId) {
    const container = document.querySelector(`.hierarchy-container[data-question-id="${questionId}"]`);
    
    // Add item button
    container.querySelector('.add-hierarchy-item').addEventListener('click', function() {
        const url = SURVEY_URLS.addHierarchyItem.replace('{questionId}', questionId);
        openHierarchyItemModal(url, null, questionId);
    });
    
    // Edit item buttons
    container.querySelectorAll('.edit-hierarchy-item').forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.closest('.hierarchy-item').dataset.itemId;
            const url = SURVEY_URLS.updateHierarchyItem.replace('{itemId}', itemId);
            openHierarchyItemModal(url, itemId, questionId);
        });
    });
    
    // Delete item buttons
    container.querySelectorAll('.delete-hierarchy-item').forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.closest('.hierarchy-item').dataset.itemId;
            deleteHierarchyItem(itemId, questionId);
        });
    });
    
    // Add child item buttons
    container.querySelectorAll('.add-child-item').forEach(button => {
        button.addEventListener('click', function() {
            const parentId = this.closest('.hierarchy-item').dataset.itemId;
            const url = `${SURVEY_URLS.addHierarchyItem.replace('{questionId}', questionId)}?parent_id=${parentId}`;
            openHierarchyItemModal(url, null, questionId, parentId);
        });
    });
    
    // Toggle expand/collapse buttons
    container.querySelectorAll('.toggle-children').forEach(button => {
        button.addEventListener('click', function() {
            const item = this.closest('.hierarchy-item');
            const childrenContainer = item.querySelector('.hierarchy-child-items');
            
            if (childrenContainer) {
                const isExpanded = childrenContainer.classList.contains('show');
                
                if (isExpanded) {
                    childrenContainer.classList.remove('show');
                    this.innerHTML = '<i class="bi bi-plus-square"></i>';
                    this.setAttribute('title', 'Expand');
                } else {
                    childrenContainer.classList.add('show');
                    this.innerHTML = '<i class="bi bi-dash-square"></i>';
                    this.setAttribute('title', 'Collapse');
                }
            }
        });
    });
}

/**
 * Open modal for adding or editing a hierarchy item
 * @param {string} url - URL for the modal content
 * @param {string|null} itemId - ID of the item being edited, or null for adding
 * @param {string} questionId - ID of the question
 * @param {string|null} parentId - ID of the parent item, or null for top-level
 */
function openHierarchyItemModal(url, itemId, questionId, parentId = null) {
    // Create modal if it doesn't exist
    let modalId = 'hierarchyItemModal';
    let modalElement = document.getElementById(modalId);
    
    if (!modalElement) {
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <!-- Content will be loaded here -->
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modalElement = document.getElementById(modalId);
    }
    
    // Show loading state
    modalElement.querySelector('.modal-content').innerHTML = `
        <div class="modal-body text-center py-4">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2">Loading...</p>
        </div>
    `;
    
    // Show modal
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    
    // Load modal content
    fetch(url)
        .then(response => response.text())
        .then(html => {
            // Update modal content
            modalElement.querySelector('.modal-content').innerHTML = html;
            
            // Set parent ID if provided
            if (parentId) {
                const parentInput = modalElement.querySelector('input[name="parent_id"]');
                if (parentInput) {
                    parentInput.value = parentId;
                }
            }
            
            // Handle form submission
            const form = modalElement.querySelector('form');
            if (form) {
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const formData = new FormData(form);
                    
                    fetch(form.action, {
                        method: form.method,
                        body: formData,
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Close modal
                                modal.hide();
                                
                                // Show success notification
                                showNotification(data.message || 'Hierarchy item saved successfully', 'success');
                                
                                // Reload hierarchy items
                                loadHierarchyItems(questionId);
                            } else {
                                // Show validation errors
                                showModalErrors($(modalElement), data);
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            showNotification('Error saving hierarchy item', 'danger');
                        });
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            modalElement.querySelector('.modal-content').innerHTML = `
                <div class="modal-body">
                    <div class="alert alert-danger">Error loading content</div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            `;
        });
}

/**
 * Delete a hierarchy item
 * @param {string} itemId - ID of the item to delete
 * @param {string} questionId - ID of the question
 */
function deleteHierarchyItem(itemId, questionId) {
    if (confirm('Are you sure you want to delete this item and all its children? This action cannot be undone.')) {
        const url = SURVEY_URLS.deleteHierarchyItem.replace('{itemId}', itemId);
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success notification
                    showNotification(data.message || 'Hierarchy item deleted successfully', 'success');
                    
                    // Reload hierarchy items
                    loadHierarchyItems(questionId);
                } else {
                    // Show error notification
                    showNotification(data.message || 'Error deleting hierarchy item', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Error deleting hierarchy item', 'danger');
            });
    }
}

/**
 * Update the preview of how the hierarchy question will look to respondents
 * @param {string} questionId - ID of the question
 */
function updateHierarchyPreview(questionId) {
    const container = document.querySelector(`.hierarchy-container[data-question-id="${questionId}"]`);
    const previewContainer = container.querySelector('.hierarchy-preview');
    
    if (!previewContainer) {
        return;
    }
    
    // Show loading state
    previewContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2">Loading preview...</p>
        </div>
    `;
    
    // Load preview
    const url = `/questions/${questionId}/hierarchy-preview/`;
    
    fetch(url)
        .then(response => response.text())
        .then(html => {
            previewContainer.innerHTML = html;
            
            // Initialize sortable for preview items if needed
            const previewList = previewContainer.querySelector('.hierarchy-preview-list');
            if (previewList) {
                new Sortable(previewList, {
                    animation: 150,
                    handle: '.preview-item-handle',
                    ghostClass: 'hierarchy-preview-item-ghost',
                    disabled: true // Preview only, not interactive
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            previewContainer.innerHTML = `
                <div class="alert alert-danger">
                    Error loading preview
                </div>
            `;
        });
}