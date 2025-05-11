from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.db.models import F
from apps.surveys.forms.hierarchy_item_form import HierarchyItemForm
from apps.surveys.models.surveymodel import HierarchyItem, Question
from django.db.models import Max
# from apps.encuestas.models import Question, HierarchyItem
# from apps.encuestas.forms import HierarchyItemForm


class HierarchyItemListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista para listar los elementos de la jerarquía de una pregunta.
    """
    permission_required = 'survey.view_hierarchyitem'    
    model = HierarchyItem
    template_name = 'surveys/hierarchy_item.html'
    context_object_name = 'items'

    def get_success_url(self):
        return reverse_lazy('encuestas:hierarchy_item_list', args=[self.object.question.id])

    def get_queryset(self):
        self.question = get_object_or_404(Question, pk=self.kwargs.get('question_id'))
        return HierarchyItem.objects.filter(question=self.question, is_active=True).order_by('order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self.question
        context['survey'] = self.question.survey
        return context

class HierarchyItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear un nuevo elemento de jerarquía
    """
    permission_required = 'survey.add_hierarchyitem'
    model = HierarchyItem
    form_class = HierarchyItemForm
    template_name = 'core/create.html'
    
    def get_initial(self):
        initial = super().get_initial()
        self.question = get_object_or_404(Question, pk=self.kwargs.get('question_id'))
        initial['question'] = self.question
        
        max_order = HierarchyItem.objects.filter(
            question=self.question
        ).aggregate(Max('order'))['order__max'] or 0
        initial['order'] = max_order + 1
        return initial 

    def get_success_url(self):
        return reverse_lazy('encuestas:hierarchy_item_list', args=[self.kwargs.get('question_id')])  # Get from kwargs
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self.question
        context['survey'] = self.question.survey
        context['title'] = 'Añadir Elemento de Jerarquía'
        context['list_url'] = reverse_lazy('encuestas:hierarchy_item_list', args=[self.kwargs.get('question_id')])  # Get from kwargs
        context['action'] = 'add'
        # context['form'] = self.get_form()
        return context
    
    def form_valid(self, form):
        # Establecer la pregunta y el orden
        form.instance.question = self.question
        
        # Obtener el último orden
        last_item = HierarchyItem.objects.filter(
            question=self.question, is_active=True
        ).order_by('-order').first()
        
        if last_item:
            form.instance.order = last_item.order + 1
        else:
            form.instance.order = 1
        
        form.instance.is_active = True
        return super().form_valid(form)
    
    def form_invalid(self, form):
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _("There was an error adding the hierarchy item"),
                'errors': form.errors
            }, status=400)
        else:
            return super().form_invalid(form)


class HierarchyItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Vista para actualizar un elemento de jerarquía existente
    """
    permission_required = 'survey.change_hierarchyitem'
    model = HierarchyItem
    form_class = HierarchyItemForm
    template_name = 'core/create.html'
    success_message = _("Elemento de jerarquía actualizado exitosamente")
    pk_url_kwarg = 'item_id'
            
    def get_queryset(self):
        # Filtra por question_id para asegurar que el ítem pertenece a la pregunta correcta
        return HierarchyItem.objects.filter(question_id=self.kwargs.get('question_id'))
    
    def get_success_url(self):
        return reverse_lazy('encuestas:hierarchy_item_list', args=[self.kwargs.get('question_id')])
    
    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        response = super().form_valid(form)
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': self.success_message,
                'item': {
                    'id': self.object.id,
                    'text': self.object.text,
                    'order': self.object.order,
                    'level': self.object.level,
                },
                'redirect': str(self.get_success_url())
            })
        return response
    
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]
                
            return JsonResponse({
                'success': False,
                'message': _("Hubo un error al actualizar el elemento de jerarquía"),
                'errors': errors
            }, status=400)
        else:
            return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = get_object_or_404(Question, pk=self.kwargs.get('question_id'))
        context['survey'] = context['question'].survey
        context['title'] = _('Editar Elemento de Jerarquía')
        context['entity'] = _('Elemento de Jerarquía')
        context['list_url'] = reverse_lazy('encuestas:hierarchy_item_list', args=[self.kwargs.get('question_id')])
        context['action'] = 'edit'
        return context


class HierarchyItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Vista para eliminar un elemento de jerarquía
    """
    permission_required = 'survey.delete_hierarchyitem'
    model = HierarchyItem
    template_name = 'core/del.html'
    context_object_name = 'item'
    pk_url_kwarg = 'item_id'
    
    def get_queryset(self):
        # Filtra por question_id para asegurar que el ítem pertenece a la pregunta correcta
        return HierarchyItem.objects.filter(
            question_id=self.kwargs.get('question_id'),
            is_active=True
        )
    
    def get_success_url(self):
        return reverse_lazy('encuestas:hierarchy_item_list', args=[self.kwargs.get('question_id')])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = get_object_or_404(Question, pk=self.kwargs.get('question_id'))
        context['survey'] = context['question'].survey
        context['title'] = _('Eliminar Elemento de Jerarquía')
        context['entity'] = _('Elemento de Jerarquía')
        context['texto'] = f'¿Seguro de eliminar el Elemento de Jerarquía {self.object}?'
        context['list_url'] = self.get_success_url()
        return context
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_message = _(f'Elemento de Jerarquía eliminado exitosamente')
        question = self.object.question
        deleted_order = self.object.order
        
        try:
            # En lugar de eliminar realmente, marcamos como inactivo
            self.object.is_active = False
            self.object.save()
            
            # Reordenar los elementos restantes
            HierarchyItem.objects.filter(
                question=question,
                is_active=True,
                order__gt=deleted_order
            ).update(order=F('order') - 1)
            
            # Respuesta para AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': success_message,
                    'redirect': str(self.get_success_url())
                })
            
            # Para solicitudes normales
            messages.success(request, success_message)
            return HttpResponseRedirect(self.get_success_url())
            
        except Exception as e:
            error_message = _(f'Ocurrió un error al eliminar el elemento de jerarquía: {str(e)}')
            messages.error(request, error_message)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                }, status=500)
            return HttpResponseRedirect(self.get_success_url())
    
    def post(self, request, *args, **kwargs):
        # Manejo consistente para peticiones AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                return self.delete(request, *args, **kwargs)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=500)
        return super().post(request, *args, **kwargs)

@login_required
def hierarchy_item_list(request, question_id):
    """Display all hierarchy items for a question"""
    question = get_object_or_404(Question, id=question_id)
    
    # Check if user has permission to view these items
    if question.survey.created_by != request.user:
        messages.error(request, _("You don't have permission to view these items"))
        return redirect('encuestas:survey_detail', survey_id=question.survey.id)
    
    # Get items grouped by level
    items_by_level = {}
    items = HierarchyItem.objects.filter(question=question).select_related('parent')
    
    for item in items:
        if item.level not in items_by_level:
            items_by_level[item.level] = []
        items_by_level[item.level].append(item)
    
    # Sort levels and items within levels
    sorted_levels = sorted(items_by_level.keys())
    for level in sorted_levels:
        items_by_level[level] = sorted(items_by_level[level], key=lambda x: x.order)
    
    context = {
        'question': question,
        'items_by_level': items_by_level,
        'sorted_levels': sorted_levels,
        'survey': question.survey,
    }
    
    return render(request, 'encuestas/hierarchy_item_list.html', context)


@login_required
def hierarchy_item_create(request, question_id):
    """Create a new hierarchy item"""
    question = get_object_or_404(Question, id=question_id)
    
    # Check if user has permission to add items
    if question.survey.created_by != request.user:
        messages.error(request, _("You don't have permission to add items to this question"))
        return redirect('encuestas:survey_detail', survey_id=question.survey.id)
    
    # Check if parent_id is provided
    parent_id = request.GET.get('parent_id')
    parent = None
    if parent_id:
        try:
            parent = HierarchyItem.objects.get(id=parent_id, question=question)
        except HierarchyItem.DoesNotExist:
            parent = None
    
    # Handle form submission
    if request.method == 'POST':
        form = HierarchyItemForm(request.POST)
        if form.is_valid():
            hierarchy_item = form.save(commit=False)
            hierarchy_item.question = question
            
            # Set parent if provided in the form
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
            
            messages.success(request, _("Hierarchy item added successfully"))
            
            # If AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': _("Hierarchy item added successfully"),
                    'item': {
                        'id': hierarchy_item.id,
                        'text': hierarchy_item.text,
                        'order': hierarchy_item.order,
                        'level': hierarchy_item.level,
                    }
                })
            
            return redirect('encuestas:hierarchy_item_list', question_id=question.id)
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _("There was an error adding the hierarchy item"),
                'errors': form.errors
            }, status=400)
    else:
        # Initialize form with parent if provided
        initial_data = {}
        if parent:
            initial_data['parent_id'] = parent.id
        
        form = HierarchyItemForm(initial=initial_data)
    
    # Get all possible parents for dropdown
    possible_parents = HierarchyItem.objects.filter(question=question)
    
    context = {
        'form': form,
        'question': question,
        'parent': parent,
        'possible_parents': possible_parents,
        'survey': question.survey,
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
    }
    
    if context['is_ajax']:
        return render(request, 'encuestas/includes/hierarchy_item_form.html', context)
    
    return render(request, 'encuestas/hierarchy_item_create.html', context)


@login_required
def hierarchy_item_update(request, item_id):
    """Update an existing hierarchy item"""
    item = get_object_or_404(HierarchyItem, id=item_id)
    question = item.question
    
    # Check if user has permission to edit this item
    if question.survey.created_by != request.user:
        messages.error(request, _("You don't have permission to edit this item"))
        return redirect('encuestas:survey_detail', survey_id=question.survey.id)
    
    # Process form submission
    if request.method == 'POST':
        form = HierarchyItemForm(request.POST, instance=item)
        if form.is_valid():
            # Check for circular references in parent
            parent_id = form.cleaned_data.get('parent_id')
            if parent_id:
                if str(item.id) == parent_id:
                    messages.error(request, _("An item cannot be its own parent"))
                    return redirect('encuestas:hierarchy_item_update', item_id=item.id)
                
                try:
                    parent = HierarchyItem.objects.get(id=parent_id, question=question)
                    
                    # Check if the selected parent is a descendant of the item
                    descendants = item.get_children_recursive()
                    if parent in descendants:
                        messages.error(request, _("Cannot select a descendant as parent"))
                        return redirect('encuestas:hierarchy_item_update', item_id=item.id)
                    
                    form.instance.parent = parent
                except HierarchyItem.DoesNotExist:
                    form.instance.parent = None
            else:
                form.instance.parent = None
            
            item = form.save()
            
            messages.success(request, _("Hierarchy item updated successfully"))
            
            # If AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': _("Hierarchy item updated successfully"),
                    'item': {
                        'id': item.id,
                        'text': item.text,
                        'order': item.order,
                        'level': item.level,
                    }
                })
            
            return redirect('encuestas:hierarchy_item_list', question_id=question.id)
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _("There was an error updating the hierarchy item"),
                'errors': form.errors
            }, status=400)
    else:
        # Initialize form with current values
        initial_data = {}
        if item.parent:
            initial_data['parent_id'] = item.parent.id
        
        form = HierarchyItemForm(instance=item, initial=initial_data)
    
    # Get all possible parents for dropdown (excluding self and descendants)
    descendants = item.get_children_recursive()
    descendants_ids = [d.id for d in descendants]
    descendants_ids.append(item.id)  # Exclude self
    
    possible_parents = HierarchyItem.objects.filter(question=question).exclude(
        id__in=descendants_ids
    )
    
    context = {
        'form': form,
        'item': item,
        'question': question,
        'possible_parents': possible_parents,
        'survey': question.survey,
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
    }
    
    if context['is_ajax']:
        return render(request, 'encuestas/includes/hierarchy_item_form.html', context)
    
    return render(request, 'encuestas/hierarchy_item_update.html', context)


@login_required
def hierarchy_item_delete(request, item_id):
    """Delete a hierarchy item"""
    item = get_object_or_404(HierarchyItem, id=item_id)
    question = item.question
    
    # Check if user has permission to delete this item
    if question.survey.created_by != request.user:
        messages.error(request, _("You don't have permission to delete this item"))
        return redirect('encuestas:survey_detail', survey_id=question.survey.id)
    
    # Handle form submission
    if request.method == 'POST':
        # Remember the question ID before deleting
        question_id = question.id
        
        # Delete the item (and its children due to CASCADE)
        item.delete()
        
        messages.success(request, _("Hierarchy item deleted successfully"))
        
        # If AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _("Hierarchy item deleted successfully"),
                'items_count': HierarchyItem.objects.filter(question_id=question_id).count()
            })
        
        return redirect('encuestas:hierarchy_item_list', question_id=question_id)
    
    context = {
        'item': item,
        'question': question,
        'survey': question.survey,
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
    }
    
    if context['is_ajax']:
        return render(request, 'encuestas/includes/hierarchy_item_delete_confirmation.html', context)
    
    return render(request, 'encuestas/hierarchy_item_delete.html', context)


@login_required
@require_http_methods(["POST"])
def hierarchy_item_reorder(request, question_id):
    """Reorder hierarchy items"""
    question = get_object_or_404(Question, id=question_id)
    
    # Check if user has permission to reorder items
    if question.survey.created_by != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _("You don't have permission to reorder these items")
            }, status=403)
        
        messages.error(request, _("You don't have permission to reorder these items"))
        return redirect('encuestas:survey_detail', survey_id=question.survey.id)
    
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
    

    """
    Vista para reordenar los elementos de jerarquía
    """
    question = get_object_or_404(Question, pk=question_id)
    
    try:
        data = json.loads(request.body)
        items_data = data.get('items', [])
        
        # Verificar que todos los elementos existen
        for item_data in items_data:
            item_id = item_data.get('id')
            new_order = item_data.get('order')
            
            item = get_object_or_404(HierarchyItem, pk=item_id, question=question, is_active=True)
            item.order = new_order
            item.save()
        
        return JsonResponse({
            'success': True
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)