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
    """Public view for filling out a survey with pagination support"""
    model = Response
    form_class = ResponseForm
    template_name = 'surveys/response_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Check if survey exists and is published"""
        survey_id = self.kwargs.get('survey_id')
        # En lugar de filtrar por is_active, filtramos directamente por el campo real is_published
        # y verificamos las fechas manualmente
        self.survey = get_object_or_404(
            Survey, 
            pk=survey_id, 
            is_active=True, 
            is_published=True
        )
        
        # Check if survey is within valid dates
        today = timezone.now().date()
        if self.survey.start_date and self.survey.start_date > today:
            messages.error(request, _('Esta encuesta aún no está disponible.'))
            return redirect('encuestas:survey_unavailable')
        
        if self.survey.end_date and self.survey.end_date < today:
            messages.error(request, _('Esta encuesta ya no está disponible.'))
            return redirect('encuestas:survey_unavailable')
        
        # Initialize session data for this survey if it doesn't exist
        self._initialize_session_data()
        
        return super().dispatch(request, *args, **kwargs)
    
    def _initialize_session_data(self):
        """Initialize or retrieve session data for tracking survey progress"""
        survey_session_key = f'survey_{self.survey.id}'
        
        if survey_session_key not in self.request.session:
            self.request.session[survey_session_key] = {
                'started_at': timezone.now().timestamp(),
                'current_page': 1,
                'questions_per_page': self._get_default_questions_per_page(),
                'completed_questions': [],
                'partial_response_id': None,
            }
            self.request.session.modified = True
    
    def _get_default_questions_per_page(self):
        """Get default number of questions per page based on survey settings or cookie"""
        # Check if user has a preference stored in cookie
        user_preference = self.request.COOKIES.get('survey_questions_per_page')
        if user_preference and user_preference.isdigit():
            return int(user_preference)
        
        # Check if survey has a default setting 
        # En lugar de utilizar hasattr, verificamos si existe el campo questions_per_page en el modelo
        # utilizando try/except para evitar errores si el campo no existe en el modelo actual
        try:
            # Si el campo existe en el modelo, lo usamos
            if hasattr(self.survey, 'questions_per_page') and self.survey.questions_per_page:
                return self.survey.questions_per_page
        except AttributeError:
            # Si el campo no existe, no hacemos nada
            pass
        
        # Default: 5 questions per page
        return 5
    
    def _get_survey_session_data(self):
        """Get session data for the current survey"""
        survey_session_key = f'survey_{self.survey.id}'
        return self.request.session.get(survey_session_key, {})
    
    def _update_survey_session_data(self, data):
        """Update session data for the current survey"""
        survey_session_key = f'survey_{self.survey.id}'
        self.request.session[survey_session_key] = data
        self.request.session.modified = True
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests with pagination parameters"""
        # Get current session data
        session_data = self._get_survey_session_data()
        
        # Process pagination parameters from GET
        page = request.GET.get('page')
        questions_per_page = request.GET.get('questions_per_page')
        
        # Update page number if provided
        if page and page.isdigit():
            session_data['current_page'] = int(page)
        
        # Update questions per page if provided
        if questions_per_page and questions_per_page.isdigit():
            new_questions_per_page = int(questions_per_page)
            if 1 <= new_questions_per_page <= 100:  # Ampliar límites
                session_data['questions_per_page'] = new_questions_per_page
                
                # Set cookie for user preference (max age 30 days)
                self.set_questions_per_page_cookie = True
                self.new_questions_per_page = new_questions_per_page
        
        # Save updated session data
        self._update_survey_session_data(session_data)
        
        response = super().get(request, *args, **kwargs)
        
        # Set cookie if needed
        if hasattr(self, 'set_questions_per_page_cookie') and self.set_questions_per_page_cookie:
            response.set_cookie('survey_questions_per_page', str(self.new_questions_per_page), max_age=60*60*24*30)
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get basic survey information
        context['survey'] = self.survey
        all_questions = self.survey.questions.filter(is_active=True).order_by('order')
        context['total_questions'] = all_questions.count()
        
        # Get session data
        session_data = self._get_survey_session_data()
        current_page = session_data.get('current_page', 1)
        questions_per_page = session_data.get('questions_per_page', 5)
        
        # Handle "show all questions" case
        if questions_per_page >= context['total_questions']:
            questions_per_page = context['total_questions']
            current_page = 1
        
        # Calculate pagination values
        start_index = (current_page - 1) * questions_per_page
        end_index = min(start_index + questions_per_page, context['total_questions'])
        
        # Get questions for the current page
        context['questions'] = all_questions[start_index:end_index]
        
        # Calculate total pages
        import math
        total_pages = math.ceil(context['total_questions'] / questions_per_page) if context['total_questions'] > 0 and questions_per_page > 0 else 1
        context['total_pages'] = total_pages
        
        # Ensure current page is valid
        if current_page > total_pages:
            current_page = total_pages
            session_data['current_page'] = current_page
            self._update_survey_session_data(session_data)
        
        # Pagination context
        context['current_page'] = current_page
        context['questions_per_page'] = questions_per_page
        context['has_previous'] = current_page > 1
        context['has_next'] = current_page < total_pages
        context['previous_page'] = current_page - 1 if context['has_previous'] else None
        context['next_page'] = current_page + 1 if context['has_next'] else None
        
        # Page ranges for pagination UI
        # Para mostrar solo un rango de páginas en lugar de todas
        if total_pages <= 10:
            context['page_range'] = range(1, total_pages + 1)
        else:
            # Mostrar un rango limitado de páginas alrededor de la página actual
            start_range = max(1, current_page - 2)
            end_range = min(total_pages + 1, current_page + 3)
            context['page_range'] = range(start_range, end_range)
        
        # Questions per page options
        context['questions_per_page_options'] = [3, 5, 10, 20, 50, 100]
        
        # Progress information
        context['progress_percentage'] = int((current_page / total_pages) * 100) if total_pages > 0 else 0
        context['questions_answered'] = len(session_data.get('completed_questions', []))
        context['questions_total'] = context['total_questions']
        
        # Información sobre el usuario actual
        context['is_authenticated'] = self.request.user.is_authenticated
        if self.request.user.is_authenticated:
            context['user_full_name'] = self.request.user.get_full_name()
            context['user_email'] = self.request.user.email
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle post request for saving answers"""
        # Verificar si es una petición de autoguardado mediante AJAX
        is_auto_save = request.POST.get('auto_save') == 'true'
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_auto_save and is_ajax:
            # Para autoguardado, solo guardar respuestas sin validación completa
            self._save_partial_answers(request)
            return JsonResponse({'success': True, 'message': _('Respuestas guardadas automáticamente')})
            
        # Resto del código de post() existente
        session_data = self._get_survey_session_data()
        current_page = session_data.get('current_page', 1)
        questions_per_page = session_data.get('questions_per_page', 5)
        
        # Si form es enviado con "next" o "previous" button, guardar página actual y redirigir
        if 'next_page' in request.POST:
            # Validar y guardar respuestas de la página actual
            self._save_partial_answers(request)
            
            # Mover a la siguiente página
            session_data['current_page'] = current_page + 1
            self._update_survey_session_data(session_data)
            
            # Redirigir a GET para evitar reenvío del formulario
            return redirect(request.path + f'?page={current_page + 1}&questions_per_page={questions_per_page}')
        
        elif 'previous_page' in request.POST:
            # Guardar respuestas de la página actual
            self._save_partial_answers(request)
            
            # Mover a la página anterior
            session_data['current_page'] = max(1, current_page - 1)
            self._update_survey_session_data(session_data)
            
            # Redirigir a GET para evitar reenvío del formulario
            return redirect(request.path + f'?page={max(1, current_page - 1)}&questions_per_page={questions_per_page}')
        
        # Si el botón de envío fue clickeado, procesar el formulario completo
        elif 'submit_survey' in request.POST:
            # Guardar respuestas de la página actual
            self._save_partial_answers(request)
            
            # Crear o actualizar la respuesta
            return self._submit_complete_survey(request)
        
        # Por defecto: permanecer en la página actual
        return self.get(request, *args, **kwargs)
    
    def _save_partial_answers(self, request):
        """Save answers from the current page without completing the survey"""
        session_data = self._get_survey_session_data()
        
        # Get or create a partial response
        partial_response_id = session_data.get('partial_response_id')
        
        if partial_response_id:
            try:
                response = Response.objects.get(pk=partial_response_id)
            except Response.DoesNotExist:
                response = self._create_new_response(request)
                session_data['partial_response_id'] = response.id
        else:
            response = self._create_new_response(request)
            session_data['partial_response_id'] = response.id
        
        # Save answers for questions on the current page
        all_questions = list(self.survey.questions.filter(is_active=True).order_by('order'))
        current_page = session_data.get('current_page', 1)
        questions_per_page = session_data.get('questions_per_page', 5)
        
        # Special case for "display all questions"
        if questions_per_page >= len(all_questions):
            current_page_questions = all_questions
        else:
            start_index = (current_page - 1) * questions_per_page
            end_index = min(start_index + questions_per_page, len(all_questions))
            current_page_questions = all_questions[start_index:end_index]
        
        # Process and save answers for current page questions
        for question in current_page_questions:
            question_id = str(question.id)
            if question_id in request.POST:
                # Save the answer to this question
                self._save_answer(response, question, request)
                
                # Mark question as completed in session
                if question_id not in session_data.get('completed_questions', []):
                    completed_questions = session_data.get('completed_questions', [])
                    completed_questions.append(question_id)
                    session_data['completed_questions'] = completed_questions
        
        # Update session data
        self._update_survey_session_data(session_data)
    
    def _create_new_response(self, request):
        """Create a new response object"""
        response = Response(
            survey=self.survey,
            respondent_ip=request.META.get('REMOTE_ADDR'),
            started_at=timezone.now()
        )
        
        # Set respondent if user is logged in
        if request.user.is_authenticated:
            response.respondent = request.user
            response.respondent_name = request.user.get_full_name()
            response.respondent_email = request.user.email
        else:
            # For anonymous users, get from POST data
            response.respondent_name = request.POST.get('respondent_name', '')
            response.respondent_email = request.POST.get('respondent_email', '')
        
        # Mark as incomplete initially
        response.is_complete = False
        response.save()
        
        return response
    
    def _save_answer(self, response, question, request):
        """Save or update an answer for a specific question"""
        question_id = str(question.id)
        
        # Try to find existing answer for this question
        try:
            answer = Answer.objects.get(
                response=response,
                question=question
            )
        except Answer.DoesNotExist:
            # Create new answer
            answer = Answer(
                response=response,
                question=question,
                created_by=request.user if request.user.is_authenticated else None,
                modified_by=request.user if request.user.is_authenticated else None
            )
        
        # Update answer based on question type
        question_type = question.question_type.name
        
        if question_type == QuestionType.TEXT or question_type == QuestionType.TEXT_AREA:
            answer.text_answer = request.POST.get(question_id, '')
            
        elif question_type == QuestionType.NUMBER:
            try:
                answer.number_answer = float(request.POST.get(question_id, '')) if request.POST.get(question_id) else None
            except ValueError:
                answer.text_answer = request.POST.get(question_id, '')  # Fallback if not a valid number
            
        elif question_type == QuestionType.DATE:
            try:
                answer.date_answer = request.POST.get(question_id, None)
            except ValueError:
                answer.text_answer = request.POST.get(question_id, '')  # Fallback if not a valid date
            
        elif question_type == QuestionType.YES_NO:
            answer.boolean_answer = request.POST.get(question_id, '').upper() == 'YES'
            
        elif question_type == QuestionType.RATING:
            try:
                answer.number_answer = float(request.POST.get(question_id, '')) if request.POST.get(question_id) else None
            except ValueError:
                pass
            
            # Also save as a choice selection
            answer.save()
            
            # Find and save the selected choice
            try:
                if request.POST.get(question_id):
                    choice = QuestionChoice.objects.get(question=question, value=request.POST.get(question_id))
                    
                    # Check if this choice is already selected
                    if not AnswerChoice.objects.filter(answer=answer, choice=choice).exists():
                        # Clear previous selections for this answer
                        AnswerChoice.objects.filter(answer=answer).delete()
                        
                        # Create new selection
                        AnswerChoice.objects.create(
                            answer=answer,
                            choice=choice,
                            created_by=answer.created_by,
                            modified_by=answer.modified_by
                        )
            except QuestionChoice.DoesNotExist:
                pass
            
            return  # Skip the save below since we already saved for choice association
            
        elif question_type == QuestionType.SINGLE_CHOICE:
            # Save as text for the main answer
            answer.text_answer = request.POST.get(question_id, '')
            answer.save()
            
            # Find and save the selected choice
            try:
                if request.POST.get(question_id):
                    choice = QuestionChoice.objects.get(question=question, value=request.POST.get(question_id))
                    
                    # Check if this choice is already selected
                    if not AnswerChoice.objects.filter(answer=answer, choice=choice).exists():
                        # Clear previous selections for this answer
                        AnswerChoice.objects.filter(answer=answer).delete()
                        
                        # Create new selection
                        AnswerChoice.objects.create(
                            answer=answer,
                            choice=choice,
                            created_by=answer.created_by,
                            modified_by=answer.modified_by
                        )
            except QuestionChoice.DoesNotExist:
                pass
            
            return  # Skip the save below since we already saved for choice association
            
        elif question_type == QuestionType.MULTIPLE_CHOICE:
            # For multiple choice, answers come as a list
            selected_values = request.POST.getlist(question_id, [])
            answer.text_answer = ", ".join(selected_values)
            answer.save()
            
            # Clear previous selections
            AnswerChoice.objects.filter(answer=answer).delete()
            
            # Find and save each selected choice
            for choice_value in selected_values:
                try:
                    choice = QuestionChoice.objects.get(question=question, value=choice_value)
                    AnswerChoice.objects.create(
                        answer=answer,
                        choice=choice,
                        created_by=answer.created_by,
                        modified_by=answer.modified_by
                    )
                except QuestionChoice.DoesNotExist:
                    pass
            
            return  # Skip the save below since we already saved for choice association
        
        # Save the answer for non-choice questions
        answer.save()
    
    def _submit_complete_survey(self, request):
        """Complete and submit the entire survey"""
        session_data = self._get_survey_session_data()
        partial_response_id = session_data.get('partial_response_id')
        
        if not partial_response_id:
            messages.error(request, _('No se ha guardado ninguna respuesta parcial. Por favor intenta de nuevo.'))
            return redirect(request.path)
        
        try:
            response = Response.objects.get(pk=partial_response_id)
            
            # Mark as completed
            response.is_complete = True
            response.completed_at = timezone.now()
            
            # Set period if applicable (current month/year)
            now = timezone.now()
            try:
                month_name = now.strftime('%B').upper()
                period = Period.objects.get(month=month_name, year=now.year)
                response.period = period
            except Period.DoesNotExist:
                # No period for current month/year
                pass
            
            response.save()
            
            # Clear session data
            del self.request.session[f'survey_{self.survey.id}']
            self.request.session.modified = True
            
            messages.success(request, _('¡Gracias por completar la encuesta!'))
            return HttpResponseRedirect(self.get_success_url())
            
        except Response.DoesNotExist:
            messages.error(request, _('No se encontró la respuesta. Por favor intenta de nuevo.'))
            return redirect(request.path)
    
    def get_success_url(self):
        """Return the correct URL after successful submission"""
        return reverse('encuestas:survey_thank_you')  # Usa 'encuestas', no 'surveys'



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