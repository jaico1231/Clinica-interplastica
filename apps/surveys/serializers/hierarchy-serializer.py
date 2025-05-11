from rest_framework import serializers
from apps.encuestas.models import (
    Survey, Question, QuestionChoice, 
    HierarchyItem, Response, Answer,
    HierarchyAnswer
)

class HierarchyItemParentSerializer(serializers.ModelSerializer):
    """Serializer for parent hierarchy items (simplified to avoid recursion)"""
    class Meta:
        model = HierarchyItem
        fields = ['id', 'text', 'level']


class HierarchyItemSerializer(serializers.ModelSerializer):
    """Serializer for hierarchy items"""
    parent = HierarchyItemParentSerializer(read_only=True)
    children_count = serializers.SerializerMethodField()
    
    class Meta:
        model = HierarchyItem
        fields = [
            'id', 'text', 'description', 'order', 
            'parent', 'level', 'is_draggable', 
            'is_editable', 'icon', 'custom_class',
            'children_count'
        ]
    
    def get_children_count(self, obj):
        """Get the number of direct children"""
        return obj.children.count()


class HierarchyAnswerSerializer(serializers.ModelSerializer):
    """Serializer for hierarchy answers"""
    item_text = serializers.ReadOnlyField(source='item.text')
    item_description = serializers.ReadOnlyField(source='item.description')
    parent_id = serializers.ReadOnlyField(source='selected_parent.id')
    parent_text = serializers.ReadOnlyField(source='selected_parent.text')
    
    class Meta:
        model = HierarchyAnswer
        fields = [
            'id', 'item', 'item_text', 'item_description',
            'selected_parent', 'parent_id', 'parent_text',
            'position', 'level', 'custom_text'
        ]


class QuestionChoiceSerializer(serializers.ModelSerializer):
    """Serializer for question choices"""
    class Meta:
        model = QuestionChoice
        fields = ['id', 'text', 'value', 'order', 'color', 'is_other_option']


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions"""
    type_name = serializers.ReadOnlyField(source='question_type.name')
    choices = QuestionChoiceSerializer(many=True, read_only=True)
    hierarchy_items_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'text', 'help_text', 'question_type', 'type_name',
            'is_required', 'order', 'min_value', 'max_value',
            'allow_hierarchy_creation', 'display_hierarchy_as',
            'choices', 'hierarchy_items_count'
        ]


class AnswerSerializer(serializers.ModelSerializer):
    """Serializer for answers"""
    question_text = serializers.ReadOnlyField(source='question.text')
    question_type = serializers.ReadOnlyField(source='question.question_type.name')
    selected_choices = serializers.SerializerMethodField()
    hierarchy_structure = serializers.SerializerMethodField()
    
    class Meta:
        model = Answer
        fields = [
            'id', 'question', 'question_text', 'question_type',
            'text_answer', 'number_answer', 'date_answer', 'boolean_answer',
            'selected_choices', 'hierarchy_structure'
        ]
    
    def get_selected_choices(self, obj):
        """Get the selected choices for multiple choice questions"""
        choices = obj.selected_choices.all()
        return QuestionChoiceSerializer(choices, many=True).data
    
    def get_hierarchy_structure(self, obj):
        """Get the hierarchy structure for hierarchy questions"""
        if obj.question.question_type.name == 'HIERARCHY':
            hierarchy_answers = obj.hierarchy_answers.all().order_by('position')
            return HierarchyAnswerSerializer(hierarchy_answers, many=True).data
        return None


class ResponseSerializer(serializers.ModelSerializer):
    """Serializer for responses"""
    answers = AnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Response
        fields = [
            'id', 'survey', 'respondent_email', 'respondent_name',
            'started_at', 'completed_at', 'is_complete', 'answers'
        ]


class SurveySerializer(serializers.ModelSerializer):
    """Serializer for surveys"""
    questions_count = serializers.ReadOnlyField(source='question_count')
    responses_count = serializers.ReadOnlyField(source='response_count')
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Survey
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'is_published', 'questions_per_page', 'show_progress_bar',
            'allow_page_navigation', 'show_results_after_completion',
            'questions_count', 'responses_count', 'questions'
        ]