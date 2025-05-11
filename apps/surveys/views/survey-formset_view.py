# from django.db.models import Max
# from django.utils.translation import gettext as _
# from django.contrib import messages
# from django.shortcuts import redirect, get_object_or_404
# from django.http import JsonResponse
# from django.urls import reverse_lazy, reverse
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.views.generic import CreateView, UpdateView, FormView

# from apps.surveys.forms.question_form import QuestionForm
# from apps.surveys.forms.questionchoice_form import BulkChoiceCreationForm, QuestionChoiceInlineFormSet, SurveyQuestionFormSet
# from apps.surveys.forms.survey_form import (
#     SurveyForm
#     )
# from apps.surveys.models.surveymodel import (
#     Question,
#     QuestionChoice,
#     Survey
#     )

# # from .models import Survey, Question, QuestionChoice
# # from .forms import (SurveyForm, QuestionFormSet, SurveyQuestionFormSet, 
# #                    QuestionChoiceFormSet, QuestionChoiceInlineFormSet,
# #                    BulkChoiceCreationForm)


# class SurveyWithQuestionsCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
#     """
#     Vista para crear una encuesta con sus preguntas en una sola página
#     """
#     permission_required = 'survey.add_survey'
#     model = Survey
#     form_class = SurveyForm
#     template_name = 'encuestas/survey_with_questions_form.html'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Crear Encuesta con Preguntas')
#         context['entity'] = _('Encuesta')
#         context['list_url'] = reverse_lazy('encuestas:survey_list')
        
#         # Agregar formset de preguntas
#         if self.request.POST:
#             context['question_formset'] = SurveyQuestionFormSet(self.request.POST)
#         else:
#             context['question_formset'] = SurveyQuestionFormSet()
            
#         return context
    
#     def form_valid(self, form):
#         context = self.get_context_data()
#         question_formset = context['question_formset']
        
#         if question_formset.is_valid():
#             # Guardar la encuesta
#             self.object = form.save()
            
#             # Asignar la encuesta al formset y guardar
#             question_formset.instance = self.object
#             question_formset.save()
            
#             messages.success(self.request, _('Encuesta y preguntas creadas con éxito'))
#             return redirect(self.get_success_url())
#         else:
#             return self.form_invalid(form)
    
#     def get_success_url(self):
#         return reverse_lazy('encuestas:survey_detail', args=[self.object.id])


# class SurveyWithQuestionsUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
#     """
#     Vista para editar una encuesta con sus preguntas en una sola página
#     """
#     permission_required = 'survey.change_survey'
#     model = Survey
#     form_class = SurveyForm
#     template_name = 'encuestas/survey_with_questions_form.html'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Editar Encuesta con Preguntas')
#         context['entity'] = _('Encuesta')
#         context['list_url'] = reverse_lazy('encuestas:survey_list')
        
#         # Agregar formset de preguntas
#         if self.request.POST:
#             context['question_formset'] = SurveyQuestionFormSet(
#                 self.request.POST, 
#                 instance=self.object
#             )
#         else:
#             context['question_formset'] = SurveyQuestionFormSet(
#                 instance=self.object
#             )
            
#         return context
    
#     def form_valid(self, form):
#         context = self.get_context_data()
#         question_formset = context['question_formset']
        
#         if question_formset.is_valid():
#             # Guardar la encuesta
#             self.object = form.save()
            
#             # Guardar el formset
#             question_formset.save()
            
#             messages.success(self.request, _('Encuesta y preguntas actualizadas con éxito'))
#             return redirect(self.get_success_url())
#         else:
#             return self.form_invalid(form)
    
#     def get_success_url(self):
#         return reverse_lazy('encuestas:survey_detail', args=[self.object.id])


# class QuestionWithChoicesCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
#     """
#     Vista para crear una pregunta con sus opciones en una sola página
#     """
#     permission_required = 'survey.add_question'
#     model = Question
#     form_class = QuestionForm
#     template_name = 'encuestas/question_with_choices_form.html'
    
#     def get_initial(self):
#         """Prepopular el formulario con la encuesta seleccionada"""
#         initial = super().get_initial()
#         self.survey = get_object_or_404(Survey, pk=self.kwargs.get('survey_id'))
#         initial['survey'] = self.survey
        
#         # Obtener el máximo orden y añadir 10 para la nueva pregunta
#         max_order = Question.objects.filter(survey=self.survey).aggregate(Max('order'))['order__max'] or 0
#         initial['order'] = max_order + 10
        
#         return initial
    
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['survey_id'] = self.kwargs.get('survey_id')
#         return kwargs
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Crear Pregunta con Opciones')
#         context['entity'] = _('Pregunta')
#         context['survey'] = get_object_or_404(Survey, pk=self.kwargs.get('survey_id'))
#         context['list_url'] = reverse_lazy('encuestas:question_list', args=[self.kwargs.get('survey_id')])
        
#         # Agregar formset de opciones
#         if self.request.POST:
#             context['choice_formset'] = QuestionChoiceInlineFormSet(self.request.POST)
#         else:
#             context['choice_formset'] = QuestionChoiceInlineFormSet()
            
#         return context
    
#     def form_valid(self, form):
#         context = self.get_context_data()
#         choice_formset = context['choice_formset']
        
#         if choice_formset.is_valid():
#             # Guardar la pregunta
#             self.object = form.save()
            
#             # Asignar la pregunta al formset y guardar
#             choice_formset.instance = self.object
#             choice_formset.save()
            
#             messages.success(self.request, _('Pregunta y opciones creadas con éxito'))
#             return redirect(self.get_success_url())
#         else:
#             return self.form_invalid(form)
    
#     def get_success_url(self):
#         return reverse_lazy('encuestas:question_list', args=[self.kwargs.get('survey_id')])


# class QuestionWithChoicesUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
#     """
#     Vista para editar una pregunta con sus opciones en una sola página
#     """
#     permission_required = 'survey.change_question'
#     model = Question
#     form_class = QuestionForm
#     template_name = 'encuestas/question_with_choices_form.html'
    
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['survey_id'] = self.object.survey.id
#         return kwargs
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = _('Editar Pregunta con Opciones')
#         context['entity'] = _('Pregunta')
#         context['survey'] = self.object.survey
#         context['list_url'] = reverse_lazy('encuestas:question_list', args=[self.object.survey.id])
        
#         # Agregar formset de opciones
#         if self.request.POST:
#             context['choice_formset'] = QuestionChoiceInlineFormSet(
#                 self.request.POST, 
#                 instance=self.object
#             )
#         else:
#             context['choice_formset'] = QuestionChoiceInlineFormSet(
#                 instance=self.object
#             )
            
#         return context
    
#     def form_valid(self, form):
#         context = self.get_context_data()
#         choice_formset = context['choice_formset']
        
#         if choice_formset.is_valid():
#             # Guardar la pregunta
#             self.object = form.save()
            
#             # Guardar el formset
#             choice_formset.save()
            
#             messages.success(self.request, _('Pregunta y opciones actualizadas con éxito'))
#             return redirect(self.get_success_url())
#         else:
#             return self.form_invalid(form)
    
#     def get_success_url(self):
#         return reverse_lazy('encuestas:question_list', args=[self.object.survey.id])


# class BulkChoiceCreationView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
#     """
#     Vista para crear múltiples opciones a la vez para una pregunta
#     """
#     permission_required = 'survey.add_questionchoice'
#     template_name = 'encuestas/bulk_choice_creation.html'
#     form_class = BulkChoiceCreationForm
    
#     def get_question(self):
#         return get_object_or_404(Question, pk=self.kwargs.get('question_id'))
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         question = self.get_question()
        
#         context['title'] = _('Crear Múltiples Opciones')
#         context['entity'] = _('Opciones')
#         context['question'] = question
#         context['survey'] = question.survey
#         context['list_url'] = reverse_lazy('encuestas:choice_list', args=[question.id])
        
#         return context
    
#     def form_valid(self, form):
#         question = self.get_question()
#         options_list = form.cleaned_data['options_text']
#         starting_order = form.cleaned_data['starting_order']
#         order_increment = form.cleaned_data['order_increment']
        
#         # Crear cada opción
#         created_options = []
#         order = starting_order
        
#         for text in options_list:
#             choice = QuestionChoice(
#                 question=question,
#                 text=text,
#                 order=order
#             )
#             choice.save()
#             created_options.append(choice)
#             order += order_increment
        
#         messages.success(
#             self.request, 
#             _('Se crearon {} opciones correctamente').format(len(created_options))
#         )
        
#         return redirect(self.get_success_url())
    
#     def get_success_url(self):
#         return reverse_lazy('encuestas:choice_list', args=[self.kwargs.get('question_id')])