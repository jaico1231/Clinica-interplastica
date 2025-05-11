{% extends 'dashboard/base_dashboard.html' %}
{% load static %}
{% load i18n %}

{% block page_title %}
    {% if dashboard %}{{ dashboard.name }}{% else %}{% trans 'Dashboard' %}{% endif %}
{% endblock %}

{% block page_actions %}
    <div class="dropdown me-2">
        <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" id="dashboardDropdown" data-bs-toggle="dropdown" aria-expanded="false">
            <i class="fas fa-cog"></i> {% trans 'Opciones' %}
        </button>
        <ul class="dropdown-menu" aria-labelledby="dashboardDropdown">
            <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#editDashboardModal">
                <i class="fas fa-edit"></i> {% trans 'Editar dashboard' %}
            </a></li>
            <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#newDashboardModal">
                <i class="fas fa-plus"></i> {% trans 'Nuevo dashboard' %}
            </a></li>
            {% if dashboard and not dashboard.is_default %}
            <li><a class="dropdown-item" href="#" id="setDefaultDashboard" data-dashboard-id="{{ dashboard.id }}">
                <i class="fas fa-star"></i> {% trans 'Establecer como predeterminado' %}
            </a></li>
            {% endif %}
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="#" data-bs-toggle="modal" data-bs-target="#resetLayoutModal">
                <i class="fas fa-undo"></i> {% trans 'Restablecer diseño' %}
            </a></li>
            {% if dashboard %}
            <li><a class="dropdown-item text-danger" href="#" data-bs-toggle="modal" data-bs-target="#deleteDashboardModal">
                <i class="fas fa-trash"></i> {% trans 'Eliminar dashboard' %}
            </a></li>
            {% endif %}
        </ul>
    </div>
    <a href="{% url 'dashboard:chart_builder' %}" class="btn btn-sm btn-primary">
        <i class="fas fa-plus"></i> {% trans 'Crear gráfico' %}
    </a>
{% endblock %}

{% block dashboard_content %}
    {% if dashboard %}
        {% if dashboard.widgets.all|length > 0 %}
            <div class="dashboard-grid" id="dashboardGrid">
                <!-- Los widgets se cargarán mediante JavaScript -->
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">{% trans 'Cargando...' %}</span>
                    </div>
                    <p class="mt-2">{% trans 'Cargando dashboard...' %}</p>
                </div>
            </div>
        {% else %}
            <div class="dashboard-empty text-center py-5">
                <div class="empty-state">
                    <i class="fas fa-chart-line fa-5x text-muted mb-3"></i>
                    <h3>{% trans 'Este dashboard está vacío' %}</h3>
                    <p class="text-muted">{% trans 'Comienza agregando gráficos a tu dashboard' %}</p>
                    <a href="{% url 'dashboard:chart_list' %}" class="btn btn-primary mt-3">
                        <i class="fas fa-chart-bar"></i> {% trans 'Ver gráficos disponibles' %}
                    </a>
                    <a href="{% url 'dashboard:chart_builder' %}" class="btn btn-outline-primary mt-3">
                        <i class="fas fa-plus"></i> {% trans 'Crear un nuevo gráfico' %}
                    </a>
                </div>
            </div>
        {% endif %}
    {% else %}
        <div class="dashboard-empty text-center py-5">
            <div class="empty-state">
                <i class="fas fa-chart-line fa-5x text-muted mb-3"></i>
                <h3>{% trans 'No hay dashboards disponibles' %}</h3>
                <p class="text-muted">{% trans 'Crea tu primer dashboard para comenzar' %}</p>
                <button class="btn btn-primary mt-3" data-bs-toggle="modal" data-bs-target="#newDashboardModal">
                    <i class="fas fa-plus"></i> {% trans 'Crear dashboard' %}
                </button>
            </div>
        </div>
    {% endif %}
{% endblock %}

{% block dashboard_js %}
<script>
    // Configuración de los widgets del dashboard
    const dashboardWidgets = {{ widget_configs|safe }};
    
    document.addEventListener('DOMContentLoaded', function() {
        // Inicializar el grid de dashboard
        initDashboardGrid(dashboardWidgets);
        
        // Inicializar los gráficos en cada widget
        initDashboardCharts(dashboardWidgets);
    });
    
    function initDashboardGrid(widgets) {
        const dashboardGrid = document.getElementById('dashboardGrid');
        if (!dashboardGrid) return;
        
        // Limpiar el grid
        dashboardGrid.innerHTML = '';
        
        // Crear los widgets
        widgets.forEach(widget => {
            const widgetEl = createWidgetElement(widget);
            dashboardGrid.appendChild(widgetEl);
        });
        
        // Si no hay widgets, mostrar mensaje
        if (widgets.length === 0) {
            dashboardGrid.innerHTML = `
                <div class="dashboard-empty text-center py-5">
                    <div class="empty-state">
                        <i class="fas fa-chart-line fa-5x text-muted mb-3"></i>
                        <h3>{% trans 'Este dashboard está vacío' %}</h3>
                        <p class="text-muted">{% trans 'Comienza agregando gráficos a tu dashboard' %}</p>
                        <a href="{% url 'dashboard:chart_list' %}" class="btn btn-primary mt-3">
                            <i class="fas fa-chart-bar"></i> {% trans 'Ver gráficos disponibles' %}
                        </a>
                    </div>
                </div>
            `;
        }
    }
    
    function createWidgetElement(widget) {
        const widgetEl = document.createElement('div');
        widgetEl.className = 'dashboard-widget';
        widgetEl.id = `widget-${widget.id}`;
        widgetEl.dataset.widgetId = widget.id;
        
        // Configurar posición y tamaño
        widgetEl.style.gridColumn = `${widget.position_x + 1} / span ${widget.width}`;
        widgetEl.style.gridRow = `${widget.position_y + 1} / span ${widget.height}`;
        
        // Establecer contenido
        widgetEl.innerHTML = `
            <div class="widget-header">
                <h5 class="widget-title">${widget.title}</h5>
                <div class="widget-actions">
                    <button class="btn btn-sm btn-link widget-action" data-action="edit" title="{% trans 'Editar' %}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-link widget-action" data-action="remove" title="{% trans 'Eliminar' %}">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="widget-body">
                <canvas id="chart-${widget.chart_id}"></canvas>
            </div>
        `;
        
        return widgetEl;
    }
    
    function initDashboardCharts(widgets) {
        widgets.forEach(widget => {
            const canvas = document.getElementById(`chart-${widget.chart_id}`);
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            new Chart(ctx, widget.chart_config);
        });
    }
</script>
{% endblock %}

<!-- Modals -->
{% include 'dashboard/components/dashboard_modals.html' %}
