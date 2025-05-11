from django.db.models import Q, Max
from django.utils.translation import gettext as _
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, ListView

from apps.surveys.forms.question_form import QuestionForm
from apps.surveys.models.surveymodel import Question, QuestionType, Survey

# from .models import Question, Survey, QuestionType
# from .forms import QuestionForm


class QuestionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista para listar las preguntas de una encuesta específica
    """
    permission_required = 'survey.view_question'
    model = Question
    template_name = 'encuestas/question_list.html'
    context_object_name = 'questions'
    
    def get_queryset(self):
        """Filtrar preguntas por la encuesta seleccionada"""
        self.survey = get_object_or_404(Survey, pk=self.kwargs.get('survey_id'))
        return Question.objects.filter(survey=self.survey, is_active=True).order_by('order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Preguntas de Encuesta')
        context['entity'] = _('Pregunta')
        context['survey'] = self.survey
        context['list_url'] = reverse('encuestas:question_list', args=[self.survey.id])
        context['create_url'] = reverse('encuestas:question_create', args=[self.survey.id])
        context['return_url'] = reverse('encuestas:survey_list')
        
        # Obtener tipos de preguntas disponibles
        context['question_types'] = QuestionType.objects.filter(is_active=True)
        
        # Configuración de acciones para cada pregunta
        context['actions'] = [
            {
                'name': 'edit',
                'label': '',
                'icon': 'edit',
                'color': 'secondary',
                'color2': 'brown',
                'url': 'encuestas:question_update',
                'modal': True
            },
            {
                'name': 'choices',
                'label': '',
                'icon': 'list',
                'color': 'info',
                'color2': 'white',
                'url': 'encuestas:choice_list',
                'modal': False,
                'condition': 'has_choices'  # Mostrar solo si la pregunta tiene opciones
            },
            {
                'name': 'del',
                'label': '',
                'icon': 'delete',
                'color': 'danger',
                'color2': 'white',
                'url': 'encuestas:question_delete',
                'modal': True
            },
            {
                'name': 'up',
                'label': '',
                'icon': 'arrow_upward',
                'color': 'primary',
                'color2': 'white',
                'url': 'encuestas:question_move_up',
                'modal': False,
                'condition': 'not_first'  # Solo mostrar si no es la primera pregunta
            },
            {
                'name': 'down',
                'label': '',
                'icon': 'arrow_downward',
                'color': 'primary',
                'color2': 'white',
                'url': 'encuestas:question_move_down',
                'modal': False,
                'condition': 'not_last'  # Solo mostrar si no es la última pregunta
            }
        ]
        
        # Marcar las preguntas primera y última para las acciones de reordenamiento
        first_question = self.get_queryset().first()
        last_question = self.get_queryset().last()
        
        if first_question and last_question:
            context['first_question_id'] = first_question.id
            context['last_question_id'] = last_question.id
        
        return context


class QuestionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear una nueva pregunta en una encuesta específica
    """
    permission_required = 'survey.add_question'
    model = Question
    form_class = QuestionForm
    template_name = 'core/create.html'
    
    def get_initial(self):
        """Prepopular el formulario con la encuesta seleccionada"""
        initial = super().get_initial()
        self.survey = get_object_or_404(Survey, pk=self.kwargs.get('survey_id'))
        initial['survey'] = self.survey
        
        # Obtener el máximo orden y añadir 10 para la nueva pregunta
        max_order = Question.objects.filter(survey=self.survey).aggregate(Max('order'))['order__max'] or 0
        initial['order'] = max_order + 10
        
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['survey_id'] = self.kwargs.get('survey_id')
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('encuestas:survey_detail', args=[self.kwargs.get('survey_id')])
    
    def form_valid(self, form):
        # Guardar la pregunta - la auditoría se maneja por señales
        self.object = form.save()
        
        # Use the ACTUAL constants defined in QuestionType model
        question_type = self.object.question_type
        if question_type and question_type.name == QuestionType.NUMBER:  # Changed from 'NUMERIC' to NUMBER
            # Handle numeric question type
            pass
        elif question_type and question_type.name == QuestionType.MULTIPLE_CHOICE:
            # Handle multiple choice
            pass
        # Add more conditions for other question types as needed
        
        messages.success(self.request, _('Pregunta creada con éxito'))
        
        # Verificar si es una solicitud AJAX
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Pregunta creada con éxito'),
                'redirect': self.get_success_url()
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
        context['title'] = _('Crear Pregunta')
        context['entity'] = _('Pregunta')
        context['survey'] = get_object_or_404(Survey, pk=self.kwargs.get('survey_id'))
        context['list_url'] = reverse_lazy('encuestas:question_list', args=[self.kwargs.get('survey_id')])
        context['action'] = 'add'
        return context


class QuestionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para actualizar una pregunta existente
    """
    permission_required = 'survey.change_question'
    model = Question
    form_class = QuestionForm
    template_name = 'core/create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['survey_id'] = self.object.survey.id
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('encuestas:question_list', args=[self.object.survey.id])
    
    def form_valid(self, form):
        # Guardar la pregunta - la auditoría se maneja por señales
        self.object = form.save(commit=True)
        
        messages.success(self.request, _('Pregunta actualizada con éxito'))
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Pregunta actualizada con éxito'),
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
        context['title'] = _('Editar Pregunta')
        context['entity'] = _('Pregunta')
        context['list_url'] = reverse_lazy('encuestas:question_list', args=[self.object.survey.id])
        context['action'] = 'edit'
        return context


class QuestionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Vista para eliminar una pregunta
    """
    permission_required = 'survey.delete_question'
    model = Question
    template_name = 'core/del.html'
    context_object_name = 'Pregunta'
    
    def get_success_url(self):
        return reverse_lazy('encuestas:question_list', args=[self.object.survey.id])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Pregunta')
        context['entity'] = _('Pregunta')
        context['texto'] = f'¿Seguro de eliminar la pregunta "{self.object.text[:50]}"?'
        context['list_url'] = reverse_lazy('encuestas:question_list', args=[self.object.survey.id])
        return context
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        survey_id = self.object.survey.id
        
        try:
            # La auditoría se maneja automáticamente con la señal post_delete
            self.object.delete()
            messages.success(request, _('Pregunta eliminada con éxito'))
            
            # Reordenar las preguntas restantes
            self._reorder_questions(survey_id)
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': _('Pregunta eliminada con éxito'),
                    'redirect': self.get_success_url()
                })
                
            return redirect(self.get_success_url())
            
        except Exception as e:
            # Capturar errores de integridad referencial
            error_message = _('No se puede eliminar la pregunta porque está siendo utilizada en respuestas')
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=400)
                
            messages.error(request, error_message)
            return redirect(self.get_success_url())
    
    def _reorder_questions(self, survey_id):
        """Reordenar las preguntas después de eliminar una"""
        questions = Question.objects.filter(survey_id=survey_id, is_active=True).order_by('order')
        order = 10
        for question in questions:
            if question.order != order:
                question.order = order
                question.save(update_fields=['order'])
            order += 10


class QuestionMoveView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista base para mover preguntas arriba o abajo en el orden
    """
    permission_required = 'survey.change_question'
    model = Question
    http_method_names = ['post']
    fields = ['order']
    
    def get_success_url(self):
        return reverse_lazy('encuestas:question_list', args=[self.object.survey.id])
    
    def _swap_positions(self, question, other_question):
        """Intercambiar posiciones entre dos preguntas"""
        temp_order = question.order
        question.order = other_question.order
        other_question.order = temp_order
        
        # Guardar ambos objetos - las señales de auditoría registrarán los cambios
        question.save(update_fields=['order'])
        other_question.save(update_fields=['order'])


class QuestionMoveUpView(QuestionMoveView):
    """
    Vista para mover una pregunta hacia arriba en el orden
    """
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        survey_id = self.object.survey.id
        
        # Buscar la pregunta anterior
        prev_question = Question.objects.filter(
            survey_id=survey_id,
            order__lt=self.object.order,
            is_active=True
        ).order_by('-order').first()
        
        if prev_question:
            self._swap_positions(self.object, prev_question)
            messages.success(request, _('Orden de pregunta actualizado'))
        else:
            messages.info(request, _('La pregunta ya está en la primera posición'))
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Orden actualizado'),
                'redirect': self.get_success_url()
            })
            
        return redirect(self.get_success_url())


class QuestionMoveDownView(QuestionMoveView):
    """
    Vista para mover una pregunta hacia abajo en el orden
    """
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        survey_id = self.object.survey.id
        
        # Buscar la siguiente pregunta
        next_question = Question.objects.filter(
            survey_id=survey_id,
            order__gt=self.object.order,
            is_active=True
        ).order_by('order').first()
        
        if next_question:
            self._swap_positions(self.object, next_question)
            messages.success(request, _('Orden de pregunta actualizado'))
        else:
            messages.info(request, _('La pregunta ya está en la última posición'))
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Orden actualizado'),
                'redirect': self.get_success_url()
            })
            
        return redirect(self.get_success_url())


class QuestionBulkReorderView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para reordenar múltiples preguntas a la vez mediante arrastrar y soltar
    """
    permission_required = 'survey.change_question'
    model = Survey
    http_method_names = ['post']
    fields = []
    
    def post(self, request, *args, **kwargs):
        survey = self.get_object()
        
        try:
            # Recibir la lista de IDs en el nuevo orden
            question_ids = request.POST.getlist('question_ids[]')
            
            if not question_ids:
                return JsonResponse({
                    'success': False,
                    'message': _('No se recibieron IDs de preguntas')
                }, status=400)
            
            # Actualizar el orden de cada pregunta
            order = 10
            for question_id in question_ids:
                try:
                    question = Question.objects.get(id=question_id, survey=survey)
                    question.order = order
                    question.save(update_fields=['order'])
                    order += 10
                except Question.DoesNotExist:
                    pass
            
            return JsonResponse({
                'success': True,
                'message': _('Preguntas reordenadas con éxito')
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)


class QuestionPreviewView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para previsualizar una pregunta como se verá en la encuesta
    """
    permission_required = 'survey.view_question'
    model = Question
    template_name = 'encuestas/question_preview.html'
    fields = []  # No modificamos campos, solo visualizamos
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Previsualización de Pregunta')
        context['entity'] = _('Pregunta')
        context['list_url'] = reverse_lazy('encuestas:question_list', args=[self.object.survey.id])
        
        # Si la pregunta tiene opciones, cargarlas
        if self.object.has_choices:
            context['choices'] = self.object.choices.filter(is_active=True).order_by('order')
        
        return context