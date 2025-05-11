import datetime
import math
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView
# from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.db import transaction
from django.utils.translation import gettext as _
from django.utils import timezone

from apps.base.models.support import QuestionType
from apps.surveys.forms.survey_form import ResponseForm
from apps.surveys.models.surveymodel import Answer, AnswerChoice, Period, QuestionChoice, Response, Survey


class ResponseListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista para listar todas las respuestas de una encuesta específica
    """
    permission_required = 'surveys.view_response'
    model = Response
    context_object_name = 'responses'
    template_name = 'surveys/response_list.html'
    
    def get_queryset(self):
        """Filtrar respuestas por survey_id"""
        survey_id = self.kwargs.get('survey_id')
        return Response.objects.filter(
            survey_id=survey_id, 
            is_active=True
        ).select_related('respondent', 'period').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey_id = self.kwargs.get('survey_id')
        context['survey'] = get_object_or_404(Survey, pk=survey_id)
        context['title'] = _('Respuestas para: ') + context['survey'].title
        
        # Estadísticas básicas
        context['total_responses'] = context['responses'].count()
        context['complete_responses'] = context['responses'].filter(is_complete=True).count()
        context['incomplete_responses'] = context['total_responses'] - context['complete_responses']
        
        # Filtrar por fecha
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                context['responses'] = context['responses'].filter(created_at__date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                context['responses'] = context['responses'].filter(created_at__date__lte=end_date)
            except ValueError:
                pass
        
        # URLs para acciones
        context['return_url'] = reverse('encuestas:survey_detail', kwargs={'pk': survey_id})
        context['export_url'] = reverse('encuestas:survey_export', kwargs={'pk': survey_id})
        
        return context


class ResponseDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Vista para ver los detalles de una respuesta específica, incluyendo
    todas las respuestas a las preguntas individuales
    """
    permission_required = 'surveys.view_response'
    model = Response
    context_object_name = 'response'
    template_name = 'surveys/response_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener la encuesta asociada
        context['survey'] = self.object.survey
        context['title'] = _('Detalle de Respuesta')
        
        # Obtener todas las respuestas a preguntas, con sus opciones seleccionadas si las hay
        context['answers'] = self.object.answers.prefetch_related(
            'selected_choices__choice',
            'question'
        ).order_by('question__order')
        
        # Información del encuestado
        context['respondent_info'] = {
            'nombre': self.object.respondent.get_full_name() if self.object.respondent else self.object.respondent_name,
            'email': self.object.respondent.email if self.object.respondent else self.object.respondent_email,
            'ip': self.object.respondent_ip,
            'fecha_inicio': self.object.started_at,
            'fecha_completado': self.object.completed_at,
            'estado': _('Completada') if self.object.is_complete else _('Incompleta')
        }
        
        # URLs para acciones
        context['return_url'] = reverse('encuestas:response_list', kwargs={'survey_id': self.object.survey.id})
        
        return context


class SurveyResponseCreateView(CreateView):
    """Public view for filling out a survey"""
    model = Response
    form_class = ResponseForm
    template_name = 'surveys/response_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Check if survey exists and is published"""
        survey_id = self.kwargs.get('survey_id')
        self.survey = get_object_or_404(
            Survey, 
            pk=survey_id, 
            is_active=True, 
            is_published=True
        )
        
        # Check if survey is within valid dates
        today = timezone.now().date()
        if self.survey.start_date and self.survey.start_date > today:
            messages.error(request, 'This survey is not yet available.')
            return redirect('encuestas:survey_unavailable')
        
        if self.survey.end_date and self.survey.end_date < today:
            messages.error(request, 'This survey is no longer available.')
            return redirect('encuestas:survey_unavailable')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        context['questions'] = self.survey.questions.filter(is_active=True).order_by('order')
        return context
    
    def form_valid(self, form):
        """Save the response with respondent info"""
        with transaction.atomic():
            # Set response metadata
            form.instance.survey = self.survey
            form.instance.respondent_ip = self.request.META.get('REMOTE_ADDR')
            
            # Set respondent if user is logged in
            if self.request.user.is_authenticated:
                form.instance.respondent = self.request.user
            
            # Set period if applicable (current month/year)
            now = timezone.now()
            try:
                month_name = now.strftime('%B').upper()
                period = Period.objects.get(month=month_name, year=now.year)
                form.instance.period = period
            except Period.DoesNotExist:
                # No period for current month/year
                pass
            
            # Mark as completed
            form.instance.is_complete = True
            form.instance.completed_at = now
            
            response = form.save()
            
            # Process and save individual question answers
            self._save_answers(response)
        
        messages.success(self.request, 'Thank you for completing the survey!')
        return HttpResponseRedirect(self.get_success_url())
    
    def _save_answers(self, response):
        """Save individual answers from the form data"""
        survey_questions = self.survey.questions.filter(is_active=True)
        
        for question in survey_questions:
            # Skip questions that were not shown (conditional logic)
            question_id = str(question.id)
            if question_id not in self.request.POST:
                continue
            
            # Create answer object
            answer = Answer(
                response=response,
                question=question,
                created_by=self.request.user if self.request.user.is_authenticated else None,
                modified_by=self.request.user if self.request.user.is_authenticated else None
            )
            
            # Save appropriate answer type based on question type
            question_type = question.question_type.name
            answer_value = self.request.POST.get(question_id)
            
            if question_type == QuestionType.TEXT or question_type == QuestionType.TEXT_AREA:
                answer.text_answer = answer_value
            
            elif question_type == QuestionType.NUMBER:
                try:
                    answer.number_answer = float(answer_value) if answer_value else None
                except ValueError:
                    answer.text_answer = answer_value  # Fallback if not a valid number
            
            elif question_type == QuestionType.DATE:
                try:
                    # En lugar de asignar directamente, validemos el formato primero
                    if answer_value and answer_value.strip():
                        # Intentar convertir al formato correcto
                        from datetime import datetime
                        
                        # Verificar varios formatos posibles
                        formats_to_try = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']
                        parsed_date = None
                        
                        for date_format in formats_to_try:
                            try:
                                date_obj = datetime.strptime(answer_value, date_format)
                                # Convertir al formato que Django espera (YYYY-MM-DD)
                                parsed_date = date_obj.strftime('%Y-%m-%d')
                                break
                            except ValueError:
                                continue
                        
                        if parsed_date:
                            # Si pudimos parsear la fecha correctamente
                            answer.date_answer = parsed_date
                        else:
                            # No pudimos parsear, guardamos como texto
                            answer.text_answer = answer_value
                            answer.date_answer = None
                    else:
                        # Si está vacío, asegurarnos de que date_answer sea None
                        answer.date_answer = None
                except Exception as e:
                    # Cualquier otro error, asegurarnos de que date_answer sea None
                    answer.text_answer = answer_value
                    answer.date_answer = None
                    # Registrar el error
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error procesando fecha '{answer_value}' para pregunta {question.id}: {e}")
            
            elif question_type == QuestionType.YES_NO:
                answer.boolean_answer = answer_value.upper() == 'YES'
            
            elif question_type == QuestionType.RATING:
                try:
                    answer.number_answer = float(answer_value) if answer_value else None
                except ValueError:
                    pass
                
                # Also save as a choice selection
                answer.save()
                
                # Find and save the selected choice
                try:
                    # Use filter() and first() instead of get() to handle duplicate choices
                    choices = QuestionChoice.objects.filter(question=question, value=answer_value)
                    if choices.exists():
                        choice = choices.first()  # Take the first one
                        AnswerChoice.objects.create(
                            answer=answer,
                            choice=choice,
                            created_by=answer.created_by,
                            modified_by=answer.modified_by
                        )
                except Exception as e:
                    # Log the error but continue
                    print(f"Error saving choice for question {question.id}: {e}")
                
                continue  # Skip the save below since we already saved for choice association
            
            elif question_type == QuestionType.SINGLE_CHOICE:
                # Save as text for the main answer
                answer.text_answer = answer_value
                answer.save()
                
                # Find and save the selected choice
                try:
                    # Use filter() and first() instead of get() to handle duplicate choices
                    choices = QuestionChoice.objects.filter(question=question, value=answer_value)
                    if choices.exists():
                        choice = choices.first()  # Take the first one
                        AnswerChoice.objects.create(
                            answer=answer,
                            choice=choice,
                            created_by=answer.created_by,
                            modified_by=answer.modified_by
                        )
                except Exception as e:
                    # Log the error but continue
                    print(f"Error saving choice for question {question.id}: {e}")
                
                continue  # Skip the save below since we already saved for choice association
            
            elif question_type == QuestionType.MULTIPLE_CHOICE:
                # For multiple choice, answers come as a list
                answer.text_answer = ", ".join(self.request.POST.getlist(question_id))
                answer.save()
                
                # Find and save each selected choice
                for choice_value in self.request.POST.getlist(question_id):
                    try:
                        # Use filter() and first() instead of get() to handle duplicate choices
                        choices = QuestionChoice.objects.filter(question=question, value=choice_value)
                        if choices.exists():
                            choice = choices.first()  # Take the first one
                            AnswerChoice.objects.create(
                                answer=answer,
                                choice=choice,
                                created_by=answer.created_by,
                                modified_by=answer.modified_by
                            )
                    except Exception as e:
                        # Log the error but continue
                        print(f"Error saving choice for question {question.id}: {e}")
                
                continue  # Skip the save below since we already saved for choice association
            
            # Save the answer for non-choice questions
            answer.save()

    def get_success_url(self):
        return reverse('encuestas:survey_thank_you')



class SurveyThankYouView(TemplateView):
    """Mostrar página de agradecimiento después de completar la encuesta"""
    template_name = 'surveys/thank_you.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('¡Gracias por su participación!')
        context['message'] = _('Su respuesta ha sido registrada exitosamente.')
        return context


class SurveyUnavailableView(TemplateView):
    """Mostrar mensaje de no disponible si la encuesta no está activa"""
    template_name = 'surveys/survey_unavailable.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Encuesta No Disponible')
        context['message'] = _('La encuesta solicitada no está disponible en este momento.')
        return context


class SurveyPreviewView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    Vista para previsualizar una encuesta antes de publicarla
    Permite ver cómo se mostrará la encuesta a los encuestados sin crear respuestas reales
    """
    permission_required = 'surveys.view_survey'
    model = Survey
    template_name = 'surveys/survey_preview.html'
    context_object_name = 'survey'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Datos básicos
        context['title'] = _('Previsualización de Encuesta')
        context['entity'] = _('Encuesta')
        
        # Obtener las preguntas ordenadas
        context['questions'] = self.object.questions.filter(
            is_active=True
        ).prefetch_related(
            'choices'
        ).order_by('order')
        
        # Verificar si hay preguntas
        context['has_questions'] = context['questions'].exists()
        
        # Simular el formulario de respuesta
        context['form'] = ResponseForm()
        
        # Estadísticas y estado actual
        context['is_preview'] = True
        context['today'] = timezone.now().date()
        context['published'] = self.object.is_published
        
        # Comprobar si estaría activa según fechas
        is_in_date_range = True
        if self.object.start_date and self.object.start_date > context['today']:
            is_in_date_range = False
            context['not_available_reason'] = _('Esta encuesta aún no está disponible. Fecha de inicio: {}'.format(
                self.object.start_date.strftime('%d/%m/%Y')))
        
        if self.object.end_date and self.object.end_date < context['today']:
            is_in_date_range = False
            context['not_available_reason'] = _('Esta encuesta ya ha finalizado. Fecha de fin: {}'.format(
                self.object.end_date.strftime('%d/%m/%Y')))
        
        context['is_active'] = self.object.is_published and is_in_date_range
        
        # URLs para acciones relacionadas
        context['return_url'] = reverse('encuestas:survey_detail', kwargs={'pk': self.object.pk})
        
        if not self.object.is_published:
            context['publish_url'] = reverse('encuestas:survey_publish', kwargs={'pk': self.object.pk})
        else:
            context['unpublish_url'] = reverse('encuestas:survey_unpublish', kwargs={'pk': self.object.pk})
        
        context['edit_url'] = reverse('encuestas:survey_update', kwargs={'pk': self.object.pk})
        context['question_list_url'] = reverse('encuestas:question_list', kwargs={'survey_id': self.object.pk})
        
        return context