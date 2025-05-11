import json
from django.db.models import Q, Max
from django.utils.translation import gettext as _
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, ListView

from apps.surveys.forms.questionchoice_form import QuestionChoiceForm
from apps.surveys.models.surveymodel import Question, QuestionChoice

from django.db import transaction  # Add this import at the top
from django.views import View
from django.http import JsonResponse
import json

# views.py
class QuestionChoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear una nueva opción para una pregunta
    """
    permission_required = 'survey.add_questionchoice'
    model = QuestionChoice
    form_class = QuestionChoiceForm
    template_name = 'core/create.html'
    
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['question_id'] = self.kwargs.get('question_id')
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('encuestas:choice_list', args=[self.object.question.id])
    
    def form_valid(self, form):
        self.object = form.save()
        
        messages.success(self.request, _('Opción creada con éxito'))
        
        # Check if it's an AJAX request
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Opción creada con éxito'),
                'id': self.object.id,
                'text': self.object.text,
                'value': self.object.value,
                'order': self.object.order
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
        context['title'] = _('Crear Opción')
        context['entity'] = _('Opción')
        context['question'] = self.question  # Use self.question instead of accessing through self.object
        context['list_url'] = reverse_lazy('encuestas:choice_list', args=[self.kwargs.get('question_id')])  # Get from kwargs
        context['action'] = 'add'
        return context


class QuestionChoiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para actualizar una opción existente
    """
    permission_required = 'survey.change_questionchoice'
    model = QuestionChoice
    form_class = QuestionChoiceForm
    template_name = 'core/create.html'
    
    def get_success_url(self):
        return reverse_lazy('encuestas:choice_list', args=[self.object.question.id])
    
    def form_valid(self, form):
        self.object = form.save()
        
        messages.success(self.request, _('Opción actualizada con éxito'))
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Opción actualizada con éxito'),
                'id': self.object.id,
                'text': self.object.text,
                'value': self.object.value,
                'order': self.object.order
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
        context['title'] = _('Editar Opción')
        context['entity'] = _('Opción')
        context['list_url'] = reverse_lazy('encuestas:question_detail', args=[self.object.question.id])
        context['action'] = 'edit'
        return context


class QuestionChoiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Vista para eliminar una opción
    """
    permission_required = 'survey.delete_questionchoice'
    model = QuestionChoice
    template_name = 'core/delete.html'
    
    def get_success_url(self):
        return reverse_lazy('encuestas:question_detail', args=[self.object.question.id])
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Perform the delete action
        self.object.delete()
        
        messages.success(request, _('Opción eliminada con éxito'))
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('Opción eliminada con éxito')
            })
        
        return HttpResponseRedirect(success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Eliminar Opción')
        context['entity'] = _('Opción')
        context['list_url'] = reverse_lazy('encuestas:question_detail', args=[self.object.question.id])
        context['action'] = 'delete'
        return context


class QuestionChoiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista para listar todas las opciones de una pregunta
    """
    permission_required = 'survey.view_questionchoice'
    model = QuestionChoice
    template_name = 'surveys/question-choice.html'
    context_object_name = 'choices'
    
    def get_success_url(self):
        # Change this to use choice_list instead of question_detail
        return reverse_lazy('encuestas:choice_list', args=[self.object.question.id])

    def get_queryset(self):
        self.question = get_object_or_404(Question, pk=self.kwargs.get('question_id'))
        return QuestionChoice.objects.filter(question=self.question, is_active=True).order_by('order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self.question
        context['survey'] = self.question.survey
        return context


class QuestionChoiceReorderView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista para reordenar las opciones de una pregunta mediante AJAX
    """
    permission_required = 'survey.change_questionchoice'
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            
            with transaction.atomic():
                for item in data:
                    choice = QuestionChoice.objects.get(id=item['id'])
                    choice.order = item['order']
                    choice.save(update_fields=['order'])
                
            return JsonResponse({
                'success': True,
                'message': _('Orden actualizado con éxito')
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    """
    Vista para crear múltiples opciones a la vez para una pregunta
    """
    permission_required = 'survey.add_questionchoice'
    model = Question
    template_name = 'encuestas/choice_bulk_create.html'
    fields = []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Crear Múltiples Opciones')
        context['entity'] = _('Opciones')
        context['question'] = self.get_object()
        context['list_url'] = reverse_lazy('encuestas:choice_list', args=[self.get_object().id])
        return context
    
    def post(self, request, *args, **kwargs):
        question = self.get_object()
        
        try:
            # Obtener texto de opciones separado por líneas
            options_text = request.POST.get('options_text', '').strip()
            if not options_text:
                return JsonResponse({
                    'success': False,
                    'message': _('Debe ingresar al menos una opción')
                }, status=400)
            
            # Dividir por líneas y filtrar líneas vacías
            options_list = [line.strip() for line in options_text.split('\n') if line.strip()]
            
            # Obtener el orden máximo actual
            max_order = QuestionChoice.objects.filter(
                question=question
            ).aggregate(Max('order'))['order__max'] or 0
            order = max_order + 10
            
            # Crear cada opción
            created_options = []
            for text in options_list:
                choice = QuestionChoice(
                    question=question,
                    text=text,
                    order=order
                )
                choice.save()
                created_options.append(choice)
                order += 10
            
            messages.success(request, _('Se crearon {} opciones correctamente').format(len(created_options)))
            
            return JsonResponse({
                'success': True,
                'message': _('Opciones creadas con éxito'),
                'redirect': reverse('encuestas:choice_list', args=[question.id])
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
        
