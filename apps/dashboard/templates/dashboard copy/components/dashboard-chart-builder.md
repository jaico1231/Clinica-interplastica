{% extends 'dashboard/base_dashboard.html' %}
{% load static %}
{% load i18n %}

{% block page_title %}
    {% if chart_id %}{% trans 'Editar Gráfico' %}{% else %}{% trans 'Crear Gráfico' %}{% endif %}
{% endblock %}

{% block page_actions %}
    <button id="saveChartBtn" class="btn btn-sm btn-primary">
        <i class="fas fa-save"></i> {% trans 'Guardar gráfico' %}
    </button>
    <a href="{% url 'dashboard:chart_list' %}" class="btn btn-sm btn-outline-secondary ms-2">
        <i class="fas fa-times"></i> {% trans 'Cancelar' %}
    </a>
{% endblock %}

{% block dashboard_content %}
<div class="row">
    <!-- Panel de configuración -->
    <div class="col-md-4">
        <div class="card mb-4">
            <div class="card-header">
                <h5 class="card-title mb-0">{% trans 'Configuración del gráfico' %}</h5>
            </div>
            <div class="card-body">
                <form id="chartBuilderForm">
                    {% if chart_id %}
                    <input type="hidden" name="chart_id" id="chartId" value="{{ chart_id }}">
                    {% endif %}
                    
                    <div class="mb-3">
                        <label for="chartTitle" class="form-label">{% trans 'Título' %}</label>
                        <input type="text" class="form-control" id="chartTitle" name="title" placeholder="{% trans 'Título del gráfico' %}" required>
                    </div>
                    
                    <div class="mb-3">
                        <label for="chartDescription" class="form-label">{% trans 'Descripción' %}</label>
                        <textarea class="form-control" id="chartDescription" name="description" rows="2" placeholder="{% trans 'Descripción opcional' %}"></textarea>
                    </div>
                    
                    <div class="mb-3">
                        <label for="chartType" class="form-label">{% trans 'Tipo de gráfico' %}</label>
                        <select class="form-select" id="chartType" name="chart_type_id" required>
                            <option value="">{% trans 'Seleccionar tipo...' %}</option>
                            {% for chart_type in chart_types %}
                            <option value="{{ chart_type.id }}">{{ chart_type.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label for="modelSelect" class="form-label">{% trans 'Modelo de datos' %}</label>
                        <select class="form-select" id="modelSelect" name="model" required>
                            <option value="">{% trans 'Seleccionar modelo...' %}</option>
                            {% for model in models %}
                            <option value="{{ model.app_label }}.{{ model.model_name }}" 
                                    data-app-label="{{ model.app_label }}"
                                    data-model-name="{{ model.model_name }}"
                                    data-content-type-id="{{ model.content_type_id }}"
                                    {% if model.is_audit_model %}class="fw-bold"{% endif %}>
                                {{ model.verbose_name }} {% if model.is_audit_model %}(*){% endif %}
                            </option>
                            {% endfor %}
                        </select>
                        <input type="hidden" id="modelContentTypeId" name="model_content_type_id">
                    </div>
                    
                    <div id="fieldsContainer" class="d-none">
                        <div class="mb-3">
                            <label for="xAxisField" class="form-label">{% trans 'Campo para eje X' %}</label>
                            <select class="form-select" id="xAxisField" name="x_axis_field">
                                <option value="">{% trans 'Seleccionar campo...' %}</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <label for="yAxisField" class="form-label">{% trans 'Campo para eje Y / Valor' %}</label>
                            <select class="form-select" id="yAxisField" name="y_axis_field">
                                <option value="">{% trans 'Seleccionar campo...' %}</option>
                                <option value="count">{% trans 'Conteo de registros' %}</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="colorScheme" class="form-label">{% trans 'Esquema de colores' %}</label>
                        <select class="form-select" id="colorScheme" name="color_scheme">
                            <option value="default">{% trans 'Predeterminado' %}</option>
                            <option value="blue">{% trans 'Azul' %}</option>
                            <option value="green">{% trans 'Verde' %}</option>
                            <option value="red">{% trans 'Rojo' %}</option>
                            <option value="grayscale">{% trans 'Escala de grises' %}</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="isPublic" name="is_public">
                            <label class="form-check-label" for="isPublic">
                                {% trans 'Compartir con otros usuarios' %}
                            </label>
                        </div>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- Panel de filtros -->
        <div class="card mb-4 d-none" id="filtersCard">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="card-title mb-0">{% trans 'Filtros' %}</h5>
                <button class="btn btn-sm btn-primary" id="addFilterBtn">
                    <i class="fas fa-plus"></i> {% trans 'Añadir filtro' %}
                </button>
            </div>
            <div class="card-body">
                <div id="filtersContainer">
                    <div class="text-center text-muted py-3">
                        {% trans 'No hay filtros configurados' %}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Panel de opciones avanzadas -->
        <div class="card mb-4 d-none" id="advancedOptionsCard">
            <div class="card-header">
                <h5 class="card-title mb-0">{% trans 'Opciones avanzadas' %}</h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <label for="aggregationFunction" class="form-label">{% trans 'Función de agregación' %}</label>
                    <select class="form-select" id="aggregationFunction" name="aggregate">
                        <option value="count">{% trans 'Conteo' %}</option>
                        <option value="sum">{% trans 'Suma' %}</option>
                        <option value="avg">{% trans 'Promedio' %}</option>
                        <option value="min">{% trans 'Mínimo' %}</option>
                        <option value="max">{% trans 'Máximo' %}</option>
                    </select>
                </div>
                
                <div class="mb-3 d-none" id="timeIntervalContainer">
                    <label for="timeInterval" class="form-label">{% trans 'Intervalo de tiempo' %}</label>
                    <select class="form-select" id="timeInterval" name="date_interval">
                        <option value="day">{% trans 'Día' %}</option>
                        <option value="week">{% trans 'Semana' %}</option>
                        <option value="month" selected>{% trans 'Mes' %}</option>
                        <option value="quarter">{% trans 'Trimestre' %}</option>
                        <option value="year">{% trans 'Año' %}</option>
                    </select>
                </div>
                
                <div class="mb-3">
                    <label for="limitResults" class="form-label">{% trans 'Límite de resultados' %}</label>
                    <input type="number" class="form-control" id="limitResults" name="limit" min="1" max="100" value="50">
                </div>
                
                <div class="mb-3" id="groupByContainer">
                    <label for="groupByField" class="form-label">{% trans 'Agrupar por' %}</label>
                    <select class="form-select" id="groupByField" name="group_by">
                        <option value="">{% trans 'Sin agrupación' %}</option>
                    </select>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Vista previa del gráfico -->
    <div class="col-md-8">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="card-title mb-0">{% trans 'Vista previa' %}</h5>
                <button class="btn btn-sm btn-outline-primary" id="refreshPreviewBtn">
                    <i class="fas fa-sync-alt"></i> {% trans 'Actualizar' %}
                </button>
            </div>
            <div class="card-body">
                <div id="chartPreviewContainer" style="min-height: 400px; position: relative;">
                    <div class="text-center py-5">
                        <i class="fas fa-chart-bar fa-4x text-muted mb-3"></i>
                        <h3>{% trans 'Vista previa del gráfico' %}</h3>
                        <p class="text-muted">{% trans 'Completa la configuración para ver una vista previa' %}</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block dashboard_js %}
<script>
    // Datos iniciales
    const modelsData = {{ models_json|safe }};
    const chartId = {% if chart_id %}{{ chart_id }}{% else %}null{% endif %};
    
    // Variables globales
    let fieldsData = [];
    let filtersData = [];
    let chartPreviewInstance = null;
    
    document.addEventListener('DOMContentLoaded', function() {
        // Inicializar selectores
        initSelectors();
        
        // Si es edición, cargar datos del gráfico
        if (chartId) {
            loadChartData(chartId);
        }
        
        // Event listeners
        document.getElementById('modelSelect').addEventListener('change', handleModelChange);
        document.getElementById('chartType').addEventListener('change', handleChartTypeChange);
        document.getElementById('xAxisField').addEventListener('change', handleAxisFieldChange);
        document.getElementById('yAxisField').addEventListener('change', handleAxisFieldChange);
        document.getElementById('colorScheme').addEventListener('change', refreshChartPreview);
        document.getElementById('refreshPreviewBtn').addEventListener('click', refreshChartPreview);
        document.getElementById('saveChartBtn').addEventListener('click', saveChart);
        document.getElementById('addFilterBtn').addEventListener('click', addFilter);
    });
    
    function initSelectors() {
        // Inicializar selectores avanzados con select2 si está disponible
        if (typeof $.fn.select2 !== 'undefined') {
            $('#modelSelect').select2({
                placeholder: '{% trans "Seleccionar modelo..." %}',
                allowClear: true,
                width: '100%'
            });
            
            $('#xAxisField, #yAxisField, #groupByField').select2({
                placeholder: '{% trans "Seleccionar campo..." %}',
                allowClear: true,
                width: '100%'
            });
            
            $('#chartType').select2({
                placeholder: '{% trans "Seleccionar tipo..." %}',
                allowClear: true,
                width: '100%'
            });
        }
    }
    
    async function handleModelChange() {
        const select = document.getElementById('modelSelect');
        const option = select.options[select.selectedIndex];
        
        if (!option || !option.value) {
            document.getElementById('fieldsContainer').classList.add('d-none');
            document.getElementById('filtersCard').classList.add('d-none');
            document.getElementById('advancedOptionsCard').classList.add('d-none');
            return;
        }
        
        // Obtener app_label y model_name
        const appLabel = option.dataset.appLabel;
        const modelName = option.dataset.modelName;
        const contentTypeId = option.dataset.contentTypeId;
        
        // Actualizar campo oculto
        document.getElementById('modelContentTypeId').value = contentTypeId;
        
        // Mostrar contenedor de campos
        document.getElementById('fieldsContainer').classList.remove('d-none');
        
        // Cargar campos del modelo
        await loadModelFields(appLabel, modelName);
        
        // Mostrar tarjetas de opciones
        document.getElementById('filtersCard').classList.remove('d-none');
        document.getElementById('advancedOptionsCard').classList.remove('d-none');
    }
    
    async function loadModelFields(appLabel, modelName) {
        try {
            // Obtener campos del modelo mediante la API
            const response = await fetch(`{% url 'dashboard:get_model_fields' %}?app_label=${appLabel}&model_name=${modelName}`);
            const data = await response.json();
            
            if (!data.success) {
                console.error('Error cargando campos:', data.message);
                return;
            }
            
            // Guardar datos de campos
            fieldsData = data.fields;
            
            // Llenar selectores de campos
            populateFieldSelectors(fieldsData);
            
        } catch (error) {
            console.error('Error:', error);
        }
    }
    
    function populateFieldSelectors(fields) {
        // Selector de eje X
        const xAxisSelect = document.getElementById('xAxisField');
        // Selector de eje Y
        const yAxisSelect = document.getElementById('yAxisField');
        // Selector de agrupación
        const groupBySelect = document.getElementById('groupByField');
        
        // Limpiar opciones existentes
        xAxisSelect.innerHTML = '<option value="">{% trans "Seleccionar campo..." %}</option>';
        yAxisSelect.innerHTML = '<option value="">{% trans "Seleccionar campo..." %}</option><option value="count">{% trans "Conteo de registros" %}</option>';
        groupBySelect.innerHTML = '<option value="">{% trans "Sin agrupación" %}</option>';
        
        // Agregar campos a los selectores
        fields.forEach(field => {
            // Evitar campos de relación muchos a muchos en el eje X
            if (field.field_type !== 'ManyToManyField') {
                const xOption = document.createElement('option');
                xOption.value = field.name;
                xOption.textContent = field.verbose_name || field.name;
                xOption.dataset.fieldType = field.field_type;
                xOption.dataset.isRelation = field.is_relation;
                xAxisSelect.appendChild(xOption);
            }
            
            // Solo campos numéricos para el eje Y (además de "count")
            if (['IntegerField', 'FloatField', 'DecimalField'].includes(field.field_type)) {
                const yOption = document.createElement('option');
                yOption.value = field.name;
                yOption.textContent = field.verbose_name || field.name;
                yAxisSelect.appendChild(yOption);
            }
            
            // Campos para agrupar (categóricos o relacionales)
            if (['CharField', 'BooleanField', 'ForeignKey', 'DateField', 'DateTimeField'].includes(field.field_type)) {
                const groupOption = document.createElement('option');
                groupOption.value = field.name;
                groupOption.textContent = field.verbose_name || field.name;
                groupBySelect.appendChild(groupOption);
            }
        });
        
        // Reinicializar select2 si está disponible
        if (typeof $.fn.select2 !== 'undefined') {
            $('#xAxisField, #yAxisField, #groupByField').select2({
                placeholder: '{% trans "Seleccionar campo..." %}',
                allowClear: true,
                width: '100%'
            });
        }
    }
    
    function handleChartTypeChange() {
        const chartType = document.getElementById('chartType').value;
        
        // Mostrar/ocultar opciones según el tipo de gráfico
        if (['line', 'area'].includes(chartType)) {
            document.getElementById('timeIntervalContainer').classList.remove('d-none');
        } else {
            document.getElementById('timeIntervalContainer').classList.add('d-none');
        }
    }
    
    function handleAxisFieldChange() {
        const xAxisSelect = document.getElementById('xAxisField');
        const xAxisOption = xAxisSelect.options[xAxisSelect.selectedIndex];
        
        // Verificar si es un campo de fecha
        if (xAxisOption && xAxisOption.dataset.fieldType) {
            const isDateField = ['DateField', 'DateTimeField'].includes(xAxisOption.dataset.fieldType);
            
            // Mostrar/ocultar opciones de intervalo de tiempo
            if (isDateField) {
                document.getElementById('timeIntervalContainer').classList.remove('d-none');
            } else {
                document.getElementById('timeIntervalContainer').classList.add('d-none');
            }
        }
    }
    
    function addFilter() {
        const filterContainer = document.getElementById('filtersContainer');
        const filterId = 'filter-' + Date.now();
        
        // Eliminar mensaje de "no hay filtros"
        if (filterContainer.querySelector('.text-muted')) {
            filterContainer.innerHTML = '';
        }
        
        // Crear elemento del filtro
        const filterElement = document.createElement('div');
        filterElement.className = 'filter-item mb-3 p-2 border rounded';
        filterElement.id = filterId;
        
        // Contenido del filtro
        filterElement.innerHTML = `
            <div class="d-flex justify-content-between mb-2">
                <strong>{% trans "Filtro" %}</strong>
                <button type="button" class="btn btn-sm btn-link text-danger p-0" onclick="removeFilter('${filterId}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="row g-2">
                <div class="col-5">
                    <select class="form-select form-select-sm filter-field" onchange="updateFilterOperators('${filterId}')">
                        <option value="">{% trans "Campo..." %}</option>
                        ${fieldsData.map(field => `<option value="${field.name}" data-field-type="${field.field_type}">${field.verbose_name || field.name}</option>`).join('')}
                    </select>
                </div>
                <div class="col-3">
                    <select class="form-select form-select-sm filter-operator">
                        <option value="exact">{% trans "=" %}</option>
                    </select>
                </div>
                <div class="col-4">
                    <input type="text" class="form-control form-control-sm filter-value" placeholder="{% trans "Valor" %}">
                </div>
            </div>
        `;
        
        filterContainer.appendChild(filterElement);
    }
    
    function removeFilter(filterId) {
        const filterElement = document.getElementById(filterId);
        if (filterElement) {
            filterElement.remove();
        }
        
        // Si no hay más filtros, mostrar mensaje
        const filterContainer = document.getElementById('filtersContainer');
        if (filterContainer.childElementCount === 0) {
            filterContainer.innerHTML = `
                <div class="text-center text-muted py-3">
                    {% trans 'No hay filtros configurados' %}
                </div>
            `;
        }
    }
    
    function updateFilterOperators(filterId) {
        const filterElement = document.getElementById(filterId);
        const fieldSelect = filterElement.querySelector('.filter-field');
        const operatorSelect = filterElement.querySelector('.filter-operator');
        const valueInput = filterElement.querySelector('.filter-value');
        
        const fieldOption = fieldSelect.options[fieldSelect.selectedIndex];
        const fieldType = fieldOption.dataset.fieldType;
        
        // Limpiar operadores actuales
        operatorSelect.innerHTML = '';
        
        // Agregar operadores según el tipo de campo
        let operators = [];
        
        switch (fieldType) {
            case 'CharField':
            case 'TextField':
                operators = [
                    { value: 'exact', text: '{% trans "=" %}' },
                    { value: 'icontains', text: '{% trans "Contiene" %}' },
                    { value: 'istartswith', text: '{% trans "Comienza con" %}' },
                    { value: 'iendswith', text: '{% trans "Termina con" %}' },
                    { value: 'isnull', text: '{% trans "Es nulo" %}' }
                ];
                break;
                
            case 'IntegerField':
            case 'FloatField':
            case 'DecimalField':
                operators = [
                    { value: 'exact', text: '{% trans "=" %}' },
                    { value: 'gt', text: '{% trans ">" %}' },
                    { value: 'gte', text: '{% trans ">=" %}' },
                    { value: 'lt', text: '{% trans "<" %}' },
                    { value: 'lte', text: '{% trans "<=" %}' },
                    { value: 'isnull', text: '{% trans "Es nulo" %}' }
                ];
                break;
                
            case 'DateField':
            case 'DateTimeField':
                operators = [
                    { value: 'exact', text: '{% trans "=" %}' },
                    { value: 'gt', text: '{% trans ">" %}' },
                    { value: 'gte', text: '{% trans ">=" %}' },
                    { value: 'lt', text: '{% trans "<" %}' },
                    { value: 'lte', text: '{% trans "<=" %}' },
                    { value: 'isnull', text: '{% trans "Es nulo" %}' }
                ];
                break;
                
            case 'BooleanField':
                operators = [
                    { value: 'exact', text: '{% trans "=" %}' }
                ];
                break;
                
            default:
                operators = [
                    { value: 'exact', text: '{% trans "=" %}' },
                    { value: 'isnull', text: '{% trans "Es nulo" %}' }
                ];
        }
        
        // Agregar operadores al select
        operators.forEach(op => {
            const option = document.createElement('option');
            option.value = op.value;
            option.textContent = op.text;
            operatorSelect.appendChild(option);
        });
        
        // Cambiar tipo de input según el campo
        if (fieldType === 'BooleanField') {
            valueInput.type = 'checkbox';
            valueInput.classList.add('form-check-input');
        } else if (['DateField', 'DateTimeField'].includes(fieldType)) {
            valueInput.type = 'date';
        } else {
            valueInput.type = 'text';
            valueInput.classList.remove('form-check-input');
        }
    }
    
    async function refreshChartPreview() {
        const form = document.getElementById('chartBuilderForm');
        const formData = new FormData(form);
        const chartPreviewContainer = document.getElementById('chartPreviewContainer');
        
        // Obtener valores de los selectores
        const contentTypeId = document.getElementById('modelContentTypeId').value;
        const xAxisField = document.getElementById('xAxisField').value;
        const yAxisField = document.getElementById('yAxisField').value;
        const chartTypeId = document.getElementById('chartType').value;
        
        // Validar campos mínimos
        if (!contentTypeId || !xAxisField || !yAxisField || !chartTypeId) {
            chartPreviewContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-exclamation-circle fa-4x text-warning mb-3"></i>
                    <h3>{% trans 'Datos insuficientes' %}</h3>
                    <p class="text-muted">{% trans 'Complete al menos el modelo, tipo de gráfico y campos de ejes X e Y' %}</p>
                </div>
            `;
            return;
        }
        
        // Recopilar filtros
        const filters = [];
        document.querySelectorAll('.filter-item').forEach(filter => {
            const field = filter.querySelector('.filter-field').value;
            const operator = filter.querySelector('.filter-operator').value;
            const value = filter.querySelector('.filter-value').value;
            
            if (field && operator) {
                filters.push({
                    field,
                    operator,
                    value
                });
            }
        });
        
        // Recopilar configuración avanzada
        const chartConfig = {
            aggregate: document.getElementById('aggregationFunction').value,
            date_interval: document.getElementById('timeInterval').value,
            limit: document.getElementById('limitResults').value,
            group_by: document.getElementById('groupByField').value
        };
        
        // Datos para la vista previa
        const previewData = {
            title: document.getElementById('chartTitle').value || 'Vista previa',
            chart_type_id: chartTypeId,
            model_content_type_id: contentTypeId,
            x_axis_field: xAxisField,
            y_axis_field: yAxisField,
            filter_config: filters,
            chart_config: chartConfig,
            color_scheme: document.getElementById('colorScheme').value
        };
        
        try {
            // Mostrar indicador de carga
            chartPreviewContainer.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">{% trans 'Cargando...' %}</span>
                    </div>
                    <p class="mt-2">{% trans 'Generando vista previa...' %}</p>
                </div>
            `;
            
            // Obtener vista previa del gráfico
            const response = await fetch('{% url "dashboard:get_chart_preview" %}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(previewData)
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Error generando vista previa');
            }
            
            // Limpiar contenedor
            chartPreviewContainer.innerHTML = '';
            
            // Crear canvas para el gráfico
            const canvas = document.createElement('canvas');
            canvas.id = 'chartPreview';
            chartPreviewContainer.appendChild(canvas);
            
            // Destruir instancia anterior si existe
            if (chartPreviewInstance) {
                chartPreviewInstance.destroy();
            }
            
            // Crear nueva instancia del gráfico
            const ctx = canvas.getContext('2d');
            chartPreviewInstance = new Chart(ctx, data.chart_config);
            
        } catch (error) {
            console.error('Error:', error);
            
            chartPreviewContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-exclamation-circle fa-4x text-danger mb-3"></i>
                    <h3>{% trans 'Error generando vista previa' %}</h3>
                    <p class="text-muted">${error.message}</p>
                </div>
            `;
        }
    }
    
    async function saveChart() {
        const form = document.getElementById('chartBuilderForm');
        const formData = new FormData(form);
        
        // Obtener valores del formulario
        const chartTitle = document.getElementById('chartTitle').value;
        const contentTypeId = document.getElementById('modelContentTypeId').value;
        const xAxisField = document.getElementById('xAxisField').value;
        const yAxisField = document.getElementById('yAxisField').value;
        const chartTypeId = document.getElementById('chartType').value;
        
        // Validar campos mínimos
        if (!chartTitle || !contentTypeId || !xAxisField || !yAxisField || !chartTypeId) {
            alert('{% trans "Por favor complete todos los campos requeridos" %}');
            return;
        }
        
        // Recopilar filtros
        const filters = [];
        document.querySelectorAll('.filter-item').forEach(filter => {
            const field = filter.querySelector('.filter-field').value;
            const operator = filter.querySelector('.filter-operator').value;
            const value = filter.querySelector('.filter-value').value;
            
            if (field && operator) {
                filters.push({
                    field,
                    operator,
                    value
                });
            }
        });
        
        // Recopilar configuración avanzada
        const chartConfig = {
            aggregate: document.getElementById('aggregationFunction').value,
            date_interval: document.getElementById('timeInterval').value,
            limit: document.getElementById('limitResults').value,
            group_by: document.getElementById('groupByField').value
        };
        
        // Datos para guardar
        const saveData = {
            title: chartTitle,
            description: document.getElementById('chartDescription').value,
            chart_type_id: chartTypeId,
            model_content_type_id: contentTypeId,
            x_axis_field: xAxisField,
            y_axis_field: yAxisField,
            filter_config: filters,
            chart_config: chartConfig,
            color_scheme: document.getElementById('colorScheme').value,
            is_public: document.getElementById('isPublic').checked
        };
        
        // Si es edición, agregar ID
        if (chartId) {
            saveData.chart_id = chartId;
        }
        
        try {
            // Guardar gráfico
            const response = await fetch('{% url "dashboard:save_chart" %}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(saveData)
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Error guardando gráfico');
            }
            
            // Redireccionar a la lista de gráficos o al detalle
            window.location.href = `{% url 'dashboard:chart_detail' 0 %}`.replace('0', data.chart_id);
            
        } catch (error) {
            console.error('Error:', error);
            alert(`{% trans "Error guardando gráfico" %}: ${error.message}`);
        }
    }
    
    async function loadChartData(chartId) {
        try {
            // Cargar datos del gráfico
            const response = await fetch(`/api/charts/${chartId}/`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Error cargando datos del gráfico');
            }
            
            // Llenar formulario con datos del gráfico
            document.getElementById('chartTitle').value = data.chart.title;
            document.getElementById('chartDescription').value = data.chart.description;
            document.getElementById('chartType').value = data.chart.chart_type_id;
            document.getElementById('colorScheme').value = data.chart.color_scheme || 'default';
            document.getElementById('isPublic').checked = data.chart.is_public;
            
            // Seleccionar modelo
            const modelSelect = document.getElementById('modelSelect');
            const contentTypeId = data.chart.model_content_type_id;
            
            for (let i = 0; i < modelSelect.options.length; i++) {
                const option = modelSelect.options[i];
                if (option.dataset.contentTypeId == contentTypeId) {
                    modelSelect.selectedIndex = i;
                    document.getElementById('modelContentTypeId').value = contentTypeId;
                    
                    // Cargar campos del modelo
                    await loadModelFields(option.dataset.appLabel, option.dataset.modelName);
                    
                    // Mostrar contenedores
                    document.getElementById('fieldsContainer').classList.remove('d-none');
                    document.getElementById('filtersCard').classList.remove('d-none');
                    document.getElementById('advancedOptionsCard').classList.remove('d-none');
                    
                    break;
                }
            }
            
            // Configuración de campos y ejes
            document.getElementById('xAxisField').value = data.chart.x_axis_field;
            document.getElementById('yAxisField').value = data.chart.y_axis_field;
            
            // Cargar filtros
            if (data.chart.filter_config && data.chart.filter_config.length > 0) {
                const filterContainer = document.getElementById('filtersContainer');
                filterContainer.innerHTML = '';
                
                data.chart.filter_config.forEach(filter => {
                    // Agregar filtro y llenarlo
                    // Implementar esta lógica según la estructura de tus filtros
                });
            }
            
            // Configuración avanzada
            if (data.chart.chart_config) {
                const config = data.chart.chart_config;
                
                document.getElementById('aggregationFunction').value = config.aggregate || 'count';
                document.getElementById('timeInterval').value = config.date_interval || 'month';
                document.getElementById('limitResults').value = config.limit || '50';
                
                if (config.group_by) {
                    document.getElementById('groupByField').value = config.group_by;
                }
            }
            
            // Actualizar select2 si está disponible
            if (typeof $.fn.select2 !== 'undefined') {
                $('#modelSelect, #xAxisField, #yAxisField, #groupByField, #chartType').trigger('change');
            }
            
            // Generar vista previa
            refreshChartPreview();
            
        } catch (error) {
            console.error('Error:', error);
            alert(`{% trans "Error cargando datos del gráfico" %}: ${error.message}`);
        }
    }
    
    // Utilidad para obtener CSRF token
    function getCsrfToken() {
        return document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }
</script>
{% endblock %}
