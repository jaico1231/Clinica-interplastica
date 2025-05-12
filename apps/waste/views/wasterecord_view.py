from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Sum, F, Case, When, Value, DecimalField
from django.utils.translation import gettext as _
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView, View
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib import messages
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.units import mm, cm
from io import BytesIO

from apps.base.views.genericexportview import GenericExportView
from apps.base.views.genericlistview import OptimizedSecureListView
from apps.base.models.company import CompanyArea
from apps.waste.models.waste_model import WasteManager, WasteType, WasteRecord, WasteDestination, WasteMediaFile
from apps.waste.forms.waste_form import WasteRecordForm, WasteDestinationForm

class WasteRecordListView(OptimizedSecureListView):
    """
    Vista optimizada para listar registros de residuos con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'waste.view_wasterecord'
    model = WasteRecord
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['waste_type__name', 'area__name', 'responsible', 'storage_location']
    # Ordenamiento por defecto
    order_by = ('-record_date',)
    
    # Atributos específicos
    title = _('Listado de Registros de Residuos')
    entity = _('Registro de Residuos')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros adicionales específicos
        # Filtrar por rango de fechas
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        if date_from:
            queryset = queryset.filter(record_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(record_date__lte=date_to)
        
        # Filtrar por tipo de residuo
        waste_type_id = self.request.GET.get('waste_type', '')
        if waste_type_id:
            queryset = queryset.filter(waste_type_id=waste_type_id)
        
        # Filtrar por área
        area_id = self.request.GET.get('area', '')
        if area_id:
            queryset = queryset.filter(area_id=area_id)
            
        # Filtrar por unidad
        unit = self.request.GET.get('unit', '')
        if unit:
            queryset = queryset.filter(unit=unit)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['FECHA', 'ÁREA', 'TIPO DE RESIDUO', 'CANTIDAD', 'UNIDAD', 'RESPONSABLE', 'UBICACIÓN']
        context['fields'] = ['record_date', 'area__name', 'waste_type__name', 'quantity', 'unit', 'responsible', 'storage_location']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': _('Crear Registro'),
                'icon': 'add',
                'url': 'control residuos:waste_record_create',
                'modal': True,
            }
        ]
        context['url_export'] = 'control residuos:waste_record_export'
        
        context['actions'] = [
            {
                'name': 'edit',
                'icon': 'edit',
                'label': '',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'control residuos:waste_record_update',
                'modal': True
            },
            {
                'name': 'delete',
                'icon': 'delete',
                'label': '',
                'color': 'danger',
                'color2': 'white',
                'url': 'control residuos:waste_record_delete',
                'modal': True
            }
        ]
        
        # Configuración para toggle si el modelo tiene is_active
        # if hasattr(self.model, 'is_active'):
            # context['use_toggle'] = True
            # context['url_toggle'] = 'control residuos:toggle_active_status'
            # context['toggle_app_name'] = self.model._meta.app_label
            # context['toggle_model_name'] = self.model._meta.model_name
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('control residuos:waste_record_list')
        
        return context


class WasteRecordDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Mostrar detalles del registro de residuos"""
    permission_required = 'waste.view_wasterecord'
    model = WasteRecord
    context_object_name = 'record'
    template_name = 'waste/record_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Detalle de Registro de Residuo')
        context['entity'] = _('Registro de Residuo')
        
        # Obtener archivos multimedia relacionados
        context['media_files'] = self.object.files.all()
        
        # Agregar URLs para acciones
        context['edit_url'] = reverse('control residuos:record_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse('control residuos:record_delete', kwargs={'pk': self.object.pk})
        context['list_url'] = reverse('control residuos:waste_record_list')
        
        # Verificar si este residuo tiene algún destino registrado
        context['destinations'] = WasteDestination.objects.filter(
            waste_type=self.object.waste_type,
            area=self.object.area,
            departure_date__gte=self.object.record_date
        ).order_by('departure_date')[:5]  # Mostramos los 5 más recientes
        
        # URL para exportar este registro específico
        context['export_url'] = reverse('control residuos:record_export', kwargs={'pk': self.object.pk})
        
        return context


class WasteRecordCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear un nuevo registro de residuo
    La auditoría se maneja automáticamente por las señales post_save
    """
    permission_required = 'waste.add_wasterecord'
    model = WasteRecord
    form_class = WasteRecordForm
    template_name = 'waste/waste_form.html'
    
    def get_success_url(self):
        return reverse_lazy('control residuos:waste_record_list')
    
    def form_valid(self, form):
        # Guardar el registro - la auditoría se maneja por señales
        self.object = form.save()
        
        # Manejar archivos cargados
        files = self.request.FILES.getlist('media_files')
        for file in files:
            WasteMediaFile.objects.create(
                record=self.object,
                file=file,
                file_type=file.content_type,
                description=_('Archivo adjunto al registro de residuo')
            )
        
        messages.success(self.request, _('Registro de residuo creado con éxito'))
        
        # Verificar si es una solicitud AJAX
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Registro de residuo creado con éxito'),
                'redirect': self.get_success_url().resolve(self.request)
            })
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
                
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
            
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Registrar Residuo')
        context['entity'] = _('Registro de Residuo')
        context['list_url'] = reverse_lazy('control residuos:waste_record_list')
        context['action'] = 'add'
        context['is_upload'] = True  # Para habilitar la carga de archivos
        return context


class WasteRecordUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para actualizar información de un registro de residuo
    La auditoría es manejada automáticamente por las señales pre_save y post_save
    """
    permission_required = 'waste.change_wasterecord'
    model = WasteRecord
    form_class = WasteRecordForm
    template_name = 'core/create.html'
    
    def get_success_url(self):
        return reverse_lazy('control residuos:waste_record_list')
    
    def form_valid(self, form):
        # Guardar el registro - la auditoría se maneja por señales
        self.object = form.save()
        
        # Manejar archivos cargados
        files = self.request.FILES.getlist('media_files')
        for file in files:
            WasteMediaFile.objects.create(
                record=self.object,
                file=file,
                file_type=file.content_type,
                description=_('Archivo adjunto al registro de residuo')
            )
        
        messages.success(self.request, _('Registro de residuo actualizado con éxito'))
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Registro de residuo actualizado con éxito'),
                'redirect': self.get_success_url().resolve(self.request)
            })
            
        return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
                
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
            
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Registro de Residuo')
        context['entity'] = _('Registro de Residuo')
        context['list_url'] = reverse_lazy('control residuos:waste_record_list')
        context['action'] = 'edit'
        context['is_upload'] = True  # Para habilitar la carga de archivos
        
        # Obtener archivos multimedia ya existentes
        context['existing_files'] = self.object.files.all()
        
        return context


class WasteRecordDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Vista para eliminar un registro de residuo
    La auditoría es manejada automáticamente por la señal post_delete
    """
    permission_required = 'waste.delete_wasterecord'
    model = WasteRecord
    template_name = 'core/del.html'
    context_object_name = 'record'
    success_url = reverse_lazy('control residuos:waste_record_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Registro de Residuo')
        context['entity'] = _('Registro de Residuo')
        context['texto'] = f'¿Seguro de eliminar el registro de {self.object.waste_type.name} del {self.object.record_date}?'
        context['list_url'] = reverse_lazy('control residuos:waste_record_list')
        return context
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        try:
            # La auditoría se maneja automáticamente con la señal post_delete
            self.object.delete()
            messages.success(request, _('Registro de residuo eliminado con éxito'))
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': _('Registro de residuo eliminado con éxito'),
                    'redirect': self.success_url
                })
                
            return redirect(self.success_url)
            
        except Exception as e:
            # Capturar errores de integridad referencial
            error_message = _('No se puede eliminar el registro porque está siendo utilizado en otros registros')
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=400)
                
            messages.error(request, error_message)
            return redirect(self.success_url)

class WasteRecordExportView(GenericExportView):
    model = WasteRecord
    permission_required = 'waste.view_wasterecord'
    fields = [
        'record_date', 
        'area__name', 
        'waste_type__name', 
        'waste_type__get_category_display', 
        'quantity', 
        'get_unit_display', 
        'weight_kg', 
        'notes'
        ]
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ... configuraciones existentes ...
        
        # Agregar formatos disponibles
        context['export_formats'] = [
            {'format': 'csv', 'label': 'CSV'},
            {'format': 'pdf', 'label': 'PDF'},
            {'format': 'excel', 'label': 'Excel'}
        ]        
        return context
    


# class WasteRecordExportView(GenericExportView):
#     """
#     Vista para exportar registros de residuos en diferentes formatos
#     Soporta CSV, Excel y PDF con filtros aplicados
#     """
#     model = WasteRecord
#     fields_to_export = ['record_date', 'area__name', 'waste_type__name', 
#                        'waste_type__get_category_display', 'quantity', 
#                        'get_unit_display', 'weight_kg', 'notes']
#     permission_required = 'waste.view_wasterecord'
#     filename_prefix = 'waste_record'
    
#     def get_queryset(self):
#         """Get records with applied filters or a specific record"""
#         record_id = self.kwargs.get('pk')
        
#         if record_id:
#             return WasteRecord.objects.filter(id=record_id)
        
#         # Iniciar el queryset
#         queryset = WasteRecord.objects.all()
        
#         # Aplicar filtros similares a los de la vista de lista
#         area_id = self.request.GET.get('area', '')
#         if area_id and area_id.isdigit():
#             queryset = queryset.filter(area_id=area_id)
        
#         waste_type_id = self.request.GET.get('waste_type', '')
#         if waste_type_id and waste_type_id.isdigit():
#             queryset = queryset.filter(waste_type_id=waste_type_id)
        
#         waste_category = self.request.GET.get('waste_category', '')
#         if waste_category:
#             queryset = queryset.filter(waste_type__category=waste_category)
        
#         date_from = self.request.GET.get('date_from', '')
#         date_to = self.request.GET.get('date_to', '')
        
#         if date_from:
#             try:
#                 start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
#                 queryset = queryset.filter(record_date__gte=start_date)
#             except ValueError:
#                 pass
                
#         if date_to:
#             try:
#                 end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
#                 queryset = queryset.filter(record_date__lte=end_date)
#             except ValueError:
#                 pass
                
#         # Optimizar consultas con select_related
#         return queryset.select_related('area', 'waste_type').order_by('-record_date')
    
#     def export_pdf(self, data):
#         """Export waste records in PDF format with detailed information"""
#         if not data:
#             return HttpResponse(_("No se encontraron registros"), status=404)
        
#         # Create PDF file
#         buffer = BytesIO()
#         doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
#         elements = []
        
#         # PDF styles
#         styles = getSampleStyleSheet()
#         title_style = styles['Heading1']
#         section_style = styles['Heading2']
#         normal_style = styles['Normal']
        
#         # Document title
#         title = Paragraph(_("Informe de Registros de Residuos"), title_style)
#         elements.append(title)
#         elements.append(Spacer(1, 12))
        
#         # Filtros aplicados
#         filter_text = []
        
#         # Verificar filtros aplicados para mostrarlos en el informe
#         if self.request.GET.get('date_from') and self.request.GET.get('date_to'):
#             filter_text.append(f"{_('Periodo')}: {self.request.GET.get('date_from')} - {self.request.GET.get('date_to')}")
#         elif self.request.GET.get('date_from'):
#             filter_text.append(f"{_('Desde')}: {self.request.GET.get('date_from')}")
#         elif self.request.GET.get('date_to'):
#             filter_text.append(f"{_('Hasta')}: {self.request.GET.get('date_to')}")
            
#         if self.request.GET.get('area'):
#             area_name = CompanyArea.objects.filter(id=self.request.GET.get('area')).first()
#             if area_name:
#                 filter_text.append(f"{_('Área')}: {area_name.name}")
                
#         if self.request.GET.get('waste_type'):
#             waste_type_name = WasteType.objects.filter(id=self.request.GET.get('waste_type')).first()
#             if waste_type_name:
#                 filter_text.append(f"{_('Tipo de Residuo')}: {waste_type_name.name}")
                
#         if self.request.GET.get('waste_category'):
#             category_dict = dict(WasteType.CATEGORIES)
#             category_name = category_dict.get(self.request.GET.get('waste_category'))
#             if category_name:
#                 filter_text.append(f"{_('Categoría')}: {category_name}")
        
#         # Mostrar filtros aplicados
#         if filter_text:
#             elements.append(Paragraph(_("Filtros aplicados:"), normal_style))
#             for filter_line in filter_text:
#                 elements.append(Paragraph(f"• {filter_line}", normal_style))
#             elements.append(Spacer(1, 12))
        
#         # Fecha de generación del informe
#         elements.append(Paragraph(f"{_('Fecha de generación')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
#         elements.append(Spacer(1, 20))
        
#         # Crear tabla de registros
#         table_data = [
#             [_("Fecha"), _("Área"), _("Tipo de Residuo"), _("Categoría"), 
#              _("Cantidad"), _("Unidad"), _("Peso (kg)"), _("Notas")]
#         ]
        
#         # Inicializar variables para totales
#         total_by_category = {}
#         total_by_status = {}  # Inicialización de la variable total_by_status
#         total_by_treatment = {}  # Inicialización de la variable total_by_treatment
#         total_kg = 0
        
#         # Agregar registros a la tabla
#         for record in data:
#             category = record['waste_type__get_category_display']
#             weight = record['weight_kg'] or 0  # Manejar posibles valores None
            
#             # Acumular totales por categoría
#             if category not in total_by_category:
#                 total_by_category[category] = 0
#             total_by_category[category] += weight
#             total_kg += weight
            
#             # Agregar fila a la tabla
#             table_data.append([
#                 record['record_date'],
#                 record['area__name'],
#                 record['waste_type__name'],
#                 category,
#                 record['quantity'],
#                 record['get_unit_display'],
#                 f"{weight:.2f}",
#                 record['notes'] or ""
#             ])
        
#         # Establecer total_quantity para cálculos porcentuales
#         total_quantity = total_kg  # Definición de la variable total_quantity
        
#         # Crear la tabla con los datos
#         table = Table(table_data, repeatRows=1)
        
#         # Estilo de la tabla
#         table_style = TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('FONTSIZE', (0, 0), (-1, 0), 10),
#             ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#             ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#             ('GRID', (0, 0), (-1, -1), 1, colors.grey),
#             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#             ('ALIGN', (4, 1), (6, -1), 'RIGHT'),  # Alinear números a la derecha
#         ])
        
#         # Alternar colores de las filas
#         for i in range(1, len(table_data)):
#             if i % 2 == 0:
#                 table_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
        
#         table.setStyle(table_style)
#         elements.append(table)
        
#         # Agregar resúmenes
#         elements.append(PageBreak())
#         elements.append(Paragraph(_("Resúmenes Estadísticos"), title_style))
#         elements.append(Spacer(1, 20))
        
#         # 1. Resumen por categoría
#         elements.append(Paragraph(_("Residuos por Categoría"), section_style))
#         elements.append(Spacer(1, 10))
        
#         # Tabla de resumen por categoría
#         category_data = [
#             [_("Categoría"), _("Cantidad Total (kg)"), _("Porcentaje")]
#         ]
        
#         for category, amount in total_by_category.items():
#             percentage = (amount / total_quantity) * 100 if total_quantity > 0 else 0
#             category_data.append([
#                 category,
#                 f"{amount:.2f}",
#                 f"{percentage:.2f}%"
#             ])
        
#         # Agregar fila de total
#         category_data.append([
#             _("TOTAL"),
#             f"{total_quantity:.2f}",
#             "100.00%"
#         ])
        
#         # Crear tabla de resumen por categoría
#         category_table = Table(category_data, colWidths=[250, 100, 100])
        
#         # Estilo de la tabla de resumen
#         category_style = TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('ALIGN', (1, 1), (2, -1), 'RIGHT'),  # Alinear números a la derecha
#             ('GRID', (0, 0), (-1, -1), 1, colors.grey),
#             ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Fila de total
#             ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Fila de total en negrita
#         ])
        
#         # Alternar colores para filas de categorías
#         for i in range(1, len(category_data)-1):
#             if i % 2 == 0:
#                 category_style.add('BACKGROUND', (0, i), (-1, i), colors.beige)
#             else:
#                 category_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
        
#         category_table.setStyle(category_style)
#         elements.append(category_table)
        
#         # Nota: Los siguientes bloques se mantienen comentados ya que parece que los registros (WasteRecord)
#         # no tienen campo 'status' ni 'treatment_method'. Si se desea incluir estos resúmenes, 
#         # se debe modificar el modelo o adaptar la vista para incluir estos datos.
        
#         """
#         # 2. Resumen por estado
#         elements.append(Spacer(1, 30))
#         elements.append(Paragraph(_("Residuos por Estado"), section_style))
#         elements.append(Spacer(1, 10))
        
#         # Tabla de resumen por estado
#         status_data = [
#             [_("Estado"), _("Cantidad Total (kg)"), _("Porcentaje")]
#         ]
        
#         for status, amount in total_by_status.items():
#             percentage = (amount / total_quantity) * 100 if total_quantity > 0 else 0
#             status_data.append([
#                 status,
#                 f"{amount:.2f}",
#                 f"{percentage:.2f}%"
#             ])
        
#         # Agregar fila de total
#         status_data.append([
#             _("TOTAL"),
#             f"{total_quantity:.2f}",
#             "100.00%"
#         ])
        
#         # Crear tabla de resumen por estado
#         status_table = Table(status_data, colWidths=[250, 100, 100])
        
#         # Estilo de la tabla de resumen
#         status_style = TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('ALIGN', (1, 1), (2, -1), 'RIGHT'),  # Alinear números a la derecha
#             ('GRID', (0, 0), (-1, -1), 1, colors.grey),
#             ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Fila de total
#             ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Fila de total en negrita
#         ])
        
#         # Alternar colores para filas de estados
#         for i in range(1, len(status_data)-1):
#             if i % 2 == 0:
#                 status_style.add('BACKGROUND', (0, i), (-1, i), colors.beige)
#             else:
#                 status_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
        
#         status_table.setStyle(status_style)
#         elements.append(status_table)
        
#         # 3. Resumen por método de tratamiento
#         elements.append(Spacer(1, 30))
#         elements.append(Paragraph(_("Residuos por Método de Tratamiento"), section_style))
#         elements.append(Spacer(1, 10))
        
#         # Tabla de resumen por método
#         treatment_data = [
#             [_("Método de Tratamiento"), _("Cantidad Total (kg)"), _("Porcentaje")]
#         ]
        
#         for treatment, amount in total_by_treatment.items():
#             percentage = (amount / total_quantity) * 100 if total_quantity > 0 else 0
#             treatment_data.append([
#                 treatment,
#                 f"{amount:.2f}",
#                 f"{percentage:.2f}%"
#             ])
        
#         # Agregar fila de total
#         treatment_data.append([
#             _("TOTAL"),
#             f"{total_quantity:.2f}",
#             "100.00%"
#         ])
        
#         # Crear tabla de resumen por método
#         treatment_table = Table(treatment_data, colWidths=[250, 100, 100])
        
#         # Estilo de la tabla de resumen
#         treatment_style = TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('ALIGN', (1, 1), (2, -1), 'RIGHT'),  # Alinear números a la derecha
#             ('GRID', (0, 0), (-1, -1), 1, colors.grey),
#             ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Fila de total
#             ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Fila de total en negrita
#         ])
        
#         # Alternar colores para filas de métodos
#         for i in range(1, len(treatment_data)-1):
#             if i % 2 == 0:
#                 treatment_style.add('BACKGROUND', (0, i), (-1, i), colors.beige)
#             else:
#                 treatment_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
        
#         treatment_table.setStyle(treatment_style)
#         elements.append(treatment_table)
#         """
        
#         # Construir el PDF
#         doc.build(elements)
        
#         # Crear respuesta HTTP
#         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
#         # Determinar nombre de archivo según si es un destino específico o una lista
#         if self.kwargs.get('pk'):
#             filename = f"{self.filename_prefix}_id{self.kwargs.get('pk')}_{timestamp}.pdf"
#         else:
#             filename = f"{self.filename_prefix}_report_{timestamp}.pdf"
        
#         response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
#         # Cerrar buffer
#         buffer.close()
        
#         return response
    

# # =========== WASTE DASHBOARD VIEW ===========

# class WasteDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
#     """
#     Vista de panel de control para análisis de residuos
#     Muestra gráficos y estadísticas sobre la generación y disposición de residuos
#     """
#     permission_required = 'waste.view_wasterecord'
#     template_name = 'waste/dashboard.html'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         today = timezone.now().date()
        
#         # Definir períodos de tiempo para análisis
#         month_start = today.replace(day=1)
#         last_month_start = (month_start - timedelta(days=1)).replace(day=1)
#         last_month_end = month_start - timedelta(days=1)
#         year_start = today.replace(month=1, day=1)
        
#         # Obtener todas las áreas activas
#         areas = CompanyArea.objects.filter(is_active=True)
        
#         # Obtener todos los tipos de residuos activos
#         waste_types = WasteType.objects.filter(is_active=True)
        
#         # 1. Estadísticas básicas
#         total_records = WasteRecord.objects.count()
#         records_this_month = WasteRecord.objects.filter(record_date__gte=month_start).count()
        
#         total_destinations = WasteDestination.objects.count()
#         destinations_this_month = WasteDestination.objects.filter(departure_date__gte=month_start).count()
        
#         hazardous_waste = WasteRecord.objects.filter(
#             waste_type__category__in=['HAZARDOUS', 'SPECIAL']
#         ).aggregate(
#             total=Sum(Case(
#                 When(unit='KG', then=F('quantity')),
#                 When(unit='TON', then=F('quantity')*1000),
#                 default=F('quantity'),
#                 output_field=DecimalField()
#             ))
#         )['total'] or 0
        
#         recyclable_waste = WasteRecord.objects.filter(
#             waste_type__category='RECYCLABLE'
#         ).aggregate(
#             total=Sum(Case(
#                 When(unit='KG', then=F('quantity')),
#                 When(unit='TON', then=F('quantity')*1000),
#                 default=F('quantity'),
#                 output_field=DecimalField()
#             ))
#         )['total'] or 0
        
#         # 2. Datos para gráficos
        
#         # 2.1 Generación mensual de residuos (último año)
#         monthly_data = []
#         for i in range(12):
#             month_date = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
#             month_end = (month_date.replace(month=month_date.month+1) if month_date.month < 12 
#                         else month_date.replace(year=month_date.year+1, month=1)) - timedelta(days=1)
            
#             monthly_total = WasteRecord.objects.filter(
#                 record_date__gte=month_date,
#                 record_date__lte=month_end
#             ).aggregate(
#                 total=Sum(Case(
#                     When(unit='KG', then=F('quantity')),
#                     When(unit='TON', then=F('quantity')*1000),
#                     default=F('quantity'),
#                     output_field=DecimalField()
#                 ))
#             )['total'] or 0
            
#             monthly_data.append({
#                 'month': month_date.strftime('%b %Y'),
#                 'total': float(monthly_total),
#                 'date': month_date
#             })
        
#         monthly_data.reverse()  # Ordenar cronológicamente
        
#         # 2.2 Distribución por categorías (últimos 3 meses)
#         three_months_ago = (today - timedelta(days=90))
        
#         category_data = []
#         for category, label in WasteType.CATEGORIES:
#             category_total = WasteRecord.objects.filter(
#                 record_date__gte=three_months_ago,
#                 waste_type__category=category
#             ).aggregate(
#                 total=Sum(Case(
#                     When(unit='KG', then=F('quantity')),
#                     When(unit='TON', then=F('quantity')*1000),
#                     default=F('quantity'),
#                     output_field=DecimalField()
#                 ))
#             )['total'] or 0
            
#             category_data.append({
#                 'category': label,
#                 'code': category,
#                 'total': float(category_total)
#             })
        
#         # 2.3 Distribución por área (mes actual)
#         area_data = []
#         for area in areas:
#             area_total = WasteRecord.objects.filter(
#                 record_date__gte=month_start,
#                 area=area
#             ).aggregate(
#                 total=Sum(Case(
#                     When(unit='KG', then=F('quantity')),
#                     When(unit='TON', then=F('quantity')*1000),
#                     default=F('quantity'),
#                     output_field=DecimalField()
#                 ))
#             )['total'] or 0
            
#             area_data.append({
#                 'area': area.name,
#                 'total': float(area_total)
#             })
        
#         # Ordenar por total descendente y tomar los 5 mayores
#         area_data.sort(key=lambda x: x['total'], reverse=True)
#         area_data = area_data[:5]
        
#         # 2.4 Distribución por método de tratamiento (año actual)
#         treatment_data = []
#         for method, label in WasteDestination.TREATMENT_METHODS:
#             treatment_total = WasteDestination.objects.filter(
#                 departure_date__gte=year_start,
#                 treatment_method=method
#             ).aggregate(
#                 total=Sum(Case(
#                     When(unit='KG', then=F('quantity')),
#                     When(unit='TON', then=F('quantity')*1000),
#                     default=F('quantity'),
#                     output_field=DecimalField()
#                 ))
#             )['total'] or 0
            
#             treatment_data.append({
#                 'method': label,
#                 'code': method,
#                 'total': float(treatment_total)
#             })
        
#         # 2.5 Comparativa mes actual vs mes anterior
#         current_month_total = WasteRecord.objects.filter(
#             record_date__gte=month_start
#         ).aggregate(
#             total=Sum(Case(
#                 When(unit='KG', then=F('quantity')),
#                 When(unit='TON', then=F('quantity')*1000),
#                 default=F('quantity'),
#                 output_field=DecimalField()
#             ))
#         )['total'] or 0
        
#         last_month_total = WasteRecord.objects.filter(
#             record_date__gte=last_month_start,
#             record_date__lte=last_month_end
#         ).aggregate(
#             total=Sum(Case(
#                 When(unit='KG', then=F('quantity')),
#                 When(unit='TON', then=F('quantity')*1000),
#                 default=F('quantity'),
#                 output_field=DecimalField()
#             ))
#         )['total'] or 0
        
#         # Calcular variación porcentual
#         if last_month_total > 0:
#             month_variation = ((current_month_total - last_month_total) / last_month_total) * 100
#         else:
#             month_variation = 100 if current_month_total > 0 else 0
        
#         # 3. Tendencias
        
#         # 3.1 Evolución de residuos peligrosos vs. no peligrosos (últimos 6 meses)
#         hazardous_trend = []
#         non_hazardous_trend = []
        
#         for i in range(6):
#             month_date = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
#             month_end = (month_date.replace(month=month_date.month+1) if month_date.month < 12 
#                         else month_date.replace(year=month_date.year+1, month=1)) - timedelta(days=1)
            
#             # Peligrosos
#             hazardous_month = WasteRecord.objects.filter(
#                 record_date__gte=month_date,
#                 record_date__lte=month_end,
#                 waste_type__category__in=['HAZARDOUS', 'SPECIAL']
#             ).aggregate(
#                 total=Sum(Case(
#                     When(unit='KG', then=F('quantity')),
#                     When(unit='TON', then=F('quantity')*1000),
#                     default=F('quantity'),
#                     output_field=DecimalField()
#                 ))
#             )['total'] or 0
            
#             # No peligrosos
#             non_hazardous_month = WasteRecord.objects.filter(
#                 record_date__gte=month_date,
#                 record_date__lte=month_end,
#                 waste_type__category__in=['ORDINARY', 'RECYCLABLE']
#             ).aggregate(
#                 total=Sum(Case(
#                     When(unit='KG', then=F('quantity')),
#                     When(unit='TON', then=F('quantity')*1000),
#                     default=F('quantity'),
#                     output_field=DecimalField()
#                 ))
#             )['total'] or 0
            
#             month_label = month_date.strftime('%b %Y')
            
#             hazardous_trend.append({
#                 'month': month_label,
#                 'total': float(hazardous_month)
#             })
            
#             non_hazardous_trend.append({
#                 'month': month_label,
#                 'total': float(non_hazardous_month)
#             })
        
#         # Invertir para orden cronológico
#         hazardous_trend.reverse()
#         non_hazardous_trend.reverse()
        
#         # Preparar contexto para la plantilla
#         context['stats'] = {
#             'total_records': total_records,
#             'records_this_month': records_this_month,
#             'total_destinations': total_destinations,
#             'destinations_this_month': destinations_this_month,
#             'hazardous_waste': hazardous_waste,
#             'recyclable_waste': recyclable_waste,
#             'current_month': month_start.strftime('%B %Y'),
#             'last_month': last_month_start.strftime('%B %Y'),
#             'current_month_total': current_month_total,
#             'last_month_total': last_month_total,
#             'month_variation': month_variation,
#         }
        
#         context['charts'] = {
#             'monthly_data': monthly_data,
#             'category_data': category_data,
#             'area_data': area_data,
#             'treatment_data': treatment_data,
#             'hazardous_trend': hazardous_trend,
#             'non_hazardous_trend': non_hazardous_trend,
#         }
        
#         # Datos para filtros
#         context['areas'] = areas
#         context['waste_types'] = waste_types
#         context['categories'] = WasteType.CATEGORIES
#         context['treatment_methods'] = WasteDestination.TREATMENT_METHODS
        
#         # URLs para acciones
#         context['record_list_url'] = reverse('control residuos:waste_record_list')
#         context['destination_list_url'] = reverse('control residuos:destination_list')
#         context['record_export_url'] = reverse('control residuos:record_export')
#         context['destination_export_url'] = reverse('control residuos:destination_export')
        
#         return context

# # =========== WASTE TYPE AND MANAGER VIEWS ===========

# class WasteTypeListView(OptimizedSecureListView):
#     """Vista para listar tipos de residuos"""
#     permission_required = 'waste.view_wastetype'
#     model = WasteType
#     template_name = 'core/list.html'
    
#     # Configuración de búsqueda y ordenamiento
#     search_fields = ['name', 'code', 'description']
#     order_by = ['category', 'name']
    
#     # Atributos específicos
#     title = _('Listado de Tipos de Residuos')
#     entity = _('Tipo de Residuo')
    
#     def get_queryset(self):
#         queryset = super().get_queryset()
        
#         # Filtro por categoría
#         category = self.request.GET.get('category', '')
#         if category:
#             queryset = queryset.filter(category=category)
            
#         # Filtro por tratamiento especial
#         special = self.request.GET.get('special', '')
#         if special == 'yes':
#             queryset = queryset.filter(requires_special_treatment=True)
#         elif special == 'no':
#             queryset = queryset.filter(requires_special_treatment=False)
            
#         return queryset
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
        
#         # Configuración específica para esta vista
#         context['headers'] = ['CÓDIGO', 'NOMBRE', 'CATEGORÍA', 'COLOR', 'TRAT. ESPECIAL']
#         context['fields'] = ['code', 'name', 'get_category_display', 'identification_color', 'requires_special_treatment']
        
#         # Configuración de botones y acciones
#         context['Btn_Add'] = [
#             {
#                 'name': 'add',
#                 'label': _('Crear Tipo de Residuo'),
#                 'icon': 'add',
#                 'url': 'control residuos:type_create',
#                 'modal': True,
#             }
#         ]
        
#         context['actions'] = [
#             {
#                 'name': 'view',
#                 'label': '',
#                 'icon': 'visibility',
#                 'color': 'info',
#                 'color2': 'white',
#                 'title': _('Ver Tipo de Residuo'),
#                 'url': 'control residuos:type_detail',
#                 'modal': False
#             },
#             {
#                 'name': 'edit',
#                 'label': '',
#                 'icon': 'edit',
#                 'color': 'primary',
#                 'color2': 'white',
#                 'title': _('Editar Tipo de Residuo'),
#                 'url': 'control residuos:type_update',
#                 'modal': True
#             },
#             {
#                 'name': 'del',
#                 'label': '',
#                 'icon': 'delete',
#                 'color': 'danger',
#                 'color2': 'white',
#                 'title': _('Eliminar Tipo de Residuo'),
#                 'url': 'control residuos:type_delete',
#                 'modal': True
#             },
#         ]
        
#         # Filtros adicionales específicos para tipos de residuos
#         context['custom_filters'] = {
#             'category': [
#                 {'value': category[0], 'label': category[1]} 
#                 for category in WasteType.CATEGORIES
#             ],
#             'special': [
#                 {'value': 'yes', 'label': _('Requiere tratamiento especial')},
#                 {'value': 'no', 'label': _('No requiere tratamiento especial')}
#             ]
#         }
        
#         # URL de cancelación
#         context['cancel_url'] = reverse_lazy('control residuos:type_list')
        
#         return context

# class WasteManagerListView(OptimizedSecureListView):
#     """Vista para listar gestores de residuos"""
#     permission_required = 'waste.view_wastemanager'
#     model = WasteManager
#     template_name = 'core/list.html'
    
#     # Configuración de búsqueda y ordenamiento
#     search_fields = ['name', 'tax_id', 'address', 'city', 'email']
#     order_by = ['name']
    
#     # Atributos específicos
#     title = _('Listado de Gestores de Residuos')
#     entity = _('Gestor de Residuos')
    
#     def get_queryset(self):
#         queryset = super().get_queryset()
        
#         # Filtro por estado (activo/inactivo)
#         status = self.request.GET.get('status', '')
#         if status == 'active':
#             queryset = queryset.filter(is_active=True)
#         elif status == 'inactive':
#             queryset = queryset.filter(is_active=False)
            
#         # Filtro por ciudad
#         city = self.request.GET.get('city', '')
#         if city:
#             queryset = queryset.filter(city__icontains=city)
            
#         return queryset
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
        
#         # Configuración específica para esta vista
#         context['headers'] = ['NOMBRE', 'NIT', 'CIUDAD', 'TELÉFONO', 'EMAIL', 'LICENCIA', 'ACTIVO']
#         context['fields'] = ['name', 'tax_id', 'city', 'phone', 'email', 'environmental_license', 'is_active']
        
#         # Configuración de botones y acciones
#         context['Btn_Add'] = [
#             {
#                 'name': 'add',
#                 'label': _('Crear Gestor'),
#                 'icon': 'add',
#                 'url': 'control residuos:manager_create',
#                 'modal': True,
#             }
#         ]
        
#         context['actions'] = [
#             {
#                 'name': 'view',
#                 'label': '',
#                 'icon': 'visibility',
#                 'color': 'info',
#                 'color2': 'white',
#                 'title': _('Ver Gestor'),
#                 'url': 'control residuos:manager_detail',
#                 'modal': False
#             },
#             {
#                 'name': 'edit',
#                 'label': '',
#                 'icon': 'edit',
#                 'color': 'primary',
#                 'color2': 'white',
#                 'title': _('Editar Gestor'),
#                 'url': 'control residuos:manager_update',
#                 'modal': True
#             },
#             {
#                 'name': 'del',
#                 'label': '',
#                 'icon': 'delete',
#                 'color': 'danger',
#                 'color2': 'white',
#                 'title': _('Eliminar Gestor'),
#                 'url': 'control residuos:manager_delete',
#                 'modal': True
#             },
#         ]
        
#         # Filtros adicionales específicos para gestores
#         context['custom_filters'] = {
#             'status': [
#                 {'value': 'active', 'label': _('Activos')},
#                 {'value': 'inactive', 'label': _('Inactivos')}
#             ]
#         }
        
#         # Lista de ciudades únicas para filtro
#         cities = WasteManager.objects.values_list('city', flat=True).distinct().order_by('city')
#         if cities:
#             context['custom_filters']['city'] = [
#                 {'value': city, 'label': city}
#                 for city in cities
#             ]
        
#         # URL de cancelación
#         context['cancel_url'] = reverse_lazy('control residuos:manager_list')
        
#         return context

# # =========== WASTE REPORT VIEWS ===========

# class WasteReportView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
#     """
#     Vista para generar informes personalizados de residuos
#     """
#     permission_required = 'waste.view_wasterecord'
#     template_name = 'waste/report_form.html'
#     form_class = WasteRecordForm  # Usar un formulario personalizado para los parámetros del informe
    
#     def get_form_class(self):
#         # Este método debe retornar un formulario personalizado para los parámetros de informe
#         # Por simplificación, aquí usamos el WasteRecordForm existente, pero se debería crear uno específico
#         return WasteRecordForm
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Generar Informe de Residuos')
#         context['entity'] = _('Informe')
        
#         # Obtener datos para los filtros
#         context['areas'] = CompanyArea.objects.filter(is_active=True).order_by('name')
#         context['waste_types'] = WasteType.objects.filter(is_active=True).order_by('name')
#         context['waste_categories'] = WasteType.CATEGORIES
#         context['managers'] = WasteManager.objects.filter(is_active=True).order_by('name')
        
#         # Obtener fechas predefinidas
#         today = timezone.now().date()
#         context['predefined_dates'] = {
#             'today': today.strftime('%Y-%m-%d'),
#             'yesterday': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
#             'week_start': (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d'),
#             'month_start': today.replace(day=1).strftime('%Y-%m-%d'),
#             'quarter_start': today.replace(month=((today.month-1)//3)*3+1, day=1).strftime('%Y-%m-%d'),
#             'year_start': today.replace(month=1, day=1).strftime('%Y-%m-%d'),
#         }
        
#         return context
    
#     def form_valid(self, form):
#         # Construir URL para el informe con los parámetros seleccionados
#         report_type = self.request.POST.get('report_type', 'records')
        
#         # Determinar la URL de exportación según el tipo de informe
#         if report_type == 'records':
#             export_url = reverse('control residuos:record_export')
#         elif report_type == 'destinations':
#             export_url = reverse('control residuos:destination_export')
#         else:
#             export_url = reverse('control residuos:dashboard')
            
#         # Construir parámetros de consulta
#         params = {}
        
#         # Filtros comunes
#         date_from = self.request.POST.get('date_from')
#         date_to = self.request.POST.get('date_to')
#         area = self.request.POST.get('area')
#         waste_type = self.request.POST.get('waste_type')
#         waste_category = self.request.POST.get('waste_category')
        
#         if date_from:
#             params['date_from'] = date_from
#         if date_to:
#             params['date_to'] = date_to
#         if area:
#             params['area'] = area
#         if waste_type:
#             params['waste_type'] = waste_type
#         if waste_category:
#             params['waste_category'] = waste_category
            
#         # Filtros específicos para destinos
#         if report_type == 'destinations':
#             manager = self.request.POST.get('manager')
#             status = self.request.POST.get('status')
#             treatment_method = self.request.POST.get('treatment_method')
            
#             if manager:
#                 params['manager'] = manager
#             if status:
#                 params['status'] = status
#             if treatment_method:
#                 params['treatment_method'] = treatment_method
                
#             # Renombrar parámetros de fecha para destinos
#             if 'date_from' in params:
#                 params['departure_from'] = params.pop('date_from')
#             if 'date_to' in params:
#                 params['departure_to'] = params.pop('date_to')
                
#         # Formato de exportación
#         export_format = self.request.POST.get('export_format', 'pdf')
#         params['format'] = export_format
        
#         # Construir URL completa
#         query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
#         redirect_url = f"{export_url}?{query_string}"
        
#         # Redireccionar a la URL de exportación
#         return HttpResponseRedirect(redirect_url)

# # =========== WASTE ANALYTICS VIEW ===========

# class WasteAnalyticsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
#     """
#     Vista para análisis avanzados de datos de residuos
#     Proporciona métricas, tendencias y comparativas detalladas
#     """
#     permission_required = 'waste.view_wasterecord'
#     template_name = 'waste/analytics.html'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         today = timezone.now().date()
        
#         # Obtener parámetros de filtro
#         date_from = self.request.GET.get('date_from')
#         date_to = self.request.GET.get('date_to')
#         period = self.request.GET.get('period', 'month')  # default: month
#         compare_with = self.request.GET.get('compare_with')  # previous, year_ago, none
        
#         # Establecer fechas por defecto si no se proporcionan
#         if not date_to:
#             date_to = today
#         else:
#             try:
#                 date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
#             except ValueError:
#                 date_to = today
        
#         if not date_from:
#             # Determinar fecha de inicio basada en el período seleccionado
#             if period == 'week':
#                 date_from = date_to - timedelta(days=7)
#             elif period == 'month':
#                 if date_to.month == 1:
#                     date_from = date_to.replace(year=date_to.year-1, month=12, day=1)
#                 else:
#                     date_from = date_to.replace(month=date_to.month-1, day=1)
#             elif period == 'quarter':
#                 quarter_start_month = ((date_to.month-1)//3)*3+1
#                 date_from = date_to.replace(month=quarter_start_month, day=1)
#             elif period == 'year':
#                 date_from = date_to.replace(month=1, day=1)
#             else:  # custom - default to 30 days
#                 date_from = date_to - timedelta(days=30)
#         else:
#             try:
#                 date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
#             except ValueError:
#                 date_from = date_to - timedelta(days=30)
        
#         # Calcular fechas para período de comparación
#         if compare_with == 'previous':
#             # Calcular el período anterior del mismo tamaño
#             delta = date_to - date_from
#             compare_to = date_from - timedelta(days=1)
#             compare_from = compare_to - delta
#         elif compare_with == 'year_ago':
#             # Mismo período del año anterior
#             compare_from = date_from.replace(year=date_from.year-1)
#             compare_to = date_to.replace(year=date_to.year-1)
#         else:
#             compare_from = None
#             compare_to = None
        
#         # 1. Métricas generales para el período seleccionado
        
#         # 1.1 Total de residuos generados en KG
#         total_waste = WasteRecord.objects.filter(
#             record_date__gte=date_from,
#             record_date__lte=date_to
#         ).aggregate(
#             total=Sum(Case(
#                 When(unit='KG', then=F('quantity')),
#                 When(unit='TON', then=F('quantity')*1000),
#                 default=F('quantity'),
#                 output_field=DecimalField()
#             ))
#         )['total'] or 0
        
#         # 1.2 Desglose por categorías
#         category_totals = {}
#         for category, label in WasteType.CATEGORIES:
#             category_total = WasteRecord.objects.filter(
#                 record_date__gte=date_from,
#                 record_date__lte=date_to,
#                 waste_type__category=category
#             ).aggregate(
#                 total=Sum(Case(
#                     When(unit='KG', then=F('quantity')),
#                     When(unit='TON', then=F('quantity')*1000),
#                     default=F('quantity'),
#                     output_field=DecimalField()
#                 ))
#             )['total'] or 0
            
#             category_totals[category] = {
#                 'label': label,
#                 'total': float(category_total),
#                 'percentage': (float(category_total) / float(total_waste) * 100) if total_waste > 0 else 0
#             }
        
#         # 1.3 Métricas para período de comparación si es necesario
#         if compare_from and compare_to:
#             compare_total = WasteRecord.objects.filter(
#                 record_date__gte=compare_from,
#                 record_date__lte=compare_to
#             ).aggregate(
#                 total=Sum(Case(
#                     When(unit='KG', then=F('quantity')),
#                     When(unit='TON', then=F('quantity')*1000),
#                     default=F('quantity'),
#                     output_field=DecimalField()
#                 ))
#             )['total'] or 0
            
#             # Calcular variación porcentual
#             if compare_total > 0:
#                 variation = ((total_waste - compare_total) / compare_total) * 100
#             else:
#                 variation = 100 if total_waste > 0 else 0
                
#             # Variación por categorías
#             category_variations = {}
#             for category, label in WasteType.CATEGORIES:
#                 compare_category = WasteRecord.objects.filter(
#                     record_date__gte=compare_from,
#                     record_date__lte=compare_to,
#                     waste_type__category=category
#                 ).aggregate(
#                     total=Sum(Case(
#                         When(unit='KG', then=F('quantity')),
#                         When(unit='TON', then=F('quantity')*1000),
#                         default=F('quantity'),
#                         output_field=DecimalField()
#                     ))
#                 )['total'] or 0
                
#                 current = float(category_totals[category]['total'])
#                 previous = float(compare_category)
                
#                 if previous > 0:
#                     cat_variation = ((current - previous) / previous) * 100
#                 else:
#                     cat_variation = 100 if current > 0 else 0
                    
#                 category_variations[category] = {
#                     'label': label,
#                     'current': current,
#                     'previous': previous,
#                     'variation': cat_variation
#                 }
#         else:
#             compare_total = None
#             variation = None
#             category_variations = None
        
#         # 2. Análisis por tipo de residuo
        
#         # Obtener los 10 tipos de residuos más comunes en el período
#         top_waste_types = WasteRecord.objects.filter(
#             record_date__gte=date_from,
#             record_date__lte=date_to
#         ).values(
#             'waste_type__name', 
#             'waste_type__category'
#         ).annotate(
#             total=Sum(Case(
#                 When(unit='KG', then=F('quantity')),
#                 When(unit='TON', then=F('quantity')*1000),
#                 default=F('quantity'),
#                 output_field=DecimalField()
#             ))
#         ).order_by('-total')[:10]
        
#         # Convertir categorías a etiquetas
#         category_dict = dict(WasteType.CATEGORIES)
#         for item in top_waste_types:
#             item['category_label'] = category_dict.get(item['waste_type__category'], '')
#             item['total'] = float(item['total'])
            
#         # 3. Análisis por área
        
#         # Obtener las áreas con más generación de residuos
#         top_areas = WasteRecord.objects.filter(
#             record_date__gte=date_from,
#             record_date__lte=date_to
#         ).values(
#             'area__name'
#         ).annotate(
#             total=Sum(Case(
#                 When(unit='KG', then=F('quantity')),
#                 When(unit='TON', then=F('quantity')*1000),
#                 default=F('quantity'),
#                 output_field=DecimalField()
#             ))
#         ).order_by('-total')[:10]
        
#         for item in top_areas:
#             item['total'] = float(item['total'])
#             item['percentage'] = (item['total'] / float(total_waste) * 100) if total_waste > 0 else 0
        
#         # 4. Análisis de tendencias
        
#         # 4.1 Determinar la unidad de tiempo para la tendencia según el período seleccionado
#         time_unit = 'day'
#         if period in ['year', 'quarter'] or (date_to - date_from).days > 90:
#             time_unit = 'month'
#         elif period == 'month' or (date_to - date_from).days > 14:
#             time_unit = 'week'
            
#         # 4.2 Obtener datos de tendencia para el período principal
#         trend_data = []
        
#         if time_unit == 'day':
#             # Tendencia diaria
#             current_date = date_from
#             while current_date <= date_to:
#                 day_total = WasteRecord.objects.filter(
#                     record_date=current_date
#                 ).aggregate(
#                     total=Sum(Case(
#                         When(unit='KG', then=F('quantity')),
#                         When(unit='TON', then=F('quantity')*1000),
#                         default=F('quantity'),
#                         output_field=DecimalField()
#                     ))
#                 )['total'] or 0
                
#                 trend_data.append({
#                     'date': current_date.strftime('%Y-%m-%d'),
#                     'label': current_date.strftime('%d %b'),
#                     'total': float(day_total)
#                 })
                
#                 current_date += timedelta(days=1)
                
#         elif time_unit == 'week':
#             # Tendencia semanal
#             current_date = date_from
#             while current_date <= date_to:
#                 # Calcular inicio y fin de la semana
#                 week_start = current_date
#                 week_end = min(current_date + timedelta(days=6), date_to)
                
#                 week_total = WasteRecord.objects.filter(
#                     record_date__gte=week_start,
#                     record_date__lte=week_end
#                 ).aggregate(
#                     total=Sum(Case(
#                         When(unit='KG', then=F('quantity')),
#                         When(unit='TON', then=F('quantity')*1000),
#                         default=F('quantity'),
#                         output_field=DecimalField()
#                     ))
#                 )['total'] or 0
                
#                 trend_data.append({
#                     'date': week_start.strftime('%Y-%m-%d'),
#                     'label': f"{week_start.strftime('%d %b')} - {week_end.strftime('%d %b')}",
#                     'total': float(week_total)
#                 })
                
#                 current_date += timedelta(days=7)
                
#         elif time_unit == 'month':
#             # Tendencia mensual
#             current_date = date_from.replace(day=1)
#             while current_date <= date_to:
#                 # Calcular fin de mes
#                 if current_date.month == 12:
#                     next_month = current_date.replace(year=current_date.year+1, month=1)
#                 else:
#                     next_month = current_date.replace(month=current_date.month+1)
                    
#                 month_end = next_month - timedelta(days=1)
#                 month_end = min(month_end, date_to)
                
#                 month_total = WasteRecord.objects.filter(
#                     record_date__gte=current_date,
#                     record_date__lte=month_end
#                 ).aggregate(
#                     total=Sum(Case(
#                         When(unit='KG', then=F('quantity')),
#                         When(unit='TON', then=F('quantity')*1000),
#                         default=F('quantity'),
#                         output_field=DecimalField()
#                     ))
#                 )['total'] or 0
                
#                 trend_data.append({
#                     'date': current_date.strftime('%Y-%m-%d'),
#                     'label': current_date.strftime('%b %Y'),
#                     'total': float(month_total)
#                 })
                
#                 # Avanzar al siguiente mes
#                 if current_date.month == 12:
#                     current_date = current_date.replace(year=current_date.year+1, month=1)
#                 else:
#                     current_date = current_date.replace(month=current_date.month+1)
        
#         # 5. Preparar los datos para el informe
#         context.update({
#             'title': _('Análisis de Residuos'),
#             'subtitle': f"{date_from.strftime('%d/%m/%Y')} - {date_to.strftime('%d/%m/%Y')}",
#             'period': period,
#             'date_from': date_from,
#             'date_to': date_to,
#             'compare_with': compare_with,
#             'compare_from': compare_from,
#             'compare_to': compare_to,
            
#             # Datos calculados
#             'total_waste': float(total_waste),
#             'compare_total': float(compare_total) if compare_total is not None else None,
#             'variation': variation,
#             'category_totals': category_totals,
#             'category_variations': category_variations,
#             'top_waste_types': list(top_waste_types),
#             'top_areas': list(top_areas),
#             'trend_data': trend_data,
#             'time_unit': time_unit,
            
#             # Datos para filtros
#             'categories': WasteType.CATEGORIES,
#             'areas': CompanyArea.objects.filter(is_active=True).order_by('name'),
#             'waste_types': WasteType.objects.filter(is_active=True).order_by('category', 'name'),
            
#             # Otros datos de contexto
#             'export_url': reverse('control residuos:record_export'),
#         })
        
#         return context
# #  filas
#         for i in range(1, len(table_data)):
#             if i % 2 == 0:
#                 table_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
        
#         table.setStyle(table_style)
#         elements.append(table)
        
#         # Agregar resumen por categoría
#         elements.append(Spacer(1, 30))
#         elements.append(Paragraph(_("Resumen por Categoría"), section_style))
#         elements.append(Spacer(1, 10))
        
#         # Tabla de resumen
#         summary_data = [
#             [_("Categoría"), _("Peso Total (kg)"), _("Porcentaje")]
#         ]
        
#         for category, weight in total_by_category.items():
#             percentage = (weight / total_kg) * 100 if total_kg > 0 else 0
#             summary_data.append([
#                 category,
#                 f"{weight:.2f}",
#                 f"{percentage:.2f}%"
#             ])
        
#         # Agregar fila de total
#         summary_data.append([
#             _("TOTAL"),
#             f"{total_kg:.2f}",
#             "100.00%"
#         ])
        
#         # Crear tabla de resumen
#         summary_table = Table(summary_data, colWidths=[300, 100, 100])
        
#         # Estilo de la tabla de resumen
#         summary_style = TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('ALIGN', (1, 1), (2, -1), 'RIGHT'),  # Alinear números a la derecha
#             ('GRID', (0, 0), (-1, -1), 1, colors.grey),
#             ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Fila de total
#             ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),  # Fila de total en negrita
#         ])
        
#         # Alternar colores para filas de categorías
#         for i in range(1, len(summary_data)-1):
#             if i % 2 == 0:
#                 summary_style.add('BACKGROUND', (0, i), (-1, i), colors.beige)
#             else:
#                 summary_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
        
#         summary_table.setStyle(summary_style)
#         elements.append(summary_table)
        
#         # Construir el PDF
#         doc.build(elements)
        
#         # Crear respuesta HTTP
#         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
#         # Determinar nombre de archivo según si es un registro específico o una lista
#         if self.kwargs.get('pk'):
#             filename = f"{self.filename_prefix}_id{self.kwargs.get('pk')}_{timestamp}.pdf"
#         else:
#             filename = f"{self.filename_prefix}_report_{timestamp}.pdf"
        
#         response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
#         # Cerrar buffer
#         buffer.close()
        
#         return response

# # =========== WASTE DESTINATION VIEWS ===========

# class WasteDestinationListView(OptimizedSecureListView):
#     """
#     Vista optimizada para listar destinos de residuos con capacidades avanzadas
#     de búsqueda, filtrado y exportación.
#     """
#     permission_required = 'waste.view_wastedestination'
#     model = WasteDestination
#     template_name = 'core/list.html'
    
#     # Definir explícitamente los campos para búsqueda
#     search_fields = ['notes', 'waste_type__name', 'manager__name', 'carrier', 'vehicle_plate', 'manifest_number', 'certificate_number']
#     # Ordenamiento por defecto
#     order_by = ('-departure_date', 'manager__name', 'waste_type__name')
    
#     # Atributos específicos
#     title = _('Listado de Destinos de Residuos')
#     entity = _('Destino de Residuos')
    
#     def get_queryset(self):
#         queryset = super().get_queryset()
        
#         # Filtro por área
#         area_id = self.request.GET.get('area', '')
#         if area_id and area_id.isdigit():
#             queryset = queryset.filter(area_id=area_id)
        
#         # Filtro por tipo de residuo
#         waste_type_id = self.request.GET.get('waste_type', '')
#         if waste_type_id and waste_type_id.isdigit():
#             queryset = queryset.filter(waste_type_id=waste_type_id)
        
#         # Filtro por categoría de residuo
#         waste_category = self.request.GET.get('waste_category', '')
#         if waste_category:
#             queryset = queryset.filter(waste_type__category=waste_category)
            
#         # Filtro por gestor de residuos
#         manager_id = self.request.GET.get('manager', '')
#         if manager_id and manager_id.isdigit():
#             queryset = queryset.filter(manager_id=manager_id)
            
#         # Filtro por estado de destino
#         status = self.request.GET.get('status', '')
#         if status:
#             queryset = queryset.filter(status=status)
            
#         # Filtro por método de tratamiento
#         treatment_method = self.request.GET.get('treatment_method', '')
#         if treatment_method:
#             queryset = queryset.filter(treatment_method=treatment_method)
            
#         # Filtro por rango de fechas de salida
#         departure_from = self.request.GET.get('departure_from', '')
#         departure_to = self.request.GET.get('departure_to', '')
        
#         if departure_from:
#             try:
#                 start_date = datetime.strptime(departure_from, '%Y-%m-%d').date()
#                 queryset = queryset.filter(departure_date__gte=start_date)
#             except ValueError:
#                 pass
                
#         if departure_to:
#             try:
#                 end_date = datetime.strptime(departure_to, '%Y-%m-%d').date()
#                 queryset = queryset.filter(departure_date__lte=end_date)
#             except ValueError:
#                 pass
                
#         # Filtro por rango de fechas de entrega
#         delivery_from = self.request.GET.get('delivery_from', '')
#         delivery_to = self.request.GET.get('delivery_to', '')
        
#         if delivery_from:
#             try:
#                 start_date = datetime.strptime(delivery_from, '%Y-%m-%d').date()
#                 queryset = queryset.filter(delivery_date__gte=start_date)
#             except ValueError:
#                 pass
                
#         if delivery_to:
#             try:
#                 end_date = datetime.strptime(delivery_to, '%Y-%m-%d').date()
#                 queryset = queryset.filter(delivery_date__lte=end_date)
#             except ValueError:
#                 pass
        
#         # Filtro por cantidad mínima
#         min_quantity = self.request.GET.get('min_quantity', '')
#         if min_quantity and min_quantity.replace('.', '', 1).isdigit():
#             queryset = queryset.filter(quantity__gte=float(min_quantity))
            
#         # Filtro por certificado (con/sin certificado)
#         has_certificate = self.request.GET.get('has_certificate', '')
#         if has_certificate == 'yes':
#             queryset = queryset.filter(certificate_number__isnull=False, certificate_file__isnull=False)
#         elif has_certificate == 'no':
#             queryset = queryset.filter(Q(certificate_number__isnull=True) | Q(certificate_file__isnull=True))
            
#         # Prefetch related para optimizar las consultas
#         queryset = queryset.select_related('area', 'waste_type', 'manager')
            
#         return queryset
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
        
#         # Configuración específica para esta vista
#         context['headers'] = ['FECHA SALIDA', 'GESTOR', 'TIPO DE RESIDUO', 'CATEGORÍA', 'CANTIDAD', 'UNIDAD', 'MÉTODO', 'ESTADO', 'CERTIFICADO']
#         context['fields'] = ['departure_date', 'manager__name', 'waste_type__name', 'waste_type__get_category_display', 
#                             'quantity', 'get_unit_display', 'get_treatment_method_display', 'get_status_display', 'certificate_number']
        
#         # Configuración de botones y acciones
#         context['Btn_Add'] = [
#             {
#                 'name': 'add',
#                 'label': _('Registrar Destino'),
#                 'icon': 'add',
#                 'url': 'control residuos:destination_create',
#                 'modal': True,
#             }
#         ]
        
#         context['url_export'] = 'control residuos:destination_export'
        
#         context['actions'] = [
#             {
#                 'name': 'view',
#                 'label': '',
#                 'icon': 'visibility',
#                 'color': 'info',
#                 'color2': 'white',
#                 'title': _('Ver Destino'),
#                 'url': 'control residuos:destination_detail',
#                 'modal': False
#             },
#             {
#                 'name': 'edit',
#                 'label': '',
#                 'icon': 'edit',
#                 'color': 'primary',
#                 'color2': 'white',
#                 'title': _('Editar Destino'),
#                 'url': 'control residuos:destination_update',
#                 'modal': True
#             },
#             {
#                 'name': 'del',
#                 'label': '',
#                 'icon': 'delete',
#                 'color': 'danger',
#                 'color2': 'white',
#                 'title': _('Eliminar Destino'),
#                 'url': 'control residuos:destination_delete',
#                 'modal': True
#             },
#             {
#                 'name': 'certificate',
#                 'label': '',
#                 'icon': 'verified',
#                 'color': 'success',
#                 'color2': 'white',
#                 'title': _('Actualizar Certificado'),
#                 'url': 'control residuos:destination_certificate',
#                 'modal': True
#             },
#         ]
        
#         # Obtener áreas para el filtro
#         context['areas'] = CompanyArea.objects.filter(is_active=True).order_by('name')
        
#         # Obtener tipos de residuos para el filtro
#         context['waste_types'] = WasteType.objects.filter(is_active=True).order_by('name')
        
#         # Obtener gestores para el filtro
#         context['managers'] = WasteManager.objects.filter(is_active=True).order_by('name')
        
#         # Categorías de residuos para el filtro
#         context['waste_categories'] = dict(WasteType.CATEGORIES)
        
#         # Unidades de medida para el filtro
#         context['units'] = dict(WasteRecord.UNITS)
        
#         # Estados para el filtro
#         context['statuses'] = dict(WasteDestination.STATUSES)
        
#         # Métodos de tratamiento para el filtro
#         context['treatment_methods'] = dict(WasteDestination.TREATMENT_METHODS)
        
#         # Filtros adicionales específicos para destinos de residuos
#         context['custom_filters'] = {
#             'waste_category': [
#                 {'value': category[0], 'label': category[1]} 
#                 for category in WasteType.CATEGORIES
#             ],
#             'status': [
#                 {'value': status[0], 'label': status[1]} 
#                 for status in WasteDestination.STATUSES
#             ],
#             'treatment_method': [
#                 {'value': method[0], 'label': method[1]} 
#                 for method in WasteDestination.TREATMENT_METHODS
#             ],
#             'has_certificate': [
#                 {'value': 'yes', 'label': _('Con certificado')},
#                 {'value': 'no', 'label': _('Sin certificado')}
#             ]
#         }
        
#         # Añadir fechas predefinidas para filtros rápidos
#         today = timezone.now().date()
#         context['predefined_dates'] = {
#             'today': today.strftime('%Y-%m-%d'),
#             'yesterday': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
#             'week_start': (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d'),
#             'month_start': today.replace(day=1).strftime('%Y-%m-%d'),
#             'year_start': today.replace(month=1, day=1).strftime('%Y-%m-%d'),
#         }
        
#         # URL de cancelación
#         context['cancel_url'] = reverse_lazy('control residuos:destination_list')
        
#         return context

# class WasteDestinationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
#     """Mostrar detalles del destino de residuos"""
#     permission_required = 'waste.view_wastedestination'
#     model = WasteDestination
#     context_object_name = 'destination'
#     template_name = 'waste/destination_detail.html'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Detalle de Destino de Residuo')
#         context['entity'] = _('Destino de Residuo')
        
#         # Obtener archivos multimedia relacionados
#         context['media_files'] = self.object.files.all()
        
#         # Agregar URLs para acciones
#         context['edit_url'] = reverse('control residuos:destination_update', kwargs={'pk': self.object.pk})
#         context['delete_url'] = reverse('control residuos:destination_delete', kwargs={'pk': self.object.pk})
#         context['list_url'] = reverse('control residuos:destination_list')
#         context['certificate_url'] = reverse('control residuos:destination_certificate', kwargs={'pk': self.object.pk})
        
#         # URL para exportar este destino específico
#         context['export_url'] = reverse('control residuos:destination_export', kwargs={'pk': self.object.pk})
        
#         # Status tracking
#         context['status_timeline'] = [
#             {
#                 'status': 'SCHEDULED',
#                 'label': _('Programado'),
#                 'date': self.object.departure_date,
#                 'completed': self.object.status != 'SCHEDULED',
#                 'active': self.object.status == 'SCHEDULED'
#             },
#             {
#                 'status': 'IN_TRANSIT',
#                 'label': _('En tránsito'),
#                 'date': self.object.departure_date,
#                 'completed': self.object.status not in ['SCHEDULED', 'IN_TRANSIT'],
#                 'active': self.object.status == 'IN_TRANSIT'
#             },
#             {
#                 'status': 'DELIVERED',
#                 'label': _('Entregado'),
#                 'date': self.object.delivery_date,
#                 'completed': self.object.status not in ['SCHEDULED', 'IN_TRANSIT', 'DELIVERED'],
#                 'active': self.object.status == 'DELIVERED'
#             },
#             {
#                 'status': 'TREATED',
#                 'label': _('Tratado'),
#                 'date': self.object.treatment_date,
#                 'completed': self.object.status not in ['SCHEDULED', 'IN_TRANSIT', 'DELIVERED', 'TREATED'],
#                 'active': self.object.status == 'TREATED'
#             },
#             {
#                 'status': 'CERTIFIED',
#                 'label': _('Certificado'),
#                 'date': self.object.updated_at if self.object.status == 'CERTIFIED' else None,
#                 'completed': self.object.status == 'CERTIFIED',
#                 'active': self.object.status == 'CERTIFIED'
#             },
#         ]
        
#         return context

# class WasteDestinationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
#     """
#     Vista para crear un nuevo destino de residuo
#     La auditoría se maneja automáticamente por las señales post_save
#     """
#     permission_required = 'waste.add_wastedestination'
#     model = WasteDestination
#     form_class = WasteDestinationForm
#     template_name = 'core/create.html'
    
#     def get_success_url(self):
#         return reverse_lazy('control residuos:destination_list')
    
#     def form_valid(self, form):
#         # Guardar el destino - la auditoría se maneja por señales
#         self.object = form.save()
        
#         # Manejar archivos cargados
#         files = self.request.FILES.getlist('media_files')
#         for file in files:
#             WasteMediaFile.objects.create(
#                 destination=self.object,
#                 file=file,
#                 file_type=file.content_type,
#                 description=_('Archivo adjunto al destino de residuo')
#             )
        
#         messages.success(self.request, _('Destino de residuo creado con éxito'))
        
#         # Verificar si es una solicitud AJAX
#         if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': True,
#                 'message': _('Destino de residuo creado con éxito'),
#                 'redirect': self.get_success_url().resolve(self.request)
#             })
        
#         return super().form_valid(form)
    
#     def form_invalid(self, form):
#         if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             errors = {}
#             for field, error_list in form.errors.items():
#                 errors[field] = [str(error) for error in error_list]
                
#             return JsonResponse({
#                 'success': False,
#                 'errors': errors
#             }, status=400)
            
#         return super().form_invalid(form)
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Registrar Destino de Residuo')
#         context['entity'] = _('Destino de Residuo')
#         context['list_url'] = reverse_lazy('control residuos:destination_list')
#         context['action'] = 'add'
#         context['is_upload'] = True  # Para habilitar la carga de archivos
#         return context

# class WasteDestinationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
#     """
#     Vista para actualizar información de un destino de residuo
#     La auditoría es manejada automáticamente por las señales pre_save y post_save
#     """
#     permission_required = 'waste.change_wastedestination'
#     model = WasteDestination
#     form_class = WasteDestinationForm
#     template_name = 'core/create.html'
    
#     def get_success_url(self):
#         return reverse_lazy('control residuos:destination_list')
    
#     def form_valid(self, form):
#         # Guardar el destino - la auditoría se maneja por señales
#         self.object = form.save()
        
#         # Manejar archivos cargados
#         files = self.request.FILES.getlist('media_files')
#         for file in files:
#             WasteMediaFile.objects.create(
#                 destination=self.object,
#                 file=file,
#                 file_type=file.content_type,
#                 description=_('Archivo adjunto al destino de residuo')
#             )
        
#         messages.success(self.request, _('Destino de residuo actualizado con éxito'))
        
#         if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': True,
#                 'message': _('Destino de residuo actualizado con éxito'),
#                 'redirect': self.get_success_url().resolve(self.request)
#             })
            
#         return super().form_valid(form)
    
#     def form_invalid(self, form):
#         if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             errors = {}
#             for field, error_list in form.errors.items():
#                 errors[field] = [str(error) for error in error_list]
                
#             return JsonResponse({
#                 'success': False,
#                 'errors': errors
#             }, status=400)
            
#         return super().form_invalid(form)
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Editar Destino de Residuo')
#         context['entity'] = _('Destino de Residuo')
#         context['list_url'] = reverse_lazy('control residuos:destination_list')
#         context['action'] = 'edit'
#         context['is_upload'] = True  # Para habilitar la carga de archivos
        
#         # Obtener archivos multimedia ya existentes
#         context['existing_files'] = self.object.files.all()
        
#         return context

# class WasteDestinationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
#     """
#     Vista para eliminar un destino de residuo
#     La auditoría es manejada automáticamente por la señal post_delete
#     """
#     permission_required = 'waste.delete_wastedestination'
#     model = WasteDestination
#     template_name = 'core/del.html'
#     context_object_name = 'destination'
#     success_url = reverse_lazy('control residuos:destination_list')
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Eliminar Destino de Residuo')
#         context['entity'] = _('Destino de Residuo')
#         context['texto'] = f'¿Seguro de eliminar el destino de {self.object.waste_type.name} a {self.object.manager.name} del {self.object.departure_date}?'
#         context['list_url'] = reverse_lazy('control residuos:destination_list')
#         return context
    
#     def delete(self, request, *args, **kwargs):
#         self.object = self.get_object()
        
#         try:
#             # La auditoría se maneja automáticamente con la señal post_delete
#             self.object.delete()
#             messages.success(request, _('Destino de residuo eliminado con éxito'))
            
#             if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                 return JsonResponse({
#                     'success': True,
#                     'message': _('Destino de residuo eliminado con éxito'),
#                     'redirect': self.success_url
#                 })
                
#             return redirect(self.success_url)
            
#         except Exception as e:
#             # Capturar errores de integridad referencial
#             error_message = _('No se puede eliminar el destino porque está siendo utilizado en otros registros')
            
#             if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                 return JsonResponse({
#                     'success': False,
#                     'message': error_message
#                 }, status=400)
                
#             messages.error(request, error_message)
#             return redirect(self.success_url)

# class WasteDestinationCertificateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
#     """
#     Vista para actualizar el certificado de un destino de residuo
#     """
#     permission_required = 'waste.change_wastedestination'
#     model = WasteDestination
#     template_name = 'waste/destination_certificate.html'
#     fields = ['certificate_number', 'certificate_file', 'treatment_date', 'notes']
    
#     def get_success_url(self):
#         return reverse_lazy('control residuos:destination_detail', kwargs={'pk': self.object.pk})
    
#     def form_valid(self, form):
#         self.object = form.save(commit=False)
        
#         # Actualizar el estado a certificado
#         self.object.status = 'CERTIFIED'
        
#         # Si no hay fecha de tratamiento, usar la fecha actual
#         if not self.object.treatment_date:
#             self.object.treatment_date = timezone.now().date()
            
#         self.object.save()
        
#         messages.success(self.request, _('Certificado actualizado con éxito'))
        
#         if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': True,
#                 'message': _('Certificado actualizado con éxito'),
#                 'redirect': self.get_success_url().resolve(self.request)
#             })
            
#         return super().form_valid(form)
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Actualizar Certificado')
#         context['entity'] = _('Destino de Residuo')
#         context['list_url'] = reverse_lazy('control residuos:destination_list')
        
#         # Información del destino para mostrar
#         context['destination_info'] = {
#             'waste_type': self.object.waste_type.name,
#             'category': self.object.waste_type.get_category_display(),
#             'manager': self.object.manager.name,
#             'departure_date': self.object.departure_date,
#             'quantity': f"{self.object.quantity} {self.object.get_unit_display()}"
#         }
        
#         return context

# class WasteDestinationExportView(GenericExportView):
#     """
#     Vista para exportar destinos de residuos en diferentes formatos
#     Soporta CSV, Excel y PDF con filtros aplicados
#     """
#     model = WasteDestination
#     fields_to_export = ['departure_date', 'manager__name', 'waste_type__name', 
#                        'waste_type__get_category_display', 'quantity', 
#                        'get_unit_display', 'get_treatment_method_display', 
#                        'manifest_number', 'carrier', 'vehicle_plate', 
#                        'delivery_date', 'treatment_date', 'get_status_display',
#                        'certificate_number', 'notes']
#     permission_required = 'waste.view_wastedestination'
#     filename_prefix = 'waste_destination'
    
#     def get_queryset(self):
#         """Get records with applied filters or a specific destination"""
#         destination_id = self.kwargs.get('pk')
        
#         if destination_id:
#             return WasteDestination.objects.filter(id=destination_id)
        
#         # Iniciar el queryset
#         queryset = WasteDestination.objects.all()
        
#         # Aplicar filtros similares a los de la vista de lista
#         area_id = self.request.GET.get('area', '')
#         if area_id and area_id.isdigit():
#             queryset = queryset.filter(area_id=area_id)
        
#         waste_type_id = self.request.GET.get('waste_type', '')
#         if waste_type_id and waste_type_id.isdigit():
#             queryset = queryset.filter(waste_type_id=waste_type_id)
        
#         waste_category = self.request.GET.get('waste_category', '')
#         if waste_category:
#             queryset = queryset.filter(waste_type__category=waste_category)
            
#         manager_id = self.request.GET.get('manager', '')
#         if manager_id and manager_id.isdigit():
#             queryset = queryset.filter(manager_id=manager_id)
            
#         status = self.request.GET.get('status', '')
#         if status:
#             queryset = queryset.filter(status=status)
            
#         treatment_method = self.request.GET.get('treatment_method', '')
#         if treatment_method:
#             queryset = queryset.filter(treatment_method=treatment_method)
        
#         departure_from = self.request.GET.get('departure_from', '')
#         departure_to = self.request.GET.get('departure_to', '')
        
#         if departure_from:
#             try:
#                 start_date = datetime.strptime(departure_from, '%Y-%m-%d').date()
#                 queryset = queryset.filter(departure_date__gte=start_date)
#             except ValueError:
#                 pass
                
#         if departure_to:
#             try:
#                 end_date = datetime.strptime(departure_to, '%Y-%m-%d').date()
#                 queryset = queryset.filter(departure_date__lte=end_date)
#             except ValueError:
#                 pass
                
#         # Optimizar consultas con select_related
#         return queryset.select_related('area', 'waste_type', 'manager').order_by('-departure_date')
    
#     def export_pdf(self, data):
#         """Export waste destinations in PDF format with detailed information"""
#         if not data:
#             return HttpResponse(_("No se encontraron registros"), status=404)
        
#         # Create PDF file
#         buffer = BytesIO()
#         doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
#         elements = []
        
#         # PDF styles
#         styles = getSampleStyleSheet()
#         title_style = styles['Heading1']
#         section_style = styles['Heading2']
#         normal_style = styles['Normal']
        
#         # Document title
#         title = Paragraph(_("Informe de Destinos de Residuos"), title_style)
#         elements.append(title)
#         elements.append(Spacer(1, 12))
        
#         # Filtros aplicados
#         filter_text = []
        
#         # Verificar filtros aplicados para mostrarlos en el informe
#         if self.request.GET.get('departure_from') and self.request.GET.get('departure_to'):
#             filter_text.append(f"{_('Periodo de salida')}: {self.request.GET.get('departure_from')} - {self.request.GET.get('departure_to')}")
#         elif self.request.GET.get('departure_from'):
#             filter_text.append(f"{_('Desde')}: {self.request.GET.get('departure_from')}")
#         elif self.request.GET.get('departure_to'):
#             filter_text.append(f"{_('Hasta')}: {self.request.GET.get('departure_to')}")
            
#         if self.request.GET.get('area'):
#             area_name = CompanyArea.objects.filter(id=self.request.GET.get('area')).first()
#             if area_name:
#                 filter_text.append(f"{_('Área')}: {area_name.name}")
                
#         if self.request.GET.get('waste_type'):
#             waste_type_name = WasteType.objects.filter(id=self.request.GET.get('waste_type')).first()
#             if waste_type_name:
#                 filter_text.append(f"{_('Tipo de Residuo')}: {waste_type_name.name}")
                
#         if self.request.GET.get('waste_category'):
#             category_dict = dict(WasteType.CATEGORIES)
#             category_name = category_dict.get(self.request.GET.get('waste_category'))
#             if category_name:
#                 filter_text.append(f"{_('Categoría')}: {category_name}")
                
#         if self.request.GET.get('manager'):
#             manager_name = WasteManager.objects.filter(id=self.request.GET.get('manager')).first()
#             if manager_name:
#                 filter_text.append(f"{_('Gestor')}: {manager_name.name}")
        
#         if self.request.GET.get('status'):
#             status_dict = dict(WasteDestination.STATUSES)
#             status_name = status_dict.get(self.request.GET.get('status'))
#             if status_name:
#                 filter_text.append(f"{_('Estado')}: {status_name}")
                
#         if self.request.GET.get('treatment_method'):
#             method_dict = dict(WasteDestination.TREATMENT_METHODS)
#             method_name = method_dict.get(self.request.GET.get('treatment_method'))
#             if method_name:
#                 filter_text.append(f"{_('Método de Tratamiento')}: {method_name}")
        
#         # Mostrar filtros aplicados
#         if filter_text:
#             elements.append(Paragraph(_("Filtros aplicados:"), normal_style))
#             for filter_line in filter_text:
#                 elements.append(Paragraph(f"• {filter_line}", normal_style))
#             elements.append(Spacer(1, 12))
        
#         # Fecha de generación del informe
#         elements.append(Paragraph(f"{_('Fecha de generación')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
#         elements.append(Spacer(1, 20))
        
#         # Crear tabla de destinos
#         table_data = [
#             [_("Fecha Salida"), _("Gestor"), _("Tipo de Residuo"), _("Categoría"), 
#              _("Cantidad"), _("Unidad"), _("Método"), _("Estado"), _("Certificado")]
#         ]
        
#         # Totales para calcular
#         total_by_category = {}
#         total_by_status = {}
#         total_by_treatment = {}
#         total_quantity = 0
        
#         # Agregar destinos a la tabla
#         for dest in data:
#             category = dest['waste_type__get_category_display']
#             status = dest['get_status_display']
#             treatment = dest['get_treatment_method_display']
#             quantity = dest['quantity']
            
#             # Acumular totales
#             if category not in total_by_category:
#                 total_by_category[category] = 0
#             total_by_category[category] += quantity
            
#             if status not in total_by_status:
#                 total_by_status[status] = 0
#             total_by_status[status] += quantity
            
#             if treatment not in total_by_treatment:
#                 total_by_treatment[treatment] = 0
#             total_by_treatment[treatment] += quantity
            
#             total_quantity += quantity
            
#             # Agregar fila a la tabla
#             table_data.append([
#                 dest['departure_date'],
#                 dest['manager__name'],
#                 dest['waste_type__name'],
#                 category,
#                 dest['quantity'],
#                 dest['get_unit_display'],
#                 treatment,
#                 status,
#                 dest['certificate_number'] or "-"
#             ])
        
#         # Crear la tabla con los datos
#         table = Table(table_data, repeatRows=1)
        
#         # Estilo de la tabla
#         table_style = TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('FONTSIZE', (0, 0), (-1, 0), 10),
#             ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#             ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#             ('GRID', (0, 0), (-1, -1), 1, colors.grey),
#             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#             ('ALIGN', (4, 1), (4, -1), 'RIGHT'),  # Alinear cantidades a la derecha
#         ])
        
# #         # Alternar colores de las