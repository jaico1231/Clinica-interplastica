from datetime import timezone
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from apps.base.models.basemodel import CompleteModel
from apps.base.models.support import QuestionType

# Assuming base models are in 'base.models'

User = get_user_model()

class Survey(CompleteModel):
    """Model to represent a survey"""
    title = models.CharField(_("Survey Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    start_date = models.DateField(_("Start Date"), null=True, blank=True)
    end_date = models.DateField(_("End Date"), null=True, blank=True)
    is_published = models.BooleanField(_("Published"), default=False)
    
    # Configuración de paginación
    questions_per_page = models.PositiveSmallIntegerField(
        _("Questions Per Page"),
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text=_("Default number of questions to display per page")
    )
    
    # Configuración de navegación
    allow_save_and_continue = models.BooleanField(
        _("Allow Save and Continue Later"),
        default=True,
        help_text=_("Allow respondents to save their progress and continue later")
    )
    
    show_progress_bar = models.BooleanField(
        _("Show Progress Bar"),
        default=True,
        help_text=_("Display progress bar to respondents")
    )
    
    allow_page_navigation = models.BooleanField(
        _("Allow Free Page Navigation"),
        default=True,
        help_text=_("Allow respondents to navigate freely between pages")
    )
    
    # Configuración de resultados
    show_results_after_completion = models.BooleanField(
        _("Show Results After Completion"),
        default=False,
        help_text=_("Show survey results to respondents after they complete the survey")
    )
    
    class Meta(CompleteModel.Meta):
        ordering = ['-created_at']
        verbose_name = _('Survey')
        verbose_name_plural = _('Surveys')
        indexes = CompleteModel.Meta.indexes + [
            models.Index(fields=['title']),
            models.Index(fields=['is_published']),
        ]
    
    def __str__(self):
        return self.title
    
    def check_is_active(self):
        """Check if survey is currently active based on dates"""
        today = timezone.now().date()
        
        if not self.is_published:
            return False
            
        if self.start_date and self.start_date > today:
            return False
            
        if self.end_date and self.end_date < today:
            return False
            
        return True
    
    @property
    def question_count(self):
        """Get the number of active questions in the survey"""
        return self.questions.filter(is_active=True).count()
    
    @property
    def response_count(self):
        """Get the number of complete responses to the survey"""
        return self.responses.filter(is_complete=True).count()
    

class Question(CompleteModel):
    """Model to represent survey questions"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions")
    question_type = models.ForeignKey(QuestionType, on_delete=models.PROTECT, related_name="questions")
    text = models.TextField(_("Question Text"))
    help_text = models.TextField(_("Help Text"), blank=True)
    is_required = models.BooleanField(_("Required"), default=True)
    order = models.PositiveIntegerField(_("Display Order"), default=0)
    
    # Additional fields for specific question types
    min_value = models.IntegerField(_("Minimum Value"), null=True, blank=True)
    max_value = models.IntegerField(_("Maximum Value"), null=True, blank=True)
    
    # Conditional display logic
    dependent_on = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="dependent_questions"
    )
    dependent_value = models.CharField(_("Dependent Value"), max_length=255, blank=True)
    
    class Meta(CompleteModel.Meta):
        ordering = ['survey', 'order']
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        indexes = CompleteModel.Meta.indexes + [
            models.Index(fields=['survey', 'order']),
            models.Index(fields=['question_type']),
        ]
    
    def __str__(self):
        return f"{self.survey.title} - {self.text[:50]}"
    
    @property
    def has_choices(self):
        """Check if this question type should have choices"""
        return self.question_type.name in [
            QuestionType.SINGLE_CHOICE, 
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.RATING
        ]


class QuestionChoice(CompleteModel):
    """Model to represent choices for questions with options"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(_("Choice Text"), max_length=255)
    value = models.CharField(_("Value"), max_length=255)
    order = models.PositiveIntegerField(_("Display Order"), default=0)
    color = models.CharField(_("Color"), max_length=20, blank=True, null=True)  # Added field
    is_other_option = models.BooleanField(_("Is 'Other' Option"), default=False)  # Added field
    
    class Meta(CompleteModel.Meta):
        ordering = ['question', 'order']
        verbose_name = _('Question Choice')
        verbose_name_plural = _('Question Choices')
        indexes = CompleteModel.Meta.indexes + [
            models.Index(fields=['question', 'order']),
        ]
    
    def __str__(self):
        return f"{self.question.text[:30]} - {self.text}"


class Response(CompleteModel):
    """Model to represent a survey response session"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="responses")
    respondent = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="survey_responses"
    )
    respondent_email = models.EmailField(_("Respondent Email"), blank=True, null=True)
    respondent_name = models.CharField(_("Respondent Name"), max_length=255, blank=True, null=True)
    respondent_ip = models.GenericIPAddressField(_("IP Address"), blank=True, null=True)
    started_at = models.DateTimeField(_("Started At"), auto_now_add=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    is_complete = models.BooleanField(_("Completed"), default=False)
    
    # For organization into periods if needed
    period = models.ForeignKey('Period', on_delete=models.SET_NULL, null=True, blank=True, related_name="responses")
    
    class Meta(CompleteModel.Meta):
        ordering = ['-created_at']
        verbose_name = _('Response')
        verbose_name_plural = _('Responses')
        indexes = CompleteModel.Meta.indexes + [
            models.Index(fields=['survey', 'is_complete']),
            models.Index(fields=['period']),
        ]
        # Add unique constraint for one email per survey
        constraints = [
            models.UniqueConstraint(
                fields=['survey', 'respondent_email'],
                name='unique_email_per_survey'
            )
        ]
    
    def __str__(self):
        return f"Response to {self.survey.title} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Ensure respondent_email is provided
        if not self.respondent_email:
            raise ValueError(_("Respondent email is required"))
        super().save(*args, **kwargs)


class Answer(CompleteModel):
    """Model to store individual question answers"""
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    
    # Different types of answer values
    text_answer = models.TextField(_("Text Answer"), blank=True)
    number_answer = models.FloatField(_("Number Answer"), null=True, blank=True)
    date_answer = models.DateField(_("Date Answer"), null=True, blank=True)
    boolean_answer = models.BooleanField(_("Yes/No Answer"), null=True, blank=True)
    # Hierarchy answers are stored in the related HierarchyAnswer model
    
    class Meta(CompleteModel.Meta):
        ordering = ['question__order']
        verbose_name = _('Answer')
        verbose_name_plural = _('Answers')
        indexes = CompleteModel.Meta.indexes + [
            models.Index(fields=['response', 'question']),
        ]
    
    def __str__(self):
        return f"Answer to {self.question.text[:30]}"
    
    @property
    def get_hierarchy_structure(self):
        """Returns structured hierarchy answer data if this is a hierarchy question"""
        if self.question.question_type.name == QuestionType.HIERARCHY:
            result = []
            hierarchy_answers = self.hierarchy_answers.all().order_by('position')
            
            # Build hierarchical structure
            for h_answer in hierarchy_answers:
                item_data = {
                    'item_id': h_answer.item.id,
                    'text': h_answer.item.text,
                    'position': h_answer.position,
                    'level': h_answer.item.level,
                }
                if h_answer.selected_parent:
                    item_data['parent_id'] = h_answer.selected_parent.id
                    
                result.append(item_data)
                
            return result
        return None


class AnswerChoice(CompleteModel):
    """Model to store selected choices for multiple choice questions"""
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="selected_choices")
    choice = models.ForeignKey(QuestionChoice, on_delete=models.CASCADE, related_name="selections")
    
    class Meta(CompleteModel.Meta):
        ordering = ['choice__order']
        verbose_name = _('Answer Choice')
        verbose_name_plural = _('Answer Choices')
        indexes = CompleteModel.Meta.indexes + [
            models.Index(fields=['answer']),
            models.Index(fields=['choice']),
        ]
    
    def __str__(self):
        return f"{self.answer} - {self.choice.text}"


class HierarchyItem(CompleteModel):
    """Model to represent items in a hierarchical question"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="hierarchy_items")
    text = models.CharField(_("Item Text"), max_length=255)
    description = models.TextField(_("Item Description"), blank=True)
    order = models.PositiveIntegerField(_("Default Order"), default=0)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children"
    )
    level = models.PositiveSmallIntegerField(_("Hierarchy Level"), default=0)
    is_draggable = models.BooleanField(_("Is Draggable"), default=True)
    is_editable = models.BooleanField(_("Is Editable"), default=True)
    icon = models.CharField(_("Icon"), max_length=50, blank=True, null=True)  # Added field
    custom_class = models.CharField(_("Custom CSS Class"), max_length=50, blank=True, null=True)  # Added field
    
    class Meta(CompleteModel.Meta):
        ordering = ['question', 'level', 'order']
        verbose_name = _('Hierarchy Item')
        verbose_name_plural = _('Hierarchy Items')
        indexes = CompleteModel.Meta.indexes + [
            models.Index(fields=['question', 'level', 'order']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        return f"{self.question.text[:30]} - {self.text}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate level based on parent
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0
        super().save(*args, **kwargs)


class HierarchyAnswer(CompleteModel):
    """Model to store hierarchical answers for hierarchy questions"""
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="hierarchy_answers")
    item = models.ForeignKey(HierarchyItem, on_delete=models.CASCADE, related_name="item_answers")
    selected_parent = models.ForeignKey(
        HierarchyItem, 
        on_delete=models.CASCADE, 
        related_name="parent_selections",
        null=True,
        blank=True
    )
    position = models.PositiveIntegerField(_("Position/Rank"), default=0)
    
    class Meta(CompleteModel.Meta):
        ordering = ['answer', 'position']
        verbose_name = _('Hierarchy Answer')
        verbose_name_plural = _('Hierarchy Answers')
        indexes = CompleteModel.Meta.indexes + [
            models.Index(fields=['answer']),
            models.Index(fields=['item']),
        ]
    
    def __str__(self):
        return f"{self.answer} - {self.item.text} (Position: {self.position})"


class Period(CompleteModel):
    """Model to represent time periods for organizing survey data"""
    MONTH_CHOICES = [
        ('JANUARY', _('January')),
        ('FEBRUARY', _('February')),
        ('MARCH', _('March')),
        ('APRIL', _('April')),
        ('MAY', _('May')),
        ('JUNE', _('June')),
        ('JULY', _('July')),
        ('AUGUST', _('August')),
        ('SEPTEMBER', _('September')),
        ('OCTOBER', _('October')),
        ('NOVEMBER', _('November')),
        ('DECEMBER', _('December')),
    ]

    name = models.CharField(_("Period Name"), max_length=255, blank=True)
    month = models.CharField(_("Month"), max_length=20, choices=MONTH_CHOICES, blank=True)
    year = models.PositiveIntegerField(_("Year"), validators=[MinValueValidator(2000), MaxValueValidator(2100)], null=True, blank=True)
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    
    class Meta(CompleteModel.Meta):
        ordering = ['-start_date']
        verbose_name = _('Period')
        verbose_name_plural = _('Periods')
        indexes = CompleteModel.Meta.indexes + [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        if self.name:
            return self.name
        elif self.month and self.year:
            return f"{self.get_month_display()} {self.year}"
        else:
            return f"{self.start_date} to {self.end_date}"
    
    def save(self, *args, **kwargs):
        # Auto-generate name if not provided
        if not self.name and self.month and self.year:
            self.name = f"{self.get_month_display()} {self.year}"
        super().save(*args, **kwargs)


class Indicator(CompleteModel):
    """Model to store calculated indicators based on survey data"""
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name="indicators")
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="indicators")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="indicators", null=True, blank=True)
    
    name = models.CharField(_("Indicator Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    
    # Store different types of aggregation values
    count_value = models.PositiveIntegerField(_("Count"), default=0)
    numeric_value = models.FloatField(_("Numeric Value"), null=True, blank=True)
    percentage_value = models.FloatField(_("Percentage"), null=True, blank=True)
    
    # Category for grouping indicators
    category = models.CharField(_("Category"), max_length=100, blank=True)
    
    class Meta(CompleteModel.Meta):
        ordering = ['period', 'survey', 'category', 'name']
        verbose_name = _('Indicator')
        verbose_name_plural = _('Indicators')
        indexes = CompleteModel.Meta.indexes + [
            models.Index(fields=['period', 'survey']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.period}"

