from django import forms
from django.utils.translation import gettext as _
from django.forms import modelformset_factory, inlineformset_factory
from django.core.exceptions import ValidationError
from django.db.models import Q
from apps.surveys.models.surveymodel import Question, QuestionChoice, QuestionType, Survey

class QuestionChoiceForm(forms.ModelForm):
    """
    Formulario para la creación y edición de opciones de respuesta
    """
    class Meta:
        model = QuestionChoice
        fields = [
            'question', 'text', 'value', 'order', 
            'color', 'is_other_option'
        ]
        labels = {
            'question': _('Pregunta'),
            'text': _('Texto de la opción'),
            'value': _('Valor'),
            'order': _('Orden'),
            'color': _('Color (opcional)'),
            'is_other_option': _('¿Es opción "Otro"?')
        }
        widgets = {
            'question': forms.HiddenInput(),
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Texto de la opción')}),
            'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Valor (se generará automáticamente si está vacío)')}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control color-picker', 'placeholder': _('Color (ej: #FF5733)')}),
            'is_other_option': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extract question_id before calling super
        self.question_id = kwargs.pop('question_id', None)
        super().__init__(*args, **kwargs)
        
        # Set initial value for question field if question_id is provided
        if self.question_id:
            try:
                question = Question.objects.get(pk=self.question_id)
                self.fields['question'].initial = question
            except Question.DoesNotExist:
                pass
        
        # Add help text for is_other_option field
        self.fields['is_other_option'].help_text = _(
            "Si está marcada, esta opción permitirá al usuario ingresar texto adicional"
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that there's not more than one "Other" option per question
        is_other = cleaned_data.get('is_other_option')
        question = cleaned_data.get('question')
        
        if is_other and question:
            # If we're editing, exclude the current instance
            instance_id = getattr(self.instance, 'id', None)
            
            # Build query to check for existing "other" options
            query = Q(question=question, is_other_option=True, is_active=True)
            
            # Exclude current instance if editing
            if instance_id:
                query &= ~Q(id=instance_id)
                
            existing_other = QuestionChoice.objects.filter(query).exists()
            
            if existing_other:
                self.add_error('is_other_option', _(
                    'Ya existe una opción "Otro" para esta pregunta'
                ))
        
        return cleaned_data
# class QuestionChoiceForm(forms.ModelForm):
#     """
#     Formulario para la creación y edición de opciones de respuesta
#     """
#     class Meta:
#         model = QuestionChoice
#         fields = [
#             'question', 'text', 'value', 'order', 
#             'color', 'is_other_option'
#         ]
#         labels = {
#             'question': _('Pregunta'),
#             'text': _('Texto de la opción'),
#             'value': _('Valor'),
#             'order': _('Orden'),
#             'color': _('Color (opcional)'),
#             'is_other_option': _('¿Es opción "Otro"?')
#         }
#         widgets = {
#             'question': forms.HiddenInput(),
#             'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Texto de la opción')}),
#             'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Valor (se generará automáticamente si está vacío)')}),
#             'order': forms.NumberInput(attrs={'class': 'form-control'}),
#             'color': forms.TextInput(attrs={'class': 'form-control color-picker', 'placeholder': _('Color (ej: #FF5733)')}),
#             'is_other_option': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }
    
#     def __init__(self, *args, **kwargs):
#         # Extract question_id before calling super
#         self.question_id = kwargs.pop('question_id', None)
#         super().__init__(*args, **kwargs)
        
#         # Set initial value for question field if question_id is provided
#         if self.question_id:
#             self.fields['question'].initial = self.question_id
        
#         # Add help text for is_other_option field
#         self.fields['is_other_option'].help_text = _(
#             "Si está marcada, esta opción permitirá al usuario ingresar texto adicional"
#         )
    
#     def clean(self):
#         cleaned_data = super().clean()
        
#         # Validate that there's not more than one "Other" option per question
#         is_other = cleaned_data.get('is_other_option')
#         question = cleaned_data.get('question')
        
#         if is_other and question:
#             # If we're editing, exclude the current instance
#             instance_id = getattr(self.instance, 'id', None)
#             filter_kwargs = {'question': question, 'is_other_option': True, 'is_active': True}
            
#             if instance_id:
#                 filter_kwargs['id__ne'] = instance_id
                
#             existing_other = QuestionChoice.objects.filter(**filter_kwargs).exists()
            
#             if existing_other:
#                 self.add_error('is_other_option', _(
#                     'Ya existe una opción "Otro" para esta pregunta'
#                 ))
        
#         return cleaned_data


class BaseQuestionFormSet(forms.BaseModelFormSet):
    """
    Formset base para manejar múltiples preguntas a la vez
    """
    def __init__(self, *args, **kwargs):
        self.survey = kwargs.pop('survey', None)
        super().__init__(*args, **kwargs)
        
        # Configurar cada formulario en el formset
        for form in self.forms:
            # Establecer la encuesta para todas las preguntas
            if self.survey:
                form.fields['survey'].initial = self.survey
                form.fields['survey'].widget = forms.HiddenInput()
            
            # Configurar queryset para los tipos de preguntas
            form.fields['question_type'].queryset = QuestionType.objects.filter(is_active=True)
            
            # Mejorar widgets
            form.fields['text'].widget.attrs.update({'class': 'form-control', 'rows': 2})
            form.fields['help_text'].widget.attrs.update({'class': 'form-control', 'rows': 1})
            form.fields['order'].widget.attrs.update({'class': 'form-control', 'min': 0})
    
    def clean(self):
        """
        Validación a nivel de formset:
        - Verificar que el orden sea único dentro de la encuesta
        - Verificar que no haya preguntas duplicadas
        """
        if any(self.errors):
            # No validar si ya hay errores
            return
        
        orders = []
        texts = []
        
        for form in self.forms:
            if 'DELETE' in form.cleaned_data and form.cleaned_data['DELETE']:
                # No validar formularios marcados para eliminar
                continue
            
            order = form.cleaned_data.get('order')
            text = form.cleaned_data.get('text')
            
            # Validar orden único
            if order in orders:
                form.add_error('order', _('El orden debe ser único dentro de la encuesta'))
            else:
                orders.append(order)
            
            # Validar texto único
            if text in texts:
                form.add_error('text', _('Ya existe una pregunta con este texto en la encuesta'))
            else:
                texts.append(text)


# Crear el formset para preguntas
QuestionFormSet = modelformset_factory(
    Question,
    fields=['survey', 'question_type', 'text', 'help_text', 'is_required', 'order', 'min_value', 'max_value'],
    formset=BaseQuestionFormSet,
    extra=1,
    can_delete=True
)


class BaseSurveyQuestionFormSet(forms.BaseInlineFormSet):
    """
    Formset base para preguntas inline dentro de una encuesta
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar cada formulario en el formset
        for form in self.forms:
            # Configurar queryset para los tipos de preguntas
            form.fields['question_type'].queryset = QuestionType.objects.filter(is_active=True)
            
            # Mejorar widgets
            form.fields['text'].widget.attrs.update({'class': 'form-control', 'rows': 2})
            form.fields['help_text'].widget.attrs.update({'class': 'form-control', 'rows': 1})
            form.fields['order'].widget.attrs.update({'class': 'form-control', 'min': 0})
            
            # Configurar campos dependientes
            form.fields['dependent_on'].queryset = Question.objects.filter(
                survey=self.instance, 
                is_active=True
            ).exclude(id=form.instance.id if form.instance and form.instance.id else None)
    
    def clean(self):
        """
        Validación a nivel de formset:
        - Verificar que el orden sea único dentro de la encuesta
        - Verificar que no haya preguntas duplicadas
        - Verificar que las dependencias no formen ciclos
        """
        if any(self.errors):
            # No validar si ya hay errores
            return
        
        orders = []
        texts = []
        
        for form in self.forms:
            if 'DELETE' in form.cleaned_data and form.cleaned_data['DELETE']:
                # No validar formularios marcados para eliminar
                continue
            
            order = form.cleaned_data.get('order')
            text = form.cleaned_data.get('text')
            
            # Validar orden único
            if order in orders:
                form.add_error('order', _('El orden debe ser único dentro de la encuesta'))
            else:
                orders.append(order)
            
            # Validar texto único
            if text in texts:
                form.add_error('text', _('Ya existe una pregunta con este texto en la encuesta'))
            else:
                texts.append(text)
        
        # Validar que no haya ciclos en las dependencias
        self._validate_no_dependency_cycles()
    
    def _validate_no_dependency_cycles(self):
        """
        Verificar que no haya ciclos en las dependencias de preguntas
        """
        # Construir un grafo de dependencias
        dependency_graph = {}
        
        for form in self.forms:
            if 'DELETE' in form.cleaned_data and form.cleaned_data['DELETE']:
                continue
                
            # Identificador de la pregunta (id o índice temporal)
            question_id = form.instance.id if form.instance and form.instance.id else f'new_{form.prefix}'
            dependent_on = form.cleaned_data.get('dependent_on')
            
            if dependent_on:
                if question_id not in dependency_graph:
                    dependency_graph[question_id] = []
                    
                dependency_graph[question_id].append(dependent_on.id)
        
        # Detectar ciclos usando DFS
        for question_id in dependency_graph:
            visited = set()
            path = []
            
            def dfs(node):
                visited.add(node)
                path.append(node)
                
                if node in dependency_graph:
                    for neighbor in dependency_graph[node]:
                        if neighbor in path:  # Ciclo detectado
                            cycle = path[path.index(neighbor):] + [neighbor]
                            raise ValidationError(
                                _('Se detectó un ciclo en las dependencias de preguntas: {}').format(
                                    ' -> '.join([str(n) for n in cycle])
                                )
                            )
                            
                        if neighbor not in visited:
                            dfs(neighbor)
                            
                path.pop()
                
            dfs(question_id)


# Crear el formset inline para preguntas dentro de una encuesta
SurveyQuestionFormSet = inlineformset_factory(
    Survey,
    Question,
    fields=['question_type', 'text', 'help_text', 'is_required', 'order', 
            'min_value', 'max_value', 'dependent_on', 'dependent_value'],
    formset=BaseSurveyQuestionFormSet,
    extra=3,
    can_delete=True
)

class BaseQuestionChoiceFormSet(forms.BaseModelFormSet):
    """
    Formset base para manejar múltiples opciones de pregunta a la vez
    """
    def __init__(self, *args, **kwargs):
        self.question = kwargs.pop('question', None)
        super().__init__(*args, **kwargs)
        
        # Configurar cada formulario en el formset
        for form in self.forms:
            # Establecer la pregunta para todas las opciones
            if self.question:
                form.fields['question'].initial = self.question
                form.fields['question'].widget = forms.HiddenInput()
            
            # Mejorar widgets
            form.fields['text'].widget.attrs.update({'class': 'form-control'})
            form.fields['value'].widget.attrs.update({'class': 'form-control'})
            form.fields['order'].widget.attrs.update({'class': 'form-control', 'min': 0})
            form.fields['color'].widget.attrs.update({'class': 'form-control color-picker'})
    
    def clean(self):
        """
        Validación a nivel de formset:
        - Verificar que el orden sea único dentro de la pregunta
        - Verificar que no haya opciones duplicadas
        - Verificar que no haya más de una opción marcada como 'is_other_option'
        """
        if any(self.errors):
            # No validar si ya hay errores
            return
        
        orders = []
        texts = []
        values = []
        other_option_count = 0
        
        for form in self.forms:
            if 'DELETE' in form.cleaned_data and form.cleaned_data['DELETE']:
                # No validar formularios marcados para eliminar
                continue
            
            order = form.cleaned_data.get('order')
            text = form.cleaned_data.get('text')
            value = form.cleaned_data.get('value')
            is_other = form.cleaned_data.get('is_other_option')
            
            # Validar orden único
            if order in orders:
                form.add_error('order', _('El orden debe ser único dentro de la pregunta'))
            else:
                orders.append(order)
            
            # Validar texto único
            if text in texts:
                form.add_error('text', _('Ya existe una opción con este texto en la pregunta'))
            else:
                texts.append(text)
                
            # Validar valor único (si no está vacío)
            if value and value in values:
                form.add_error('value', _('Ya existe una opción con este valor en la pregunta'))
            elif value:
                values.append(value)
            
            # Contar opciones "Otro"
            if is_other:
                other_option_count += 1
        
        # Validar que no haya más de una opción "Otro"
        if other_option_count > 1:
            raise ValidationError(
                _('Solo puede haber una opción marcada como "Otro" por pregunta')
            )


# Crear el formset para opciones de pregunta
QuestionChoiceFormSet = modelformset_factory(
    QuestionChoice,
    fields=['question', 'text', 'value', 'order', 'color', 'is_other_option'],
    formset=BaseQuestionChoiceFormSet,
    extra=4,
    can_delete=True
)


class BaseQuestionChoiceInlineFormSet(forms.BaseInlineFormSet):
    """
    Formset base para opciones inline dentro de una pregunta
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar cada formulario en el formset
        for form in self.forms:
            # Mejorar widgets
            form.fields['text'].widget.attrs.update({'class': 'form-control'})
            form.fields['value'].widget.attrs.update({'class': 'form-control'})
            form.fields['order'].widget.attrs.update({'class': 'form-control', 'min': 0})
            form.fields['color'].widget.attrs.update({'class': 'form-control color-picker'})
    
    def clean(self):
        """
        Validación a nivel de formset:
        - Verificar que el orden sea único dentro de la pregunta
        - Verificar que no haya opciones duplicadas
        - Verificar que no haya más de una opción marcada como 'is_other_option'
        """
        if any(self.errors):
            # No validar si ya hay errores
            return
        
        orders = []
        texts = []
        values = []
        other_option_count = 0
        
        for form in self.forms:
            if 'DELETE' in form.cleaned_data and form.cleaned_data['DELETE']:
                # No validar formularios marcados para eliminar
                continue
            
            order = form.cleaned_data.get('order')
            text = form.cleaned_data.get('text')
            value = form.cleaned_data.get('value')
            is_other = form.cleaned_data.get('is_other_option')
            
            # Validar orden único
            if order in orders:
                form.add_error('order', _('El orden debe ser único dentro de la pregunta'))
            else:
                orders.append(order)
            
            # Validar texto único
            if text in texts:
                form.add_error('text', _('Ya existe una opción con este texto en la pregunta'))
            else:
                texts.append(text)
                
            # Validar valor único (si no está vacío)
            if value and value in values:
                form.add_error('value', _('Ya existe una opción con este valor en la pregunta'))
            elif value:
                values.append(value)
            
            # Contar opciones "Otro"
            if is_other:
                other_option_count += 1
        
        # Validar que no haya más de una opción "Otro"
        if other_option_count > 1:
            raise ValidationError(
                _('Solo puede haber una opción marcada como "Otro" por pregunta')
            )

    def save(self, commit=True):
        """
        Personalizar el guardado para asegurar que los valores se generen correctamente
        """
        instances = super().save(commit=False)
        
        # Generar valores para opciones sin valor explícito
        for instance in instances:
            if not instance.value and instance.text:
                instance.value = instance.text.lower().replace(' ', '_')
            
            if commit:
                instance.save()
        
        # Completar el guardado normal
        if commit:
            self.save_m2m()
            
        return instances


# Crear el formset inline para opciones dentro de una pregunta
QuestionChoiceInlineFormSet = inlineformset_factory(
    Question,
    QuestionChoice,
    fields=['text', 'value', 'order', 'color', 'is_other_option'],
    formset=BaseQuestionChoiceInlineFormSet,
    extra=4,
    can_delete=True
)


class BulkChoiceCreationForm(forms.Form):
    """
    Formulario para crear múltiples opciones a la vez mediante texto
    """
    options_text = forms.CharField(
        label=_('Opciones (una por línea)'),
        widget=forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
        help_text=_('Ingrese cada opción en una línea separada')
    )
    
    starting_order = forms.IntegerField(
        label=_('Orden inicial'),
        initial=10,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    order_increment = forms.IntegerField(
        label=_('Incremento de orden'),
        initial=10,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def clean_options_text(self):
        options_text = self.cleaned_data.get('options_text')
        
        # Dividir por líneas y filtrar líneas vacías
        options_list = [line.strip() for line in options_text.split('\n') if line.strip()]
        
        if not options_list:
            raise ValidationError(_('Debe ingresar al menos una opción'))
            
        return options_list