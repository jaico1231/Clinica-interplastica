/**
 * dashboard.js - Funcionalidades principales para el Dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    setupModalHandlers();
    setupDashboardControls();
});

/**
 * Inicializa tooltips de Bootstrap
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Configurar manejadores para modales
 */
function setupModalHandlers() {
    // Evento para modal de edición de dashboard
    const editDashboardModal = document.getElementById('editDashboardModal');
    if (editDashboardModal) {
        editDashboardModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const dashboardId = button.getAttribute('data-dashboard-id');
            const dashboardName = button.getAttribute('data-dashboard-name');
            
            const modalTitle = editDashboardModal.querySelector('.modal-title');
            const dashboardIdInput = editDashboardModal.querySelector('#dashboardId');
            const dashboardNameInput = editDashboardModal.querySelector('#dashboardName');
            
            modalTitle.textContent = 'Editar Dashboard';
            dashboardIdInput.value = dashboardId;
            dashboardNameInput.value = dashboardName;
        });
    }
    
    // Evento para modal de confirmación de eliminación
    const deleteConfirmationModal = document.getElementById('deleteDashboardModal');
    if (deleteConfirmationModal) {
        deleteConfirmationModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const dashboardId = button.getAttribute('data-dashboard-id');
            const dashboardName = button.getAttribute('data-dashboard-name');
            
            const confirmDeleteBtn = deleteConfirmationModal.querySelector('#confirmDeleteDashboard');
            confirmDeleteBtn.setAttribute('data-dashboard-id', dashboardId);
            
            const modalBody = deleteConfirmationModal.querySelector('.modal-body p');
            modalBody.textContent = `¿Estás seguro de que deseas eliminar el dashboard "${dashboardName}"? Esta acción no se puede deshacer.`;
        });
    }
}

/**
 * Configurar controles del dashboard
 */
function setupDashboardControls() {
    // Manejar click en botón para establecer dashboard predeterminado
    const setDefaultBtn = document.getElementById('setDefaultDashboard');
    if (setDefaultBtn) {
        setDefaultBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const dashboardId = this.getAttribute('data-dashboard-id');
            setDashboardAsDefault(dashboardId);
        });
    }
    
    // Manejar envío del formulario de edición de dashboard
    const editDashboardForm = document.getElementById('editDashboardForm');
    if (editDashboardForm) {
        editDashboardForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            saveDashboard(formData);
        });
    }
    
    // Manejar envío del formulario de nuevo dashboard
    const newDashboardForm = document.getElementById('newDashboardForm');
    if (newDashboardForm) {
        newDashboardForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            createDashboard(formData);
        });
    }
    
    // Manejar confirmación de eliminación de dashboard
    const confirmDeleteBtn = document.getElementById('confirmDeleteDashboard');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function(e) {
            const dashboardId = this.getAttribute('data-dashboard-id');
            deleteDashboard(dashboardId);
        });
    }
    
    // Manejar click en botón para restablecer layout
    const resetLayoutBtn = document.getElementById('confirmResetLayout');
    if (resetLayoutBtn) {
        resetLayoutBtn.addEventListener('click', function(e) {
            resetDashboardLayout();
        });
    }
    
    // Manejar acciones de widgets
    setupWidgetActions();
}

/**
 * Configurar acciones de widgets
 */
function setupWidgetActions() {
    // Delegar eventos para acciones de widgets
    const dashboardGrid = document.getElementById('dashboardGrid');
    if (dashboardGrid) {
        dashboardGrid.addEventListener('click', function(e) {
            // Botón de editar
            if (e.target.closest('.widget-action[data-action="edit"]')) {
                const widget = e.target.closest('.dashboard-widget');
                const widgetId = widget.getAttribute('data-widget-id');
                const chartId = widget.getAttribute('data-chart-id');
                editChart(chartId);
            }
            
            // Botón de eliminar
            if (e.target.closest('.widget-action[data-action="remove"]')) {
                const widget = e.target.closest('.dashboard-widget');
                const widgetId = widget.getAttribute('data-widget-id');
                removeWidgetFromDashboard(widgetId);
            }
        });
    }
}

/**
 * Inicializar los gráficos del dashboard
 * @param {Array} widgets - Array de widgets con configuraciones de gráficos
 */
function initDashboardCharts(widgets) {
    if (!widgets || widgets.length === 0) return;
    
    // Destruir gráficos existentes para evitar conflictos
    if (window.dashboardCharts) {
        Object.values(window.dashboardCharts).forEach(chart => {
            if (chart) chart.destroy();
        });
    }
    
    // Crear objeto para almacenar instancias de gráficos
    window.dashboardCharts = {};
    
    // Crear cada gráfico
    widgets.forEach(widget => {
        try {
            const chartId = `chart-${widget.chart_id}`;
            const canvas = document.getElementById(chartId);
            
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            window.dashboardCharts[chartId] = new Chart(ctx, widget.chart_config);
        } catch (error) {
            console.error('Error inicializando gráfico:', error);
        }
    });
}

/**
 * Inicializar grid de dashboard
 * @param {Array} widgets - Array de widgets
 */
function initDashboardGrid(widgets) {
    const dashboardGrid = document.getElementById('dashboardGrid');
    if (!dashboardGrid) return;
    
    // Limpiar grid
    dashboardGrid.innerHTML = '';
    
    if (!widgets || widgets.length === 0) {
        // Mostrar mensaje si no hay widgets
        dashboardGrid.innerHTML = `
            <div class="dashboard-empty text-center py-5" style="grid-column: span 12;">
                <div class="empty-state">
                    <i class="fas fa-chart-line fa-5x text-muted mb-3"></i>
                    <h3>Este dashboard está vacío</h3>
                    <p class="text-muted">Comienza agregando gráficos a tu dashboard</p>
                    <a href="/dashboard/charts/" class="btn btn-primary mt-3">
                        <i class="fas fa-chart-bar"></i> Ver gráficos disponibles
                    </a>
                </div>
            </div>
        `;
        return;
    }
    
    // Crear widgets
    widgets.forEach(widget => {
        const widgetElement = createWidgetElement(widget);
        dashboardGrid.appendChild(widgetElement);
    });
}

/**
 * Crear elemento HTML para un widget
 * @param {Object} widget - Datos del widget
 * @returns {HTMLElement} - Elemento del widget
 */
function createWidgetElement(widget) {
    const widgetElement = document.createElement('div');
    widgetElement.className = 'dashboard-widget';
    widgetElement.id = `widget-${widget.id}`;
    widgetElement.setAttribute('data-widget-id', widget.id);
    widgetElement.setAttribute('data-chart-id', widget.chart_id);
    
    // Configurar posición y tamaño en el grid
    widgetElement.style.gridColumn = `${widget.position_x + 1} / span ${widget.width}`;
    widgetElement.style.gridRow = `${widget.position_y + 1} / span ${widget.height}`;
    
    // Contenido HTML del widget
    widgetElement.innerHTML = `
        <div class="widget-header">
            <h5 class="widget-title">${widget.title}</h5>
            <div class="widget-actions">
                <button class="btn btn-sm btn-link widget-action" data-action="edit" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-link widget-action" data-action="remove" title="Eliminar">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
        <div class="widget-body">
            <canvas id="chart-${widget.chart_id}"></canvas>
        </div>
    `;
    
    return widgetElement;
}

/**
 * Guardar el dashboard
 * @param {FormData} formData - Datos del formulario
 */
async function saveDashboard(formData) {
    try {
        const response = await fetch('/dashboard/api/save-dashboard/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Error al guardar dashboard');
        }
        
        // Recargar la página
        window.location.reload();
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al guardar dashboard: ${error.message}`);
    }
}

/**
 * Crear nuevo dashboard
 * @param {FormData} formData - Datos del formulario
 */
async function createDashboard(formData) {
    try {
        const response = await fetch('/dashboard/api/create-dashboard/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Error al crear dashboard');
        }
        
        // Redirigir al nuevo dashboard
        window.location.href = `/dashboard/?dashboard_id=${data.dashboard_id}`;
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al crear dashboard: ${error.message}`);
    }
}

/**
 * Eliminar dashboard
 * @param {string} dashboardId - ID del dashboard a eliminar
 */
async function deleteDashboard(dashboardId) {
    try {
        const response = await fetch(`/dashboard/api/delete-dashboard/${dashboardId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Error al eliminar dashboard');
        }
        
        // Redirigir a la página principal
        window.location.href = '/dashboard/';
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al eliminar dashboard: ${error.message}`);
    }
}

/**
 * Establecer dashboard como predeterminado
 * @param {string} dashboardId - ID del dashboard
 */
async function setDashboardAsDefault(dashboardId) {
    try {
        const response = await fetch(`/dashboard/api/set-default-dashboard/${dashboardId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Error al establecer dashboard predeterminado');
        }
        
        // Recargar la página
        window.location.reload();
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al establecer dashboard predeterminado: ${error.message}`);
    }
}

/**
 * Restablecer layout del dashboard
 */
async function resetDashboardLayout() {
    try {
        const dashboardId = document.getElementById('currentDashboardId').value;
        
        const response = await fetch(`/dashboard/api/reset-dashboard-layout/${dashboardId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Error al restablecer layout');
        }
        
        // Recargar la página
        window.location.reload();
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al restablecer layout: ${error.message}`);
    }
}

/**
 * Remover widget del dashboard
 * @param {string} widgetId - ID del widget a eliminar
 */
async function removeWidgetFromDashboard(widgetId) {
    if (!confirm('¿Estás seguro de que deseas eliminar este widget?')) {
        return;
    }
    
    try {
        const response = await fetch(`/dashboard/api/remove-widget/${widgetId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Error al eliminar widget');
        }
        
        // Eliminar el widget del DOM
        const widget = document.getElementById(`widget-${widgetId}`);
        if (widget) {
            widget.remove();
        }
        
        // Si no hay más widgets, mostrar mensaje vacío
        const dashboardGrid = document.getElementById('dashboardGrid');
        if (dashboardGrid && dashboardGrid.children.length === 0) {
            initDashboardGrid([]);
        }
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error al eliminar widget: ${error.message}`);
    }
}

/**
 * Editar gráfico
 * @param {string} chartId - ID del gráfico a editar
 */
function editChart(chartId) {
    window.location.href = `/dashboard/chart-builder/${chartId}/`;
}

/**
 * Obtener token CSRF del DOM
 * @returns {string} - Token CSRF
 */
function getCsrfToken() {
    return document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || 
           document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
}

/**
 * Formatear fecha para mostrar
 * @param {string} dateString - Fecha en formato ISO
 * @returns {string} - Fecha formateada
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}
