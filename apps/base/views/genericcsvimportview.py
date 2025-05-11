import csv
import json
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import models
from django.forms import modelform_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import View, FormView
from django import forms
from io import StringIO, TextIOWrapper
from decimal import Decimal, InvalidOperation
from django.core.exceptions import FieldDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction


class GenericCSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='Seleccionar archivo CSV',
        help_text='Seleccione un archivo CSV para importar'
    )


class GenericCSVImportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    model = None  # Debe ser definido en la clase hija o al instanciar
    template_name = 'import/csvimport_template.html'
    success_url = None  # Debe ser definido en la clase hija o al instanciar
    unique_field = None  # Campo para identificar registros existentes (ej: 'reference_code')
    permission_required = 'add_model'  # Debe ser definido en la clase hija
    exclude_fields = [
        'id', 'created_at', 'updated_at', 'image', 
        'modified_at', 'created_by', 'modified_by', 
        'is_active', 'deleted_at', 'deleted_by'
    ]  # Campos a excluir de la importación
    preview_rows = 5  # Número de filas a mostrar en la vista previa
    csv_delimiter = ';'  # Delimitador para el CSV
    csv_quotechar = '"'  # Carácter para entrecomillar campos

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if self.model:
            self.model_name = self.model._meta.model_name
            self.app_name = self.model._meta.app_label
            if not self.success_url:
                self.success_url = reverse_lazy(f'{self.app_name}:{self.model_name}_list')
            
            # Configurar permiso automáticamente
            if self.permission_required == 'add_model':
                self.permission_required = f'{self.app_name}.add_{self.model_name}'

    def get(self, request, *args, **kwargs):
        print("GET method called with:", request.GET)
        
        # If template download requested
        if 'download_template' in request.GET:
            print("Downloading template")
            return self.download_template()
        
        # If preview requested
        if 'preview' in request.GET:
            print("Preview requested, session keys:", request.session.keys())
            if 'csv_data' in request.session:
                print("CSV data found in session")
                return self.preview_import(request)
            else:
                print("CSV data NOT found in session")
                messages.error(request, "No CSV data found in session. Please upload a file first.")
        
        # Main upload view
        print("Showing main upload form")
        form = GenericCSVImportForm()
        return self.render_response(request, {'form': form})

    def post(self, request, *args, **kwargs):
        
        # Confirm import after preview
        if 'confirm_import' in request.POST and 'csv_data' in request.session:
            print("Confirming import")
            return self.process_import(request)
        
        # Process uploaded file for preview
        form = GenericCSVImportForm(request.POST, request.FILES)
        if not form.is_valid():
            print("Form is not valid:", form.errors)
            return self.render_response(request, {'form': form})
        
        # Process the CSV file for preview
        csv_file = form.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            print("File is not a CSV:", csv_file.name)
            messages.error(request, _('El archivo debe ser un CSV'))
            return self.render_response(request, {'form': form})
        
        # Read the CSV file with different encodings
        print("Reading CSV file:", csv_file.name)
        
        # Lista de codificaciones para intentar
        encodings = ['latin-1', 'iso-8859-1', 'cp1252', 'utf-8']
        
        # Intentar diferentes codificaciones
        csv_data = None
        fieldnames = None
        error_message = None
        
        for encoding in encodings:
            try:
                # Reiniciar el puntero del archivo
                csv_file.file.seek(0)
                
                # Leer el contenido completo del archivo primero
                content = csv_file.file.read()
                # Decodificar el contenido con la codificación actual
                decoded_content = content.decode(encoding)
                
                # Crear un StringIO para usar csv.DictReader
                from io import StringIO
                csv_io = StringIO(decoded_content)
                
                # Usar el DictReader con configuración para manejar comillas
                reader = csv.DictReader(
                    csv_io, 
                    delimiter=self.csv_delimiter,
                    quotechar=self.csv_quotechar
                )
                
                # Forzar la lectura de fieldnames
                if not reader.fieldnames:
                    error_message = "No se pudieron leer los encabezados del archivo"
                    continue
                
                # Guardar los nombres de campo - Ya deben estar bien manejados con las comillas
                fieldnames = reader.fieldnames
                
                # Imprimir nombres de campos para depuración
                print(f"Detected fieldnames: {fieldnames}")
                
                # Leer todos los datos
                csv_data = list(reader)
                
                # Si hay datos, mostrar primera fila para depuración
                if csv_data:
                    print(f"First row: {csv_data[0]}")
                
                # Si llegamos aquí, la decodificación fue exitosa
                print(f"Successfully decoded with {encoding}")
                break
            except Exception as e:
                error_message = f"Error con codificación {encoding}: {str(e)}"
                print(error_message)
        
        # Si no se pudo decodificar con ninguna codificación
        if csv_data is None or not fieldnames:
            messages.error(request, _(f'No se pudo procesar el archivo CSV. {error_message}'))
            return self.render_response(request, {'form': form})
        
        # Validate required fields
        required_fields = self.get_required_fields()
        print("Required fields:", required_fields)
        missing_fields = []
        for field in required_fields:
            if field not in fieldnames:
                missing_fields.append(field)
        
        if missing_fields:
            fields_str = ", ".join(missing_fields)
            messages.error(request, _(f'El archivo no contiene los campos obligatorios: {fields_str}'))
            return self.render_response(request, {'form': form})
        
        # Save data in session for preview
        print(f"Storing {len(csv_data)} rows in session")
        request.session['csv_data'] = json.dumps(csv_data, cls=DjangoJSONEncoder)
        request.session['csv_fieldnames'] = fieldnames
        request.session.modified = True  # Explicitly mark the session as modified
        
        # Redirect to preview
        preview_url = f"{request.path}?preview=1"
        print(f"Redirecting to preview: {preview_url}")
        return redirect(preview_url)

    def preview_import(self, request):
        """Versión con depuración mejorada para identificar problemas de previsualización"""
        print("Starting preview_import method")
        try:
            # Verificar que los datos existen en la sesión
            if 'csv_data' not in request.session:
                messages.error(request, _('No se encontraron datos CSV en la sesión. Por favor, cargue el archivo nuevamente.'))
                return redirect(request.path)
                
            # Intentar cargar los datos
            csv_data = json.loads(request.session['csv_data'])
            fieldnames = request.session.get('csv_fieldnames', [])
            
            # Registrar para depuración
            print(f"CSV fieldnames: {fieldnames}")
            print(f"CSV data (primeras 2 filas): {csv_data[:2] if csv_data else 'No hay datos'}")
            
            # Limitar a primeras filas para vista previa
            preview_data = csv_data[:self.preview_rows]
            total_rows = len(csv_data)
            
            # Analizar estado de cada fila
            validated_rows = []
            for i, row in enumerate(preview_data):
                try:
                    row_status = self.validate_row(row)
                    validated_rows.append({
                        'data': row,
                        'status': row_status['status'],
                        'message': row_status['message']
                    })
                    print(f"Fila {i+1} validada: {row_status}")
                except Exception as e:
                    print(f"Error validando fila {i+1}: {str(e)}")
                    messages.error(request, _(f"Error procesando fila {i+1}: {str(e)}"))
            
            # Estadísticas
            try:
                total_valid = sum(1 for row in csv_data if self.validate_row(row)['status'] in ['new', 'update'])
                total_invalid = total_rows - total_valid
            except Exception as e:
                print(f"Error calculando estadísticas: {str(e)}")
                total_valid = 0
                total_invalid = 0
                messages.error(request, _(f"Error calculando estadísticas: {str(e)}"))
            
            # Verificar la plantilla
            template_exists = True
            try:
                from django.template.loader import get_template
                template = get_template(self.template_name)
            except Exception as e:
                template_exists = False
                print(f"Error verificando plantilla {self.template_name}: {str(e)}")
                messages.error(request, _(f"Error con la plantilla: {str(e)}"))
            
            # Preparar contexto
            context = {
                'preview': True,
                'fieldnames': fieldnames,
                'validated_rows': validated_rows,
                'total_rows': total_rows,
                'total_valid': total_valid,
                'total_invalid': total_invalid,
                'model_name': self.model._meta.verbose_name,
                'model_name_plural': self.model._meta.verbose_name_plural,
                'template_exists': template_exists,
            }
            
            return self.render_response(request, context)
        except json.JSONDecodeError as e:
            print(f"Error decodificando JSON: {str(e)}")
            messages.error(request, _('Error al cargar los datos JSON. Por favor, inténtelo de nuevo.'))
        except Exception as e:
            print(f"Error general en preview_import: {str(e)}")
            messages.error(request, _(f'Error al cargar la vista previa: {str(e)}'))
        
        return redirect(request.path)
    
    def process_import(self, request):
        try:
            # Verificar que los datos existen en la sesión
            if 'csv_data' not in request.session:
                print("No CSV data found in session")
                messages.error(request, _('No se encontraron datos CSV en la sesión. Por favor, cargue el archivo nuevamente.'))
                return redirect(request.path)
            
            # Cargar datos de la sesión    
            try:
                csv_data = json.loads(request.session['csv_data'])
                print(f"Loaded {len(csv_data)} rows from session")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")
                messages.error(request, _('Error al decodificar los datos JSON de la sesión.'))
                return redirect(request.path)
            
            # Procesar todas las filas para importación real
            stats = {
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'errors': []
            }
            
            # Procesar cada fila en su propia transacción
            for row_num, row in enumerate(csv_data, start=2):  # start=2 porque la fila 1 son los encabezados
                try:
                    print(f"Processing row {row_num}: {row}")
                    
                    # Usar transacción individual para cada fila
                    with transaction.atomic():
                        result = self.process_row(row)
                        
                        if result['status'] == 'new':
                            stats['created'] += 1
                            print(f"Row {row_num}: Created new record")
                        elif result['status'] == 'update':
                            stats['updated'] += 1
                            print(f"Row {row_num}: Updated existing record")
                        elif result['status'] == 'error':
                            stats['skipped'] += 1
                            error_msg = f"Fila {row_num}: {result['message']}"
                            stats['errors'].append(error_msg)
                            print(f"Row {row_num}: Error - {result['message']}")
                except Exception as e:
                    stats['skipped'] += 1
                    error_msg = f"Fila {row_num}: Error inesperado - {str(e)}"
                    stats['errors'].append(error_msg)
                    print(f"Row {row_num}: Unexpected error - {str(e)}")
            
            # Limpiar datos de sesión
            if 'csv_data' in request.session:
                del request.session['csv_data']
            if 'csv_fieldnames' in request.session:
                del request.session['csv_fieldnames']
            
            print(f"Import stats: created={stats['created']}, updated={stats['updated']}, skipped={stats['skipped']}, errors={len(stats['errors'])}")
            
            # Preparar mensaje detallado para mostrar en modal/alert
            message_details = []
            if stats['created'] > 0:
                message_details.append(f"Se han creado {stats['created']} registros nuevos")
            if stats['updated'] > 0:
                message_details.append(f"Se han actualizado {stats['updated']} registros existentes")
            if stats['skipped'] > 0:
                message_details.append(f"Se han omitido {stats['skipped']} registros por errores")
            
            # Almacenar detalles completos en la sesión para modal
            if stats['errors']:
                message_details.append(f"Se encontraron {len(stats['errors'])} errores")
                request.session['import_errors'] = stats['errors'][:100]  # Limitamos a 100 errores para no sobrecargar
                request.session['import_has_more_errors'] = len(stats['errors']) > 100
                request.session.modified = True
            
            # Mensaje simple para flash
            summary_message = ". ".join(message_details)
            if stats['created'] > 0 or stats['updated'] > 0:
                messages.success(request, _(f'Importación completada: {summary_message}'))
                # Mensaje para indicar que hay detalles disponibles
                if stats['errors']:
                    messages.warning(request, _('Haga clic en "Ver detalles" para información sobre los errores.'))
            else:
                messages.error(request, _(f'Importación fallida: {summary_message}'))
            
            # Guardar estadísticas en sesión para mostrar modal
            request.session['import_stats'] = {
                'created': stats['created'],
                'updated': stats['updated'],
                'skipped': stats['skipped'],
                'errors_count': len(stats['errors'])
            }
            request.session.modified = True
            
            # Si todo fue exitoso o parcialmente exitoso, redirigir a la URL de éxito
            return redirect(self.success_url)
                
        except Exception as e:
            # Capturar cualquier error no manejado
            print(f"Unexpected error in process_import: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, _(f'Error inesperado durante la importación: {str(e)}'))
            return redirect(request.path)

    def validate_row(self, row):
        """Valida una fila y determina si se creará o actualizará un registro"""
        if not self.unique_field or not row.get(self.unique_field):
            # Sin campo único, se creará nuevo registro
            # Verificar campos requeridos
            for field in self.get_required_fields():
                if not row.get(field):
                    return {'status': 'error', 'message': f'Falta el campo requerido: {field}'}
            return {'status': 'new', 'message': 'Nuevo registro'}
        
        # Buscar registro existente por campo único
        try:
            existing = self.get_existing_object(row)
            if existing:
                return {'status': 'update', 'message': f'Actualizar registro existente #{existing.pk}'}
            else:
                return {'status': 'new', 'message': 'Nuevo registro'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def process_row(self, row):
        """Procesa una fila para crear o actualizar un registro"""
        print(f"Processing row data: {row}")
        
        # Verificar campos requeridos
        for field in self.get_required_fields():
            if not row.get(field):
                return {'status': 'error', 'message': f'Falta el campo requerido: {field}'}
        
        # Preparar datos
        try:
            cleaned_data = self.clean_row_data(row)
            print(f"Cleaned data: {cleaned_data}")
            
            if not cleaned_data:
                return {'status': 'error', 'message': 'No se pudieron procesar datos válidos de esta fila'}
            
            # Si tenemos campo único, buscar existente
            if self.unique_field and row.get(self.unique_field):
                try:
                    instance = self.get_existing_object(row)
                    if instance:
                        print(f"Found existing instance with {self.unique_field}={row[self.unique_field]}")
                        # Actualizar existente
                        for field, value in cleaned_data.items():
                            setattr(instance, field, value)
                        instance.save()
                        return {'status': 'update', 'message': 'Registro actualizado'}
                except Exception as e:
                    print(f"Error updating existing record: {str(e)}")
                    return {'status': 'error', 'message': f'Error al actualizar registro existente: {str(e)}'}
            
            # Crear nuevo
            try:
                print(f"Creating new record with data: {cleaned_data}")
                self.model.objects.create(**cleaned_data)
                return {'status': 'new', 'message': 'Registro creado'}
            except Exception as e:
                print(f"Error creating new record: {str(e)}")
                return {'status': 'error', 'message': f'Error al crear nuevo registro: {str(e)}'}
        except Exception as e:
            print(f"Unexpected error in process_row: {str(e)}")
            return {'status': 'error', 'message': f'Error inesperado: {str(e)}'}

    def clean_row_data(self, row):
        """Limpia y convierte los datos de la fila según los tipos de campo"""
        cleaned_data = {}
        print(f"Cleaning row data: {row}")
        
        # Obtener una lista de campos válidos del modelo
        valid_fields = self.get_model_fields()
        print(f"Valid model fields: {valid_fields}")
        
        for field_name, value in row.items():
            print(f"Processing field '{field_name}' with value '{value}'")
            
            # Saltar campos vacíos o en la lista de exclusión
            if not value or field_name in self.exclude_fields:
                print(f"Skipping field '{field_name}': empty or excluded")
                continue
            
            # Verificar si el campo existe en el modelo
            if field_name not in valid_fields:
                print(f"Skipping field '{field_name}': not in model fields")
                continue
                
            try:
                field = self.model._meta.get_field(field_name)
                
                # Convertir según tipo de campo
                if isinstance(field, models.IntegerField):
                    try:
                        cleaned_data[field_name] = int(value) if value.strip() else None
                        print(f"Converted '{field_name}' to integer: {cleaned_data[field_name]}")
                    except ValueError as e:
                        print(f"Error converting '{field_name}' to integer: {str(e)}")
                        continue
                        
                elif isinstance(field, models.DecimalField):
                    try:
                        # Reemplazar coma por punto para decimales
                        decimal_value = value.replace(',', '.').strip()
                        cleaned_data[field_name] = Decimal(decimal_value) if decimal_value else None
                        print(f"Converted '{field_name}' to decimal: {cleaned_data[field_name]}")
                    except InvalidOperation as e:
                        print(f"Error converting '{field_name}' to decimal: {str(e)}")
                        continue
                        
                elif isinstance(field, models.BooleanField):
                    bool_value = value.lower() in ('true', 'yes', 'si', 's', '1', 'verdadero')
                    cleaned_data[field_name] = bool_value
                    print(f"Converted '{field_name}' to boolean: {cleaned_data[field_name]}")
                    
                elif isinstance(field, models.ForeignKey):
                    if value.strip():
                        try:
                            # Intentar obtener objeto por ID
                            related_obj = field.related_model.objects.get(pk=int(value))
                            cleaned_data[field_name] = related_obj
                            print(f"Found related object for '{field_name}': {related_obj}")
                        except (field.related_model.DoesNotExist, ValueError) as e:
                            print(f"Error finding related object for '{field_name}': {str(e)}")
                            # Intentar buscar por nombre o código si es apropiado
                            # Este código es un ejemplo y puede necesitar adaptarse según tus modelos
                            if hasattr(field.related_model, 'name'):
                                try:
                                    related_obj = field.related_model.objects.get(name=value.strip())
                                    cleaned_data[field_name] = related_obj
                                    print(f"Found related object by name for '{field_name}': {related_obj}")
                                except (field.related_model.DoesNotExist, field.related_model.MultipleObjectsReturned) as e:
                                    print(f"Error finding related object by name for '{field_name}': {str(e)}")
                elif isinstance(field, models.DateField):
                    try:
                        # Intentar varios formatos de fecha
                        from datetime import datetime
                        formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
                        date_value = None
                        for fmt in formats:
                            try:
                                date_value = datetime.strptime(value.strip(), fmt).date()
                                break
                            except ValueError:
                                continue
                        
                        if date_value:
                            cleaned_data[field_name] = date_value
                            print(f"Converted '{field_name}' to date: {cleaned_data[field_name]}")
                        else:
                            print(f"Could not parse date format for '{field_name}'")
                    except Exception as e:
                        print(f"Error converting '{field_name}' to date: {str(e)}")
                else:
                    # Para campos de texto y otros tipos
                    cleaned_data[field_name] = value.strip()
                    print(f"Set '{field_name}' as string: {cleaned_data[field_name]}")
            except Exception as e:
                print(f"Unexpected error processing field '{field_name}': {str(e)}")
                # Continuar con el siguiente campo en lugar de fallar
                continue
        
        print(f"Final cleaned data: {cleaned_data}")
        return cleaned_data

    def get_existing_object(self, row):
        """Obtiene objeto existente según el campo único"""
        if not self.unique_field or not row.get(self.unique_field):
            return None
            
        filters = {self.unique_field: row[self.unique_field]}
        try:
            return self.model.objects.get(**filters)
        except self.model.DoesNotExist:
            return None
        except self.model.MultipleObjectsReturned:
            raise Exception(f'Múltiples registros encontrados con {self.unique_field}={row[self.unique_field]}')

    def get_model_fields(self):
        """Obtiene los campos del modelo excluyendo los campos en exclude_fields"""
        return [
            f.name for f in self.model._meta.get_fields()
            if not f.is_relation or f.many_to_one  # Solo incluir campos regulares y ForeignKeys
            if f.name not in self.exclude_fields
        ]

    def get_required_fields(self):
        """Obtiene los campos obligatorios del modelo"""
        return [
            f.name for f in self.model._meta.get_fields()
            if not f.is_relation  # Solo campos regulares, no relaciones
            if not f.null and not f.blank and f.name not in self.exclude_fields
            if not f.has_default() and not f.auto_created  # Excluir campos con valor predeterminado
        ]

    def get_field_types(self):
        """Devuelve un diccionario con los tipos de cada campo"""
        field_types = {}
        for field in self.model._meta.get_fields():
            if field.name in self.exclude_fields:
                continue
                
            if not field.is_relation or field.many_to_one:
                if isinstance(field, models.ForeignKey):
                    field_types[field.name] = 'foreignkey'
                elif isinstance(field, models.IntegerField):
                    field_types[field.name] = 'integer'
                elif isinstance(field, models.DecimalField):
                    field_types[field.name] = 'decimal'
                elif isinstance(field, models.BooleanField):
                    field_types[field.name] = 'boolean'
                elif isinstance(field, models.DateField):
                    field_types[field.name] = 'date'
                elif isinstance(field, models.DateTimeField):
                    field_types[field.name] = 'datetime'
                else:
                    field_types[field.name] = 'string'
                    
        return field_types

    def download_template(self):
        """Genera y descarga una plantilla CSV para el modelo actual"""
        fields = self.get_model_fields()
        required_fields = self.get_required_fields()
        
        # Crear archivo CSV
        output = StringIO()
        writer = csv.writer(
            output,
            delimiter=self.csv_delimiter,
            quotechar=self.csv_quotechar,
            quoting=csv.QUOTE_ALL  # Poner comillas en todos los campos
        )
        
        # Escribir encabezados
        writer.writerow(fields)
        
        # Escribir fila de ejemplo
        example_row = []
        for field in fields:
            if field in required_fields:
                example_row.append(f'REQUERIDO - Ejemplo {field}')
            else:
                example_row.append(f'Ejemplo {field}')
        writer.writerow(example_row)
        
        # Preparar respuesta
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self.model._meta.model_name}_template.csv"'
        
        return response

    def render_response(self, request, context=None):
        """Renderiza la respuesta, manejando peticiones AJAX y normales"""
        if context is None:
            context = {}
            
        # Añadir datos comunes al contexto
        context.update({
            'title': f'Importar {self.model._meta.verbose_name_plural}',
            'entity': self.model._meta.verbose_name,
            'list_url': self.success_url,
            'action': 'import',
            'model_fields': self.get_model_fields(),
            'required_fields': self.get_required_fields(),
            'field_types': self.get_field_types(),
        })
        
        # Si es petición AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if 'form' in context and context['form'].errors:
                errors = {}
                for field, error_list in context['form'].errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({
                    'success': False,
                    'errors': errors
                }, status=400)
            else:
                return JsonResponse({
                    'success': True,
                    'html': render(request, self.template_name, context).content.decode('utf-8')
                })
        
        return render(request, self.template_name, context)
    
    