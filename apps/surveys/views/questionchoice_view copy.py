# from django.db.models import Q, Max
# from django.utils.translation import gettext as _
# from django.contrib import messages
# from django.shortcuts import redirect, get_object_or_404
# from django.http import JsonResponse
# from django.urls import reverse_lazy, reverse
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.views.generic import CreateView, UpdateView, DeleteView, ListView

# from apps.surveys.forms.questionchoice_form import QuestionChoiceForm
# from apps.surveys.models.surveymodel import Question, QuestionChoice

# # from .models import Question, QuestionChoice
# # from .forms import QuestionChoiceForm


# class ChoiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
#     """
#     Vista para listar opciones de una pregunta específica
#     """
#     permission_required = 'survey.view_questionchoice'
#     model = QuestionChoice
#     template_name = 'encuestas/choice_list.html'
#     context_object_name = 'choices'
    
#     def get_queryset(self):
#         """Filtrar opciones por la pregunta seleccionada"""
#         self.question = get_object_or_404(Question, pk=self.kwargs.get('question_id'))
#         return QuestionChoice.objects.filter(question=self.question, is_active=True).order_by('order')
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Opciones de Respuesta')
#         context['entity'] = _('Opción')
#         context['question'] = self.question
#         context['list_url'] = reverse('encuestas:choice_list', args=[self.question.id])
#         context['create_url'] = reverse('encuestas:choice_create', args=[self.question.id])
#         context['return_url'] = reverse('encuestas:question_list', args=[self.question.survey.id])
        
#         # Configuración de acciones para cada opción
#         context['actions'] = [
#             {
#                 'name': 'edit',
#                 'label': '',
#                 'icon': 'edit',
#                 'color': 'secondary',
#                 'color2': 'brown',
#                 'url': 'encuestas:choice_update',
#                 'modal': True
#             },
#             {
#                 'name': 'del',
#                 'label': '',
#                 'icon': 'delete',
#                 'color': 'danger',
#                 'color2': 'white',
#                 'url': 'encuestas:choice_delete',
#                 'modal': True
#             },
#             {
#                 'name': 'up',
#                 'label': '',
#                 'icon': 'arrow_upward',
#                 'color': 'primary',
#                 'color2': 'white',
#                 'url': 'encuestas:choice_move_up',
#                 'modal': False
#             },
#             {
#                 'name': 'down',
#                 'label': '',
#                 'icon': 'arrow_downward',
#                 'color': 'primary',
#                 'color2': 'white',
#                 'url': 'encuestas:choice_move_down',
#                 'modal': False
#             }
#         ]
        
#         return context


# class ChoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
#     """
#     Vista para crear una nueva opción para una pregunta específica
#     """
#     permission_required = 'survey.add_questionchoice'
#     model = QuestionChoice
#     form_class = QuestionChoiceForm
#     template_name = 'core/create.html'
    
#     def get_initial(self):
#         """Prepopular el formulario con la pregunta seleccionada"""
#         initial = super().get_initial()
#         self.question = get_object_or_404(Question, pk=self.kwargs.get('question_id'))
#         initial['question'] = self.question
        
#         # Obtener el máximo orden y añadir 10 para la nueva opción
#         max_order = QuestionChoice.objects.filter(question=self.question).aggregate(Max('order'))['order__max'] or 0
#         initial['order'] = max_order + 10
        
#         return initial
    
#     def get_success_url(self):
#         return reverse_lazy('encuestas:choice_list', args=[self.kwargs.get('question_id')])
    
#     def form_valid(self, form):
#         # Guardar la opción - la auditoría se maneja por señales
#         self.object = form.save()
        
#         messages.success(self.request, _('Opción creada con éxito'))
        
#         # Verificar si es una solicitud AJAX
#         if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': True,
#                 'message': _('Opción creada con éxito'),
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
#         context['title'] = _('Crear Opción')
#         context['entity'] = _('Opción')
#         context['question'] = get_object_or_404(Question, pk=self.kwargs.get('question_id'))
#         context['list_url'] = reverse_lazy('encuestas:choice_list', args=[self.kwargs.get('question_id')])
#         context['action'] = 'add'
#         return context


# class ChoiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
#     """
#     Vista para actualizar una opción existente
#     """
#     permission_required = 'survey.change_questionchoice'
#     model = QuestionChoice
#     form_class = QuestionChoiceForm
#     template_name = 'core/create.html'
    
#     def get_success_url(self):
#         return reverse_lazy('encuestas:choice_list', args=[self.object.question.id])
    
#     def form_valid(self, form):
#         self.object = form.save(commit=True)
        
#         messages.success(self.request, _('Opción actualizada con éxito'))
        
#         if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': True,
#                 'message': _('Opción actualizada con éxito'),
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
#         context['title'] = _('Editar Opción')
#         context['entity'] = _('Opción')
#         context['list_url'] = reverse_lazy('encuestas:choice_list', args=[self.object.question.id])
#         context['action'] = 'edit'
#         return context


# class ChoiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
#     """
#     Vista para eliminar una opción
#     """
#     permission_required = 'survey.delete_questionchoice'
#     model = QuestionChoice
#     template_name = 'core/del.html'
#     context_object_name = 'Opción'
    
#     def get_success_url(self):
#         return reverse_lazy('encuestas:choice_list', args=[self.object.question.id])
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Eliminar Opción')
#         context['entity'] = _('Opción')
#         context['texto'] = f'¿Seguro de eliminar la opción "{self.object.text}"?'
#         context['list_url'] = reverse_lazy('encuestas:choice_list', args=[self.object.question.id])
#         return context
    
#     def delete(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         question_id = self.object.question.id
        
#         try:
#             # La auditoría se maneja automáticamente con la señal post_delete
#             self.object.delete()
#             messages.success(request, _('Opción eliminada con éxito'))
            
#             # Reordenar las opciones restantes
#             self._reorder_choices(question_id)
            
#             if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                 return JsonResponse({
#                     'success': True,
#                     'message': _('Opción eliminada con éxito'),
#                     'redirect': self.get_success_url()
#                 })
                
#             return redirect(self.get_success_url())
            
#         except Exception as e:
#             # Capturar errores de integridad referencial
#             error_message = _('No se puede eliminar la opción porque está siendo utilizada en respuestas')
            
#             if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                 return JsonResponse({
#                     'success': False,
#                     'message': error_message
#                 }, status=400)
                
#             messages.error(request, error_message)
#             return redirect(self.get_success_url())
    
#     def _reorder_choices(self, question_id):
#         """Reordenar las opciones después de eliminar una"""
#         choices = QuestionChoice.objects.filter(question_id=question_id, is_active=True).order_by('order')
#         order = 10
#         for choice in choices:
#             if choice.order != order:
#                 choice.order = order
#                 choice.save(update_fields=['order'])
#             order += 10


# class ChoiceMoveView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
#     """
#     Vista base para mover opciones arriba o abajo en el orden
#     """
#     permission_required = 'survey.change_questionchoice'
#     model = QuestionChoice
#     http_method_names = ['post']
#     fields = ['order']
    
#     def get_success_url(self):
#         return reverse_lazy('encuestas:choice_list', args=[self.object.question.id])
    
#     def _swap_positions(self, choice, other_choice):
#         """Intercambiar posiciones entre dos opciones"""
#         temp_order = choice.order
#         choice.order = other_choice.order
#         other_choice.order = temp_order
        
#         # Guardar ambos objetos - las señales de auditoría registrarán los cambios
#         choice.save(update_fields=['order'])
#         other_choice.save(update_fields=['order'])


# class ChoiceMoveUpView(ChoiceMoveView):
#     """
#     Vista para mover una opción hacia arriba en el orden
#     """
#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         question_id = self.object.question.id
        
#         # Buscar la opción anterior
#         prev_choice = QuestionChoice.objects.filter(
#             question_id=question_id,
#             order__lt=self.object.order,
#             is_active=True
#         ).order_by('-order').first()
        
#         if prev_choice:
#             self._swap_positions(self.object, prev_choice)
#             messages.success(request, _('Orden de opción actualizado'))
#         else:
#             messages.info(request, _('La opción ya está en la primera posición'))
        
#         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': True,
#                 'message': _('Orden actualizado'),
#                 'redirect': self.get_success_url()
#             })
            
#         return redirect(self.get_success_url())


# class ChoiceMoveDownView(ChoiceMoveView):
#     """
#     Vista para mover una opción hacia abajo en el orden
#     """
#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         question_id = self.object.question.id
        
#         # Buscar la siguiente opción
#         next_choice = QuestionChoice.objects.filter(
#             question_id=question_id,
#             order__gt=self.object.order,
#             is_active=True
#         ).order_by('order').first()
        
#         if next_choice:
#             self._swap_positions(self.object, next_choice)
#             messages.success(request, _('Orden de opción actualizado'))
#         else:
#             messages.info(request, _('La opción ya está en la última posición'))
        
#         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': True,
#                 'message': _('Orden actualizado'),
#                 'redirect': self.get_success_url()
#             })
            
#         return redirect(self.get_success_url())


# class ChoiceBulkCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
#     """
#     Vista para crear múltiples opciones a la vez para una pregunta
#     """
#     permission_required = 'survey.add_questionchoice'
#     model = Question
#     template_name = 'encuestas/choice_bulk_create.html'
#     fields = []
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Crear Múltiples Opciones')
#         context['entity'] = _('Opciones')
#         context['question'] = self.get_object()
#         context['list_url'] = reverse_lazy('encuestas:choice_list', args=[self.get_object().id])
#         return context
    
#     def post(self, request, *args, **kwargs):
#         question = self.get_object()
        
#         try:
#             # Obtener texto de opciones separado por líneas
#             options_text = request.POST.get('options_text', '').strip()
#             if not options_text:
#                 return JsonResponse({
#                     'success': False,
#                     'message': _('Debe ingresar al menos una opción')
#                 }, status=400)
            
#             # Dividir por líneas y filtrar líneas vacías
#             options_list = [line.strip() for line in options_text.split('\n') if line.strip()]
            
#             # Obtener el orden máximo actual
#             max_order = QuestionChoice.objects.filter(
#                 question=question
#             ).aggregate(Max('order'))['order__max'] or 0
#             order = max_order + 10
            
#             # Crear cada opción
#             created_options = []
#             for text in options_list:
#                 choice = QuestionChoice(
#                     question=question,
#                     text=text,
#                     order=order
#                 )
#                 choice.save()
#                 created_options.append(choice)
#                 order += 10
            
#             messages.success(request, _('Se crearon {} opciones correctamente').format(len(created_options)))
            
#             return JsonResponse({
#                 'success': True,
#                 'message': _('Opciones creadas con éxito'),
#                 'redirect': reverse('encuestas:choice_list', args=[question.id])
#             })
            
#         except Exception as e:
#             return JsonResponse({
#                 'success': False,
#                 'message': str(e)
#             }, status=500)