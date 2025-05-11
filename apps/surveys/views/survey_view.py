

from datetime import datetime
from apps.base.views.genericexportview import GenericExportView
from apps.base.views.genericlistview import OptimizedSecureListView
from apps.surveys.forms.response_form import ResponseForm
from apps.surveys.forms.survey_form import SurveyForm
from apps.surveys.models.surveymodel import Survey
from django.utils import timezone
from django.db.models import Q, Count
from django.utils.translation import gettext as _
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView, View
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib import messages
from reportlab.lib.pagesizes import letter, landscape
from apps.surveys.models.surveymodel import Survey, Response
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, cm
from reportlab.platypus import PageBreak

class SurveyListView(OptimizedSecureListView):
    """
    Vista optimizada para listar encuestas con capacidades avanzadas
    de búsqueda, filtrado y exportación.
    """
    permission_required = 'survey.view_survey'
    model = Survey
    template_name = 'core/list.html'
    
    # Definir explícitamente los campos para búsqueda
    search_fields = ['title', 'description']
    # Ordenamiento por defecto
    order_by = ('-created_at', 'title')
    
    # Atributos específicos
    title = _('Listado de Encuestas')
    entity = _('Encuesta')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Búsqueda personalizada para encuestas publicadas, no publicadas, etc.
        status = self.request.GET.get('status', '')
        if status:
            if status == 'published':
                queryset = queryset.filter(is_published=True)
            elif status == 'unpublished':
                queryset = queryset.filter(is_published=False)
            elif status == 'active':
                today = timezone.now().date()
                queryset = queryset.filter(is_published=True)
                queryset = queryset.filter(start_date__lte=today)
                queryset = queryset.filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
            elif status == 'expired':
                today = timezone.now().date()
                queryset = queryset.filter(
                    is_published=True,
                    end_date__lt=today
                )
            elif status == 'upcoming':
                today = timezone.now().date()
                queryset = queryset.filter(
                    is_published=True,
                    start_date__gt=today
                )
        
        # Filtro por rango de fechas
        start_from = self.request.GET.get('start_from', '')
        start_to = self.request.GET.get('start_to', '')
        if start_from:
            try:
                start_date = datetime.strptime(start_from, '%Y-%m-%d').date()
                queryset = queryset.filter(start_date__gte=start_date)
            except ValueError:
                pass
        if start_to:
            try:
                end_date = datetime.strptime(start_to, '%Y-%m-%d').date()
                queryset = queryset.filter(start_date__lte=end_date)
            except ValueError:
                pass
        
        # Filtro por número de preguntas
        min_questions = self.request.GET.get('min_questions', '')
        if min_questions and min_questions.isdigit():
            queryset = queryset.annotate(
                question_count=Count('questions', filter=Q(questions__is_active=True))
            ).filter(question_count__gte=int(min_questions))
        
        # Filtro por número de respuestas
        min_responses = self.request.GET.get('min_responses', '')
        if min_responses and min_responses.isdigit():
            queryset = queryset.annotate(
                response_count=Count('responses', filter=Q(responses__is_active=True))
            ).filter(response_count__gte=int(min_responses))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Configuración específica para esta vista
        context['headers'] = ['TÍTULO', 'DESCRIPCIÓN', 'PUBLICADO', 'FECHA INICIO', 'FECHA FIN', 'PREGUNTAS', 'RESPUESTAS']
        context['fields'] = ['title', 'description', 'is_published', 'start_date', 'end_date', 'question_count', 'response_count']
        
        # Configuración de botones y acciones
        context['Btn_Add'] = [
            {
                'name': 'add',
                'label': _('Crear Encuesta'),
                'icon': 'add',
                'url': 'encuestas:survey_create',
                'modal': True,
            }
        ]
        
        # context['url_export'] = 'encuestas:survey-download'
        
        context['actions'] = [
            {
                'name': 'view',
                'label': '',
                'icon': 'visibility',
                'color': 'info',
                'color2': 'white',
                'title': _('Ver Encuesta'),
                'url': 'encuestas:survey_detail',
                'modal': False
            },
            {
                'name': 'del',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'title': _('Eliminar Encuesta'),
                'url': 'encuestas:survey_delete',
                'modal': True
            },
            {
                'name': 'publish',
                'label': '',
                'icon': 'publish',
                'color': 'success',
                'color2': 'white',
                'title': _('Publicar Encuesta'),
                'url': 'encuestas:survey_publish',
                'modal': True
            },
        ]
        
        # Filtros adicionales específicos para encuestas
        context['custom_filters'] = {
            'status': [
                {'value': 'published', 'label': _('Publicadas')},
                {'value': 'unpublished', 'label': _('No Publicadas')},
                {'value': 'active', 'label': _('Activas')},
                {'value': 'expired', 'label': _('Expiradas')},
                {'value': 'upcoming', 'label': _('Próximas')},
            ]
        }
        
        # URL de cancelación
        context['cancel_url'] = reverse_lazy('encuestas:survey_list')
        
        return context

class SurveyDetailView(LoginRequiredMixin, DetailView):
    """Show survey details"""
    model = Survey
    context_object_name = 'survey'
    template_name = 'surveys/survey_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.filter(is_active=True).order_by('order')
        context['response_count'] = self.object.response_count
        context['url_export'] = 'encuestas:survey_export'
        return context

class SurveyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear una nueva encuesta
    La auditoría se maneja automáticamente por las señales post_save
    """
    permission_required = 'survey.add_survey'
    model = Survey
    form_class = SurveyForm
    template_name = 'core/create.html'
    
    def get_success_url(self):
        return reverse_lazy('encuestas:survey_list')
    
    def form_valid(self, form):
        # Guardar la encuesta - la auditoría se maneja por señales
        self.object = form.save()
        
        messages.success(self.request, _('Encuesta creada con éxito'))
        
        # Verificar si es una solicitud AJAX
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Encuesta creada con éxito'),
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
        context['title'] = _('Crear Encuesta')
        context['entity'] = _('Encuesta')
        context['list_url'] = reverse_lazy('encuestas:survey_list')
        context['action'] = 'add'
        return context

class SurveyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para actualizar información de una encuesta
    La auditoría es manejada automáticamente por las señales pre_save y post_save
    """
    permission_required = 'survey.change_survey'
    model = Survey
    form_class = SurveyForm
    template_name = 'core/create.html'
    
    def get_success_url(self):
        return reverse_lazy('encuestas:survey_list')
    
    def form_valid(self, form):
        # Guardar la encuesta - la auditoría se maneja por señales
        self.object = form.save(commit=True)
        
        messages.success(self.request, _('Encuesta actualizada con éxito'))
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Encuesta actualizada con éxito'),
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
        context['title'] = _('Editar Encuesta')
        context['entity'] = _('Encuesta')
        context['list_url'] = reverse_lazy('encuestas:survey_list')
        context['action'] = 'edit'
        return context

class SurveyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Vista para eliminar una encuesta
    La auditoría es manejada automáticamente por la señal post_delete
    """
    permission_required = 'survey.delete_survey'
    model = Survey
    template_name = 'core/del.html'
    context_object_name = 'Encuesta'
    success_url = reverse_lazy('encuestas:survey_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Encuesta')
        context['entity'] = _('Encuesta')
        context['texto'] = f'¿Seguro de eliminar la Encuesta {self.object}?'
        context['list_url'] = reverse_lazy('encuestas:survey_list')
        return context
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        try:
            # La auditoría se maneja automáticamente con la señal post_delete
            self.object.delete()
            messages.success(request, _('Encuesta eliminada con éxito'))
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': _('Encuesta eliminada con éxito'),
                    'redirect': self.success_url
                })
                
            return redirect(self.success_url)
            
        except Exception as e:
            # Capturar errores de integridad referencial
            error_message = _('No se puede eliminar la encuesta porque está siendo utilizada en otros registros')
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=400)
                
            messages.error(request, error_message)
            return redirect(self.success_url)
        
class SurveyPublishView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para publicar encuestas
    La auditoría se maneja con las señales de pre_save y post_save
    """
    permission_required = 'survey.change_survey'
    model = Survey
    template_name = 'core/confirm.html'  # Add a template for confirmation
    fields = ['is_published']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Publicar Encuesta')
        context['texto'] = _('¿Está seguro de que desea publicar esta encuesta?')
        context['btn_text'] = _('Publicar')
        context['btn_class'] = 'btn-success'
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Cambiar estado de publicación - la auditoría registrará el cambio automáticamente
        self.object.is_published = True
        self.object.save(update_fields=['is_published'])
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_published': self.object.is_published,
                'message': _("Encuesta publicada correctamente"),
                'reload': True
            })
            
        messages.success(request, _("Encuesta publicada correctamente"))
        return redirect('encuestas:survey_detail', pk=self.object.pk)

class SurveyUnpublishView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para despublicar encuestas
    La auditoría se maneja con las señales de pre_save y post_save
    """
    permission_required = 'survey.change_survey'
    model = Survey
    template_name = 'core/confirm.html'  # Add a template for confirmation
    fields = ['is_published']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Despublicar Encuesta')
        context['texto'] = _('¿Está seguro de que desea despublicar esta encuesta?')
        context['btn_text'] = _('Despublicar')
        context['btn_class'] = 'btn-warning'
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Cambiar estado de publicación - la auditoría registrará el cambio automáticamente
        self.object.is_published = False
        self.object.save(update_fields=['is_published'])
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_published': self.object.is_published,
                'message': _("Encuesta despublicada correctamente"),
                'reload': True
            })
            
        messages.success(request, _("Encuesta despublicada correctamente"))
        return redirect('encuestas:survey_detail', pk=self.object.pk)

class SurveyPreviewView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Vista para previsualizar una encuesta antes de publicarla
    Muestra las preguntas y opciones de respuesta como las verían los encuestados
    """
    permission_required = 'surveys.view_survey'  
    model = Survey
    context_object_name = 'survey'
    template_name = 'surveys/survey_preview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Previsualización de Encuesta')
        context['entity'] = _('Encuesta')
        
        # Obtener todas las preguntas activas ordenadas por el campo 'order'
        context['questions'] = self.object.questions.filter(is_active=True).order_by('order')
        
        # Agregar información adicional para la previsualización
        context['is_preview'] = True
        context['today'] = timezone.now().date()
        
        # Verificar el estado actual de la encuesta
        context['published'] = self.object.is_published
        context['is_active'] = (
            self.object.is_published and 
            (not self.object.start_date or self.object.start_date <= context['today']) and
            (not self.object.end_date or self.object.end_date >= context['today'])
        )
        
        # Obtener el formulario de respuesta para simular cómo se verá
        context['form'] = ResponseForm()
        
        # URLs para acciones posteriores a la previsualización
        context['return_url'] = reverse('encuestas:survey_detail', kwargs={'pk': self.object.pk})
        context['publish_url'] = reverse('encuestas:survey_publish', kwargs={'pk': self.object.pk})
        context['edit_url'] = reverse('encuestas:survey_update', kwargs={'pk': self.object.pk})
        
        return context

class SurveyExportView(GenericExportView):
    model = Survey
    fields_to_export = ['title', 'description', 'start_date', 'end_date', 'is_published', 
                       'questions_per_page', 'allow_save_and_continue', 'show_progress_bar', 
                       'show_results_after_completion']
    permission_required = 'surveys.view_survey'
    filename_prefix = 'survey'
    
    def get_queryset(self):
        """Get only the selected survey"""
        survey_id = self.kwargs.get('pk') or self.request.GET.get('survey_id')
        if not survey_id:
            return Survey.objects.none()
        
        return Survey.objects.filter(id=survey_id)
    
    def export_pdf(self, data):
        """Export a single survey with its questions in PDF format"""
        if not data:
            # Return empty response if no survey was found
            return HttpResponse(_("Survey not found"), status=404)
        
        # Get the survey data (first item in the data list)
        survey_data = data[0]
        survey_id = survey_data.get('id')
        
        try:
            # Get the actual survey object
            survey = Survey.objects.get(id=survey_id)
        except Survey.DoesNotExist:
            return HttpResponse(_("Survey not found"), status=404)
        
        # Create PDF file
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # PDF styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        section_style = styles['Heading2']
        subsection_style = styles['Heading3']
        normal_style = styles['Normal']
        
        # Document title
        title = Paragraph(f"{_('Survey')}: {survey.title}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Survey description
        if survey.description:
            elements.append(Paragraph(_("Description:"), section_style))
            elements.append(Paragraph(survey.description, normal_style))
            elements.append(Spacer(1, 12))
        
        # Survey details table
        elements.append(Paragraph(_("Survey Details"), section_style))
        
        detail_data = [
            [_("Start Date"), str(survey.start_date) if survey.start_date else _("Not set")],
            [_("End Date"), str(survey.end_date) if survey.end_date else _("Not set")],
            [_("Published"), _("Yes") if survey.is_published else _("No")],
            [_("Questions Per Page"), str(survey.questions_per_page)],
            [_("Allow Save and Continue"), _("Yes") if survey.allow_save_and_continue else _("No")],
            [_("Show Progress Bar"), _("Yes") if survey.show_progress_bar else _("No")],
            [_("Allow Page Navigation"), _("Yes") if survey.allow_page_navigation else _("No")],
            [_("Show Results After Completion"), _("Yes") if survey.show_results_after_completion else _("No")],
            [_("Question Count"), str(survey.question_count)],
            [_("Response Count"), str(survey.response_count)]
        ]
        
        # Create and style details table
        detail_table = Table(detail_data, colWidths=[200, 300])
        detail_style = TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ])
        
        # Alternate colors for rows
        for i in range(len(detail_data)):
            if i % 2 == 0:
                detail_style.add('BACKGROUND', (1, i), (1, i), colors.beige)
            else:
                detail_style.add('BACKGROUND', (1, i), (1, i), colors.whitesmoke)
        
        detail_table.setStyle(detail_style)
        elements.append(detail_table)
        elements.append(Spacer(1, 20))
        
        # Questions section
        elements.append(Paragraph(_("Survey Questions"), section_style))
        elements.append(Spacer(1, 10))
        
        # Get questions for this survey
        questions = survey.questions.all().order_by('order')
        
        if questions.exists():
            # Add each question with its details
            for index, question in enumerate(questions, 1):
                # Question header
                elements.append(Paragraph(
                    f"{index}. {question.text} {'*' if question.is_required else ''}", 
                    subsection_style
                ))
                
                # Question details in a table
                q_detail_data = [
                    [_("Question Type"), question.question_type.name],
                    [_("Required"), _("Yes") if question.is_required else _("No")],
                    [_("Display Order"), str(question.order)]
                ]
                
                # Add help text if exists
                if question.help_text:
                    q_detail_data.append([_("Help Text"), question.help_text])
                
                # Add min/max values if exists
                if question.min_value is not None:
                    q_detail_data.append([_("Minimum Value"), str(question.min_value)])
                if question.max_value is not None:
                    q_detail_data.append([_("Maximum Value"), str(question.max_value)])
                
                # Add dependent question if exists
                if question.dependent_on:
                    q_detail_data.append([_("Dependent On"), f"Question #{question.dependent_on.order}: {question.dependent_on.text[:30]}..."])
                    q_detail_data.append([_("Dependent Value"), question.dependent_value])
                
                # Create question details table
                q_detail_table = Table(q_detail_data, colWidths=[150, 350])
                q_detail_style = TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ])
                
                # Alternate colors for rows
                for i in range(len(q_detail_data)):
                    if i % 2 == 0:
                        q_detail_style.add('BACKGROUND', (1, i), (1, i), colors.whitesmoke)
                    else:
                        q_detail_style.add('BACKGROUND', (1, i), (1, i), colors.beige)
                
                q_detail_table.setStyle(q_detail_style)
                elements.append(q_detail_table)
                
                # If the question has choices, add them
                if question.has_choices:
                    elements.append(Spacer(1, 8))
                    elements.append(Paragraph(_("Options:"), normal_style))
                    
                    choices = question.choices.all().order_by('order')
                    if choices.exists():
                        choice_data = [[_("Option Text"), _("Value"), _("Order")]]
                        
                        for choice in choices:
                            choice_data.append([
                                choice.text,
                                choice.value,
                                str(choice.order)
                            ])
                        
                        # Create choices table
                        choice_table = Table(choice_data, colWidths=[250, 150, 100])
                        choice_style = TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lavender),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                        ])
                        
                        # Alternate colors for rows
                        for i in range(1, len(choice_data)):
                            if i % 2 == 0:
                                choice_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
                            else:
                                choice_style.add('BACKGROUND', (0, i), (-1, i), colors.beige)
                        
                        choice_table.setStyle(choice_style)
                        elements.append(choice_table)
                
                # Add space between questions
                elements.append(Spacer(1, 20))
                
        else:
            elements.append(Paragraph(_("No questions found for this survey."), normal_style))
        
        # Build the PDF
        doc.build(elements)
        
        # Create HTTP response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.filename_prefix}_{survey.id}_{timestamp}.pdf"
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Close buffer
        buffer.close()
        
        return response


class SurveyPDFExportView(GenericExportView):
    model = Survey
    permission_required = 'surveys.view_survey'
    filename_prefix = 'survey'
    
    def get(self, request, *args, **kwargs):
        """Override get method to handle PDF export directly"""
        # Get survey ID from URL or query parameters
        survey_id = kwargs.get('pk') or request.GET.get('survey_id')
        if not survey_id:
            return HttpResponse(_("Survey ID is required"), status=400)
        
        # Export directly to PDF format
        return self.export_survey_pdf(survey_id)
    
    def export_survey_pdf(self, survey_id):
        """Export a specific survey with all its questions to PDF"""
        try:
            # Get the survey object
            survey = Survey.objects.get(id=survey_id)
        except Survey.DoesNotExist:
            return HttpResponse(_("Survey not found"), status=404)
        
        # Create PDF file
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # PDF styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        section_style = styles['Heading2']
        subsection_style = styles['Heading3']
        normal_style = styles['Normal']
        
        # Document title
        title = Paragraph(f"{_('Survey')}: {survey.title}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Survey description
        if survey.description:
            elements.append(Paragraph(_("Description:"), section_style))
            elements.append(Paragraph(survey.description, normal_style))
            elements.append(Spacer(1, 12))
        
        # Survey metadata
        elements.append(Paragraph(_("Survey Information"), section_style))
        
        detail_data = [
            [_("Start Date"), str(survey.start_date) if survey.start_date else _("Not set")],
            [_("End Date"), str(survey.end_date) if survey.end_date else _("Not set")],
            [_("Published"), _("Yes") if survey.is_published else _("No")],
            [_("Questions Per Page"), str(survey.questions_per_page)],
            [_("Allow Save and Continue"), _("Yes") if survey.allow_save_and_continue else _("No")],
            [_("Show Progress Bar"), _("Yes") if survey.show_progress_bar else _("No")],
            [_("Allow Page Navigation"), _("Yes") if survey.allow_page_navigation else _("No")],
            [_("Show Results After Completion"), _("Yes") if survey.show_results_after_completion else _("No")],
            [_("Question Count"), str(survey.question_count)],
            [_("Response Count"), str(survey.response_count)]
        ]
        
        # Create and style details table
        detail_table = Table(detail_data, colWidths=[200, 300])
        detail_style = TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ])
        
        # Alternate colors for rows
        for i in range(len(detail_data)):
            if i % 2 == 0:
                detail_style.add('BACKGROUND', (1, i), (1, i), colors.beige)
            else:
                detail_style.add('BACKGROUND', (1, i), (1, i), colors.whitesmoke)
        
        detail_table.setStyle(detail_style)
        elements.append(detail_table)
        elements.append(Spacer(1, 20))
        
        # Questions section
        elements.append(Paragraph(_("Survey Questions"), section_style))
        elements.append(Spacer(1, 10))
        
        # Get ALL questions for this survey, don't filter by is_active
        questions = survey.questions.all().order_by('order')
        
        if questions.exists():
            # Add each question with its details
            for index, question in enumerate(questions, 1):
                # Question header with required indicator
                elements.append(Paragraph(
                    f"{index}. {question.text} {'*' if question.is_required else ''}", 
                    subsection_style
                ))
                
                # Question details in a table
                q_detail_data = [
                    [_("Question Type"), question.question_type.name],
                    [_("Required"), _("Yes") if question.is_required else _("No")],
                    [_("Display Order"), str(question.order)],
                    [_("Active"), _("Yes") if getattr(question, 'is_active', True) else _("No")]
                ]
                
                # Add help text if exists
                if question.help_text:
                    q_detail_data.append([_("Help Text"), question.help_text])
                
                # Add min/max values if exists
                if question.min_value is not None:
                    q_detail_data.append([_("Minimum Value"), str(question.min_value)])
                if question.max_value is not None:
                    q_detail_data.append([_("Maximum Value"), str(question.max_value)])
                
                # Add dependent question if exists
                if question.dependent_on:
                    q_detail_data.append([_("Dependent On"), f"Question #{question.dependent_on.order}: {question.dependent_on.text[:30]}..."])
                    q_detail_data.append([_("Dependent Value"), question.dependent_value])
                
                # Create question details table
                q_detail_table = Table(q_detail_data, colWidths=[150, 350])
                q_detail_style = TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ])
                
                # Alternate colors for rows
                for i in range(len(q_detail_data)):
                    if i % 2 == 0:
                        q_detail_style.add('BACKGROUND', (1, i), (1, i), colors.whitesmoke)
                    else:
                        q_detail_style.add('BACKGROUND', (1, i), (1, i), colors.beige)
                
                q_detail_table.setStyle(q_detail_style)
                elements.append(q_detail_table)
                
                # If the question has choices, add them
                if question.has_choices:
                    elements.append(Spacer(1, 8))
                    elements.append(Paragraph(_("Options:"), normal_style))
                    
                    choices = question.choices.all().order_by('order')
                    if choices.exists():
                        choice_data = [[_("Option Text"), _("Value"), _("Order"), _("Is 'Other' Option")]]
                        
                        for choice in choices:
                            choice_data.append([
                                choice.text,
                                choice.value,
                                str(choice.order),
                                _("Yes") if choice.is_other_option else _("No")
                            ])
                        
                        # Create choices table
                        choice_table = Table(choice_data, colWidths=[200, 150, 60, 90])
                        choice_style = TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.lavender),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                        ])
                        
                        # Alternate colors for rows
                        for i in range(1, len(choice_data)):
                            if i % 2 == 0:
                                choice_style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
                            else:
                                choice_style.add('BACKGROUND', (0, i), (-1, i), colors.beige)
                        
                        choice_table.setStyle(choice_style)
                        elements.append(choice_table)
                
                # Add space between questions
                elements.append(Spacer(1, 20))
                
        else:
            elements.append(Paragraph(_("No questions found for this survey."), normal_style))
        
        # Build the PDF
        doc.build(elements)
        
        # Create HTTP response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"survey_{survey.id}_{timestamp}.pdf"
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Close buffer
        buffer.close()
        
        return response
    
