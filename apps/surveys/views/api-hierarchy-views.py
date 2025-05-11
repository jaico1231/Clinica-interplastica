from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
import json

from apps.surveys.forms.hierarchy_item_form import HierarchyItemForm
from apps.surveys.models.surveymodel import HierarchyItem, Question

# from apps.encuestas.models import Question, QuestionChoice, HierarchyItem
# from apps.encuestas.forms import HierarchyItemForm


@login_required
@require_http_methods(["POST"])
def reorder_questions(request):
    """API endpoint to update question order"""
    try:
        # Parse the request body
        data = json.loads(request.body)
        
        # Update each question
        for item in data:
            question_id = item.get('id')
            order = item.get('order')
            
            question = get_object_or_404(Question, id=question_id)
            
            # Check if user has permission to edit this question
            if question.survey.created_by != request.user:
                return JsonResponse({
                    'success': False,
                    'message': _("You don't have permission to edit this question")
                }, status=403)
            
            # Update order
            question.order = order
            question.save(update_fields=['order'])
        
        return JsonResponse({
            'success': True,
            'message': _("Question order updated successfully")
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _("Invalid JSON data")
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_hierarchy_items(request, question_id):
    """API endpoint to get all hierarchy items for a question"""
    question = get_object_or_404(Question, id=question_id)
    
    # Check if user has permission to view this question
    if question.survey.created_by != request.user:
        return JsonResponse({
            'success': False,
            'message': _("You don't have permission to view these items")
        }, status=403)
    
    # Get all hierarchy items for this question
    items = HierarchyItem.objects.filter(question=question).select_related('parent')
    
    # Prepare item data
    item_data = []
    for item in items:
        data = {
            'id': item.id,
            'text': item.text,
            'description': item.description,
            'order': item.order,
            'level': item.level,
            'is_draggable': item.is_draggable,
            'is_editable': item.is_editable,
            'icon': item.icon,
            'custom_class': item.custom_class,
            'parent_id': item.parent_id,
        }
        
        if item.parent:
            data['parent'] = {
                'id': item.parent.id,
                'text': item.parent.text,
                'level': item.parent.level
            }
        
        item_data.append(data)
    
    return JsonResponse({
        'success': True,
        'data': item_data
    })


@login_required
@require_http_methods(["POST"])
def create_hierarchy_item(request, question_id):
    """API endpoint to create a new hierarchy item"""
    question = get_object_or_404(Question, id=question_id)
    
    # Check if user has permission to add items
    if question.survey.created_by != request.user:
        return JsonResponse({
            'success': False,
            'message': _("You don't have permission to add items to this question")
        }, status=403)
    
    # Process form data
    try:
        # If request body is JSON
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            form = HierarchyItemForm(data)
        else:
            # Handle form data
            form = HierarchyItemForm(request.POST)
        
        if form.is_valid():
            hierarchy_item = form.save(commit=False)
            hierarchy_item.question = question
            
            # Handle parent
            parent_id = form.cleaned_data.get('parent_id')
            if parent_id:
                try:
                    parent = HierarchyItem.objects.get(id=parent_id, question=question)
                    hierarchy_item.parent = parent
                except HierarchyItem.DoesNotExist:
                    pass
            
            # Set order to the next available order
            if hierarchy_item.parent:
                max_order = HierarchyItem.objects.filter(
                    question=question, 
                    parent=hierarchy_item.parent
                ).order_by('-order').values_list('order', flat=True).first() or 0
            else:
                max_order = HierarchyItem.objects.filter(
                    question=question, 
                    parent__isnull=True
                ).order_by('-order').values_list('order', flat=True).first() or 0
            
            hierarchy_item.order = max_order + 1
            hierarchy_item.save()
            
            # Prepare response data
            response_data = {
                'id': hierarchy_item.id,
                'text': hierarchy_item.text,
                'description': hierarchy_item.description,
                'order': hierarchy_item.order,
                'level': hierarchy_item.level,
                'is_draggable': hierarchy_item.is_draggable,
                'is_editable': hierarchy_item.is_editable,
                'icon': hierarchy_item.icon,
                'custom_class': hierarchy_item.custom_class,
                'parent_id': hierarchy_item.parent_id,
            }
            
            if hierarchy_item.parent:
                response_data['parent'] = {
                    'id': hierarchy_item.parent.id,
                    'text': hierarchy_item.parent.text,
                    'level': hierarchy_item.parent.level
                }
            
            return JsonResponse({
                'success': True,
                'message': _("Hierarchy item created successfully"),
                'item': response_data
            })
        else:
            return JsonResponse({
                'success': False,
                'message': _("There was an error creating the hierarchy item"),
                'errors': form.errors
            }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _("Invalid JSON data")
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def update_hierarchy_item(request, item_id):
    """API endpoint to update a hierarchy item"""
    item = get_object_or_404(HierarchyItem, id=item_id)
    question = item.question
    
    # Check if user has permission to edit this item
    if question.survey.created_by != request.user:
        return JsonResponse({
            'success': False,
            'message': _("You don't have permission to edit this item")
        }, status=403)
    
    # Process form data
    try:
        # If request body is JSON
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            form = HierarchyItemForm(data, instance=item)
        else:
            # Handle form data
            form = HierarchyItemForm(request.POST, instance=item)
        
        if form.is_valid():
            # Check for circular references in parent
            parent_id = form.cleaned_data.get('parent_id')
            if parent_id:
                if str(item.id) == parent_id:
                    return JsonResponse({
                        'success': False,
                        'message': _("An item cannot be its own parent"),
                        'errors': {'parent_id': [_("An item cannot be its own parent")]}
                    }, status=400)
                
                try:
                    parent = HierarchyItem.objects.get(id=parent_id, question=question)
                    
                    # Check if the selected parent is a descendant of the item
                    descendants = item.get_children_recursive()
                    if parent in descendants:
                        return JsonResponse({
                            'success': False,
                            'message': _("Cannot select a descendant as parent"),
                            'errors': {'parent_id': [_("Cannot select a descendant as parent")]}
                        }, status=400)
                    
                    form.instance.parent = parent
                except HierarchyItem.DoesNotExist:
                    form.instance.parent = None
            else:
                form.instance.parent = None
            
            hierarchy_item = form.save()
            
            # Prepare response data
            response_data = {
                'id': hierarchy_item.id,
                'text': hierarchy_item.text,
                'description': hierarchy_item.description,
                'order': hierarchy_item.order,
                'level': hierarchy_item.level,
                'is_draggable': hierarchy_item.is_draggable,
                'is_editable': hierarchy_item.is_editable,
                'icon': hierarchy_item.icon,
                'custom_class': hierarchy_item.custom_class,
                'parent_id': hierarchy_item.parent_id,
            }
            
            if hierarchy_item.parent:
                response_data['parent'] = {
                    'id': hierarchy_item.parent.id,
                    'text': hierarchy_item.parent.text,
                    'level': hierarchy_item.parent.level
                }
            
            return JsonResponse({
                'success': True,
                'message': _("Hierarchy item updated successfully"),
                'item': response_data
            })
        else:
            return JsonResponse({
                'success': False,
                'message': _("There was an error updating the hierarchy item"),
                'errors': form.errors
            }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _("Invalid JSON data")
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_hierarchy_item(request, item_id):
    """API endpoint to delete a hierarchy item"""
    item = get_object_or_404(HierarchyItem, id=item_id)
    question = item.question
    
    # Check if user has permission to delete this item
    if question.survey.created_by != request.user:
        return JsonResponse({
            'success': False,
            'message': _("You don't have permission to delete this item")
        }, status=403)
    
    # Get children count before deletion
    children_count = item.children.count()
    
    # Delete the item (and its children due to CASCADE)
    item.delete()
    
    return JsonResponse({
        'success': True,
        'message': _("Hierarchy item deleted successfully"),
        'children_deleted': children_count,
        'items_count': HierarchyItem.objects.filter(question=question).count()
    })


@login_required
@require_http_methods(["POST"])
def reorder_hierarchy_items(request, question_id):
    """API endpoint to reorder hierarchy items"""
    question = get_object_or_404(Question, id=question_id)
    
    # Check if user has permission to edit this question
    if question.survey.created_by != request.user:
        return JsonResponse({
            'success': False,
            'message': _("You don't have permission to edit this question")
        }, status=403)
    
    try:
        # Parse the request body
        data = json.loads(request.body)
        items = data.get('items', [])
        
        # Update each item
        for item_data in items:
            item_id = item_data.get('id')
            order = item_data.get('order')
            parent_id = item_data.get('parent_id')
            
            try:
                item = HierarchyItem.objects.get(id=item_id, question=question)
                
                # Update order
                item.order = order
                
                # Update parent if provided
                if parent_id:
                    try:
                        parent = HierarchyItem.objects.get(id=parent_id, question=question)
                        
                        # Check for circular references
                        if parent.id == item.id:
                            continue
                        
                        # Check if parent is a descendant of the item
                        descendants = item.get_children_recursive()
                        if parent in descendants:
                            continue
                        
                        item.parent = parent
                    except HierarchyItem.DoesNotExist:
                        pass
                else:
                    item.parent = None
                
                item.save()
            except HierarchyItem.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'message': _("Hierarchy items reordered successfully")
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': _("Invalid JSON data")
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)