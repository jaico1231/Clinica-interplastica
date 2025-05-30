{% extends 'base.html' %}
{% load static %}
{% load i18n %}

{% block title %}Dashboard{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'dashboard/css/dashboard.css' %}">
{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <!-- Sidebar -->
        <nav id="sidebar" class="col-md-3 col-lg-2 d-md-block bg-light sidebar">
            <div class="position-sticky pt-3">
                <h5 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
                    <span>{% trans 'Analytics' %}</span>
                </h5>
                <ul class="nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link {% if request.resolver_match.url_name == 'home' %}active{% endif %}" href="{% url 'dashboard:home' %}">
                            <i class="fas fa-chart-line"></i>
                            {% trans 'Dashboard' %}
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.resolver_match.url_name == 'chart_list' %}active{% endif %}" href="{% url 'dashboard:chart_list' %}">
                            <i class="fas fa-chart-bar"></i>
                            {% trans 'Gráficos' %}
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.resolver_match.url_name == 'chart_builder' %}active{% endif %}" href="{% url 'dashboard:chart_builder' %}">
                            <i class="fas fa-plus-circle"></i>
                            {% trans 'Crear Gráfico' %}
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.resolver_match.url_name == 'report_list' %}active{% endif %}" href="{% url 'dashboard:report_list' %}">
                            <i class="fas fa-file-alt"></i>
                            {% trans 'Informes' %}
                        </a>
                    </li>
                </ul>
                
                {% if dashboards and dashboards|length > 0 %}
                <h6 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
                    <span>{% trans 'Mis Dashboards' %}</span>
                </h6>
                <ul class="nav flex-column mb-2">
                    {% for db in dashboards %}
                    <li class="nav-item">
                        <a class="nav-link {% if dashboard and dashboard.id == db.id %}active{% endif %}" href="{% url 'dashboard:home' %}?dashboard_id={{ db.id }}">
                            <i class="fas {% if db.is_default %}fa-star{% else %}fa-tachometer-alt{% endif %}"></i>
                            {{ db.name }}
                        </a>
                    </li>
                    {% endfor %}
                </ul>
                {% endif %}
            </div>
        </nav>

        <!-- Main content -->
        <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
            <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                <h1 class="h2">{% block page_title %}{% trans 'Dashboard' %}{% endblock %}</h1>
                <div class="btn-toolbar mb-2 mb-md-0">
                    {% block page_actions %}{% endblock %}
                </div>
            </div>

            {% block dashboard_content %}{% endblock %}
        </main>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script>
<script src="{% static 'dashboard/js/dashboard.js' %}"></script>
{% block dashboard_js %}{% endblock %}
{% endblock %}
