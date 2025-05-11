from django.utils import timezone
from django.db.models import Count, Q
from django.core.serializers.json import DjangoJSONEncoder
import json

def prepare_survey_data_for_frontend(survey, questions, saved_answers=None):
    """
    Prepara los datos de la encuesta en formato JSON para ser utilizados por el frontend.
    
    Args:
        survey: Objeto Survey
        questions: QuerySet con las preguntas
        saved_answers: Dict con respuestas guardadas (opcional)
    
    Returns:
        String JSON con los datos formateados para el frontend
    """
    questions_data = []
    
    for question in questions:
        question_data = {
            'id': str(question.id),
            'type': question.question_type.name.lower(),
            'text': question.text,
            'required': question.is_required,
            'placeholder': getattr(question, 'placeholder', ''),
        }
        
        # Añadir opciones para preguntas de selección
        if question.question_type.name in ['SINGLE_CHOICE', 'MULTIPLE_CHOICE', 'RATING']:
            question_data['options'] = [
                {
                    'value': choice.value, 
                    'text': choice.text
                } 
                for choice in question.choices.all()
            ]
        
        questions_data.append(question_data)
    
    # Preparar respuestas guardadas
    answers_data = {}
    if saved_answers:
        for answer in saved_answers:
            answer_value = None
            
            if answer.question.question_type.name == 'MULTIPLE_CHOICE':
                # Para selección múltiple, guardamos lista de valores
                answer_value = [choice.choice.value for choice in answer.choices.all()]
            elif answer.question.question_type.name == 'YES_NO':
                answer_value = answer.boolean_answer
            elif answer.question.question_type.name in ['NUMBER', 'RATING']:
                answer_value = answer.number_answer
            elif answer.question.question_type.name == 'DATE':
                answer_value = answer.date_answer.isoformat() if answer.date_answer else None
            else:
                # Para texto y otros tipos simples
                answer_value = answer.text_answer
                
            answers_data[str(answer.question.id)] = answer_value
    
    # Crear estructura final
    survey_data = {
        'questions': questions_data,
        'savedAnswers': answers_data
    }
    
    # Convertir a JSON
    return json.dumps(survey_data, cls=DjangoJSONEncoder)

def get_saved_answers(response):
    """
    Obtiene las respuestas guardadas para una respuesta existente.
    
    Args:
        response: Objeto Response
    
    Returns:
        QuerySet con las respuestas
    """
    if response:
        return response.answers.all().prefetch_related('choices', 'choices__choice', 'question')
    return []

def check_survey_completion(survey, response):
    """
    Verifica si una encuesta está completa o no.
    
    Args:
        survey: Objeto Survey
        response: Objeto Response
    
    Returns:
        (bool, dict): (is_complete, completion_stats)
    """
    # Total de preguntas requeridas
    required_questions = survey.questions.filter(is_active=True, is_required=True)
    total_required = required_questions.count()
    
    # Si no hay preguntas requeridas, la encuesta está completa
    if total_required == 0:
        return True, {'answered': 0, 'required': 0, 'percentage': 100}
    
    if not response:
        return False, {'answered': 0, 'required': total_required, 'percentage': 0}
    
    # Contar respuestas válidas a preguntas requeridas
    answered_required = response.answers.filter(
        question__is_required=True,
        question__is_active=True
    ).exclude(
        Q(text_answer='') & Q(number_answer__isnull=True) & 
        Q(date_answer__isnull=True) & Q(boolean_answer__isnull=True)
    ).count()
    
    # Calcular porcentaje de completitud
    completion_percentage = int((answered_required / total_required) * 100)
    
    is_complete = answered_required >= total_required
    
    return is_complete, {
        'answered': answered_required,
        'required': total_required,
        'percentage': completion_percentage
    }