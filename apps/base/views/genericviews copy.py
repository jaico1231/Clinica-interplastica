# # views.py
# from django.forms import modelform_factory
# from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView, TemplateView
# from django.urls import reverse_lazy
# from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
# from django.db.models import Q
# import logging

# logger = logging.getLogger(__name__)

# class LayoutView(TemplateView):
#     template_name = None 
#     pass

# from django.utils.functional import cached_property

# class GenericListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
#     """
#     Vista genérica para listados con soporte para DataTables,
#     búsqueda, acciones y botones personalizados.
#     """
#     template_name = 'core/list.html'
#     context_object_name = 'object_list'
#     permission_required = None  # Debe ser definido en cada vista hija
#     url_toggle = None  # Opcional: URL para toggle de estado
    
#     # Configuración básica (sobrescribir en vistas hijas)
#     list_title = "Título de Listado"
#     headers = []
#     fields = []
#     actions = []
#     btn_add = []
#     entity_name = "Entidad"
    
#     # Configuración de búsqueda
#     search_fields = []  # Campos para búsqueda
#     order_by = None  # Campo para ordenamiento por defecto
    
#     # Controles de debug
#     debug_mode = False

#     def get_queryset(self):
#         """
#         Obtiene y filtra el queryset base.
#         Incluye búsqueda si search_fields está definido.
#         """
#         queryset = super().get_queryset()
        
#         # Aplicar búsqueda si hay search_fields definidos
#         search_term = self.request.GET.get('search', '')
#         if search_term and self.search_fields:
#             q_objects = Q()
#             for field in self.search_fields:
#                 q_objects |= Q(**{f"{field}__icontains": search_term})
#             queryset = queryset.filter(q_objects)
        
#         # Aplicar ordenamiento por defecto
#         if self.order_by:
#             queryset = queryset.order_by(self.order_by)
            
#         # Depuración si está habilitada
#         if self.debug_mode:
#             logger.debug(f"Query: {queryset.query}")
            
#         return queryset

#     def get_context_data(self, **kwargs):
#         """
#         Prepara el contexto para el template incluyendo la configuración
#         de la vista y metadatos necesarios para renderizado especializado.
#         """
#         context = super().get_context_data(**kwargs)
        
#         # Información básica
#         context.update({
#             'title': self.list_title,
#             'headers': self.headers,
#             'fields': self.fields,
#             'actions': self.actions,
#             'Btn_Add': self.btn_add,
#             'entity': self.entity_name,
#             'url_toggle': self.url_toggle,
#             'search_term': self.request.GET.get('search', ''),
#         })
        
#         # Información de tipos de campo para renderizado especializado
#         context['field_info'] = self._get_field_info()
        
#         # Depuración si está habilitada
#         if self.debug_mode:
#             self._debug_context(context)
            
#         return context
    
#     def _get_field_info(self):
#         """
#         Genera información sobre los tipos de campo para
#         permitir un renderizado adaptado a cada tipo de dato.
#         """
#         field_info = {}
        
#         if not hasattr(self, 'model') or not self.model:
#             return field_info
        
#         # Obtener información sobre todos los campos del modelo
#         model_fields = {}
#         for field in self.model._meta.get_fields():
#             model_fields[field.name] = field
        
#         # Analizar cada campo en la lista de campos a mostrar
#         for field_name in self.fields:
#             # Manejar campos anidados con punto (relaciones)
#             if '.' in field_name:
#                 parts = field_name.split('.')
#                 base_field = parts[0]
                
#                 if base_field in model_fields:
#                     field_info[field_name] = {
#                         'type': 'related',
#                         'base_field': base_field,
#                         'related_field': '.'.join(parts[1:])
#                     }
#                 else:
#                     field_info[field_name] = {'type': 'unknown'}
#                 continue
            
#             # Campos simples (no anidados)
#             if field_name in model_fields:
#                 field = model_fields[field_name]
#                 field_type = self._get_field_type(field)
                
#                 field_info[field_name] = {
#                     'type': field_type,
#                     'name': field_name,
#                     'verbose_name': getattr(field, 'verbose_name', field_name.replace('_', ' ').title())
#                 }
#             else:
#                 # Campo no encontrado en el modelo - podría ser un método o propiedad
#                 field_info[field_name] = {'type': 'custom'}
        
#         return field_info
    
#     def _get_field_type(self, field):
#         """Determina el tipo de campo para su renderizado especializado."""
#         # Primero verificar si es booleano
#         if field.get_internal_type() == 'BooleanField':
#             return 'boolean'
            
#         # Campos de fecha/hora
#         if field.get_internal_type() in ['DateField', 'DateTimeField']:
#             return 'date'
            
#         # Campos de relación
#         if field.get_internal_type() in ['ForeignKey', 'OneToOneField', 'ManyToManyField']:
#             return 'related'
            
#         # Otros tipos de campo
#         if field.get_internal_type() == 'TextField':
#             return 'text'
            
#         if field.get_internal_type() in ['IntegerField', 'DecimalField', 'FloatField']:
#             return 'number'
            
#         if field.get_internal_type() == 'FileField':
#             return 'file'
            
#         if field.get_internal_type() == 'ImageField':
#             return 'image'
            
#         # Para otros casos, usar tipo simple
#         return 'simple'
    
#     def _debug_context(self, context):
#         """Imprime información detallada sobre el contexto para depuración."""
#         logger.debug(f"[{self.__class__.__name__}] Contexto enviado al template:")
#         logger.debug(f"- Título: {context.get('title')}")
#         logger.debug(f"- Headers: {context.get('headers')}")
#         logger.debug(f"- Campos: {context.get('fields')}")
#         logger.debug(f"- Tipos de campo: {context.get('field_info')}")
#         logger.debug(f"- Total registros: {len(context.get(self.context_object_name, []))}")
#     # def get_context_data(self, **kwargs):
#     #     context = super().get_context_data(**kwargs)
        
#     #     # Validar que los campos existan en el modelo
#     #     self._validate_fields()
        
#     #     # Construir información de campos para mejor renderizado
#     #     field_info = self._build_field_info()
        
#     #     context.update({
#     #         'title': self.list_title,
#     #         'headers': self.headers,
#     #         'fields': self.fields,
#     #         'field_info': field_info,  # Información adicional sobre los campos
#     #         'actions': self.actions,
#     #         'Btn_Add': self.btn_add,
#     #         'entity': self.entity_name,
#     #         'url_toggle': self.url_toggle
#     #     })
#     #     return context
    
#     # def _validate_fields(self):
#     #     """Valida que los campos especificados existan en el modelo"""
#     #     if not hasattr(self, 'model') or not self.model:
#     #         return
            
#     #     model_fields = [f.name for f in self.model._meta.get_fields()]
        
#     #     for i, field in enumerate(self.fields):
#     #         # Comprobar si es un campo compuesto (con punto)
#     #         if '.' in field:
#     #             base_field = field.split('.')[0]
#     #             if base_field not in model_fields:
#     #                 # Si no existe, eliminarlo o mostrar advertencia
#     #                 print(f"Advertencia: El campo '{base_field}' no existe en {self.model.__name__}")
#     #         elif field not in model_fields:
#     #             print(f"Advertencia: El campo '{field}' no existe en {self.model.__name__}")
    
#     # def _build_field_info(self):
#     #     """
#     #     Construye información adicional sobre los campos para ayudar
#     #     en el renderizado en la plantilla.
#     #     """
#     #     if not hasattr(self, 'model') or not self.model:
#     #         return {}
            
#     #     result = {}
#     #     model_fields = {f.name: f for f in self.model._meta.get_fields()}
        
#     #     for field_name in self.fields:
#     #         if '.' in field_name:
#     #             # Campo relacionado con punto
#     #             base_field = field_name.split('.')[0]
#     #             if base_field in model_fields:
#     #                 result[field_name] = {
#     #                     'type': 'related',
#     #                     'is_simple': False
#     #                 }
#     #             else:
#     #                 result[field_name] = {'type': 'unknown', 'is_simple': True}
#     #         elif field_name in model_fields:
#     #             field = model_fields[field_name]
#     #             # Detectar tipo de campo para renderizado
#     #             if field.get_internal_type() == 'BooleanField':
#     #                 result[field_name] = {'type': 'boolean', 'is_simple': True}
#     #             elif field.get_internal_type() in ['DateField', 'DateTimeField']:
#     #                 result[field_name] = {'type': 'date', 'is_simple': True}
#     #             elif field.get_internal_type() in ['ForeignKey', 'OneToOneField', 'ManyToManyField']:
#     #                 result[field_name] = {'type': 'related', 'is_simple': False}
#     #             else:
#     #                 # Campos simples (texto, número, etc.)
#     #                 result[field_name] = {'type': 'simple', 'is_simple': True}
#     #         else:
#     #             # Podría ser un atributo calculado o método
#     #             result[field_name] = {'type': 'unknown', 'is_simple': True}
                
#     #     return result
    
# class BaseCrudMixin(LoginRequiredMixin, PermissionRequiredMixin):
#     """
#     Mixin base para todas las vistas CRUD
#     """
#     success_message = None
#     exclude_fields = []  # Campos a excluir del formulario automático
#     template_name = None

#     def get_success_url(self):
#         """Genera URL de redirección basada en convenciones de nomenclatura"""
#         if hasattr(self, 'success_url') and self.success_url:
#             return self.success_url

#         app_label = self.model._meta.app_label
#         model_name = self.model._meta.model_name
#         return reverse_lazy(f'{app_label}:{model_name}_list')

#     def get_permission_required(self):
#         """Genera permisos requeridos basados en el modelo y la acción"""
#         if self.permission_required:
#             return self.permission_required

#         app_label = self.model._meta.app_label
#         model_name = self.model._meta.model_name
        
#         if isinstance(self, CreateView):
#             action = 'add'
#         elif isinstance(self, UpdateView):
#             action = 'change'
#         elif isinstance(self, DeleteView):
#             action = 'delete'
#         else:
#             action = 'view'
            
#         return [f'{app_label}.{action}_{model_name}']

#     def get_context_data(self, **kwargs):
#         """Agrega contexto común para todas las vistas"""
#         context = super().get_context_data(**kwargs)
        
#         # Metadata del modelo
#         model_verbose_name = self.model._meta.verbose_name.title()
#         context['model_name'] = model_verbose_name
#         context['model_name_plural'] = self.model._meta.verbose_name_plural.title()
        
#         # Información de acción
#         action_verb = 'Crear' if isinstance(self, CreateView) else \
#                      'Editar' if isinstance(self, UpdateView) else \
#                      'Eliminar' if isinstance(self, DeleteView) else ''
        
#         context['action_verb'] = action_verb
#         context['title'] = f"{action_verb} {model_verbose_name}"
        
#         return context

#     def get_form_class(self):
#         """Usa ModelForm con campos configurados o excluidos automáticamente"""
#         if hasattr(self, 'form_class') and self.form_class:
#             return self.form_class
            
#         if hasattr(self, 'fields') and self.fields != '__all__':
#             return modelform_factory(self.model, fields=self.fields)
            
#         return modelform_factory(self.model, exclude=self.exclude_fields)

#     def get_success_message(self):
#         """Mensaje a mostrar después de una operación exitosa"""
#         if self.success_message:
#             return self.success_message
            
#         model_name = self.model._meta.verbose_name
#         if isinstance(self, CreateView):
#             return f"{capfirst(model_name)} creado exitosamente."
#         elif isinstance(self, UpdateView):
#             return f"{capfirst(model_name)} actualizado exitosamente."
#         elif isinstance(self, DeleteView):
#             return f"{capfirst(model_name)} eliminado exitosamente."
#         return "Operación completada exitosamente."

# class GenericCreateView(BaseCrudMixin, CreateView):
#     """Vista genérica para creación de registros"""
#     def get_template_names(self):
#         """Determina la plantilla a usar"""
#         if self.template_name:
#             return [self.template_name]
            
#         model_name = self.model._meta.model_name
#         app_label = self.model._meta.app_label
        
#         return [
#             f"{app_label}/{model_name}_create.html",
#             f"{app_label}/generic_create.html",
#             "core/generic_form.html"
#         ]

#     def form_valid(self, form):
#         """Registra campos de auditoría y muestra mensaje de éxito"""
#         # Agregar usuario creador si existe el campo
#         if hasattr(form.instance, 'created_by'):
#             form.instance.created_by = self.request.user
            
#         if hasattr(form.instance, 'modified_by'):
#             form.instance.modified_by = self.request.user
            
#         response = super().form_valid(form)
#         messages.success(self.request, self.get_success_message())
#         return response

#     def form_invalid(self, form):
#         """Muestra mensajes de error en formularios inválidos"""
#         for field, errors in form.errors.items():
#             for error in errors:
#                 if field == '__all__':
#                     messages.error(self.request, f"Error: {error}")
#                 else:
#                     field_name = form.fields[field].label or field
#                     messages.error(self.request, f"Error en {field_name}: {error}")
        
#         return super().form_invalid(form)

# class GenericUpdateView(BaseCrudMixin, UpdateView):
#     """Vista genérica para actualizar registros"""
#     def get_template_names(self):
#         """Determina la plantilla a usar"""
#         if self.template_name:
#             return [self.template_name]
            
#         model_name = self.model._meta.model_name
#         app_label = self.model._meta.app_label
        
#         return [
#             f"{app_label}/{model_name}_update.html",
#             f"{app_label}/generic_update.html",
#             f"{app_label}/{model_name}_form.html",
#             "core/generic_form.html"
#         ]

#     def form_valid(self, form):
#         """Registra usuario que modifica y muestra mensaje de éxito"""
#         if hasattr(form.instance, 'modified_by'):
#             form.instance.modified_by = self.request.user
            
#         response = super().form_valid(form)
#         messages.success(self.request, self.get_success_message())
#         return response
        
#     def form_invalid(self, form):
#         """Muestra mensajes de error en formularios inválidos"""
#         for field, errors in form.errors.items():
#             for error in errors:
#                 if field == '__all__':
#                     messages.error(self.request, f"Error: {error}")
#                 else:
#                     field_name = form.fields[field].label or field
#                     messages.error(self.request, f"Error en {field_name}: {error}")
        
#         return super().form_invalid(form)

# class GenericDeleteView(BaseCrudMixin, DeleteView):
#     """Vista genérica para eliminar registros"""
#     def get_template_names(self):
#         """Determina la plantilla a usar"""
#         if self.template_name:
#             return [self.template_name]
            
#         model_name = self.model._meta.model_name
#         app_label = self.model._meta.app_label
        
#         return [
#             f"{app_label}/{model_name}_delete.html",
#             f"{app_label}/generic_delete.html",
#             "core/generic_confirm_delete.html"
#         ]

#     def post(self, request, *args, **kwargs):
#         """
#         Maneja eliminación, usando soft_delete si está disponible
#         """
#         self.object = self.get_object()
#         success_url = self.get_success_url()
        
#         # Si el modelo tiene soft_delete, usarlo en lugar de eliminar
#         if hasattr(self.object, 'soft_delete') and callable(getattr(self.object, 'soft_delete')):
#             try:
#                 self.object.soft_delete(user=request.user)
#                 messages.success(request, self.get_success_message())
#                 return redirect(success_url)
#             except Exception as e:
#                 messages.error(request, f"Error al eliminar: {str(e)}")
#                 return self.render_to_response(self.get_context_data())
        
#         # Eliminación normal
#         try:
#             response = super().delete(request, *args, **kwargs)
#             messages.success(request, self.get_success_message())
#             return response
#         except Exception as e:
#             messages.error(request, f"Error al eliminar: {str(e)}")
#             return self.render_to_response(self.get_context_data())