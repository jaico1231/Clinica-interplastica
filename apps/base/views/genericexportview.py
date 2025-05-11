import csv
import json
from datetime import datetime
from io import BytesIO, StringIO

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext as _
from django.views.generic import View

# Add reportlab for PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph


class GenericExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista genérica para exportar datos de un modelo a diferentes formatos (CSV, PDF)
    
    Configuración:
    - model: Modelo Django a exportar
    - permission_required: Permiso requerido (por defecto 'view_modelname')
    - fields_to_export: Lista de campos a exportar (si es None, se exportan todos)
    - exclude_fields: Lista de campos a excluir de la exportación
    - queryset: Para sobreescribir el queryset por defecto
    - filename_prefix: Prefijo para el nombre del archivo (por defecto es el nombre del modelo)
    """
    model = None  # Debe ser definido en la clase hija
    permission_required = 'view_model'  # Debe ser definido en la clase hija o se auto-configurará
    fields_to_export = None  # Si es None, se exportan todos los campos
    exclude_fields = ['id', 'created_at', 'updated_at', 'image']  # Campos a excluir de la exportación
    queryset = None  # Para sobreescribir el queryset por defecto
    filename_prefix = None  # Prefijo para el nombre del archivo
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if self.model:
            self.model_name = self.model._meta.model_name
            self.app_name = self.model._meta.app_label
            
            # Configurar permiso automáticamente si no se ha definido específicamente
            if self.permission_required == 'view_model':
                self.permission_required = f'{self.app_name}.view_{self.model_name}'
            
            # Configurar el prefijo del nombre de archivo si no se ha definido
            if self.filename_prefix is None:
                self.filename_prefix = self.model_name
    
    def get(self, request, *args, **kwargs):
        # Determinar el formato de exportación
        export_format = request.GET.get('format', 'csv').lower()
        
        # Validar el formato
        if export_format not in ['csv', 'pdf', 'excel']:
            return JsonResponse({'error': _('Formato no soportado')}, status=400)
        
        # Obtener los datos
        data = self.get_data()
        
        # Ejecutar la exportación según el formato solicitado
        if export_format == 'csv':
            return self.export_csv(data)
        elif export_format == 'pdf':
            return self.export_pdf(data)
        elif export_format == 'excel':
            return self.export_excel(data)
    
    def get_fields(self):
        """Obtener la lista de campos a exportar"""
        if self.fields_to_export is not None:
            return self.fields_to_export
        
        # Si no se especifican campos, obtener todos excepto los excluidos
        fields = []
        for field in self.model._meta.get_fields():
            if field.name not in self.exclude_fields:
                # Solo incluir campos regulares y relaciones ForeignKey
                if not field.is_relation or field.many_to_one:
                    fields.append(field.name)
        
        return fields
    
    def get_headers(self, fields=None):
        """Obtener los nombres para mostrar de los campos"""
        if fields is None:
            fields = self.get_fields()
        
        headers = []
        for field_name in fields:
            try:
                # Intentar obtener el verbose_name del campo
                field = self.model._meta.get_field(field_name)
                headers.append(str(field.verbose_name).capitalize())
            except:
                # Si no se puede, usar el nombre del campo
                headers.append(field_name.replace('_', ' ').capitalize())
        
        return headers
    
    def get_queryset(self):
        """Obtener el queryset de registros a exportar"""
        if self.queryset is not None:
            return self.queryset
        
        # Si no se ha definido un queryset específico, usar el predeterminado del modelo
        return self.model.objects.all()
    
    def get_data(self):
        """Obtener los datos a exportar"""
        queryset = self.get_queryset()
        fields = self.get_fields()
        
        data = []
        for obj in queryset:
            row = {}
            for field in fields:
                # Gestionar campos con puntos (relaciones)
                if '.' in field:
                    parts = field.split('.')
                    value = obj
                    for part in parts:
                        if value is None:
                            break
                        value = getattr(value, part, None)
                else:
                    value = getattr(obj, field, None)
                
                # Si el valor es una función, llamarla
                if callable(value):
                    value = value()
                
                row[field] = value
            
            data.append(row)
        
        return data
    
    def export_csv(self, data):
        """Exportar datos en formato CSV"""
        fields = self.get_fields()
        headers = self.get_headers(fields)
        
        # Crear archivo CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow(headers)
        
        # Escribir datos
        for row in data:
            writer.writerow([str(row.get(field, '')) for field in fields])
        
        # Crear respuesta HTTP
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.filename_prefix}_export_{timestamp}.csv"
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def export_pdf(self, data):
        """Exportar datos en formato PDF"""
        fields = self.get_fields()
        headers = self.get_headers(fields)
        
        # Crear archivo PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        
        # Estilos para el PDF
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        
        # Título del documento
        model_name = self.model._meta.verbose_name_plural.capitalize()
        title = Paragraph(f"Exportación de {model_name}", title_style)
        elements.append(title)
        
        # Preparar datos para la tabla
        table_data = [headers]  # Primera fila con encabezados
        
        for row in data:
            table_data.append([str(row.get(field, '')) for field in fields])
        
        # Crear tabla
        table = Table(table_data)
        
        # Estilo de la tabla
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        # Alternar colores para filas
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
        
        table.setStyle(style)
        elements.append(table)
        
        # Construir el PDF
        doc.build(elements)
        
        # Crear respuesta HTTP
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.filename_prefix}_export_{timestamp}.pdf"
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Cerrar el buffer
        buffer.close()
        
        return response
    
    def export_excel(self, data):
        """Exportar datos en formato Excel (XLSX)"""
        try:
            import xlsxwriter
        except ImportError:
            return JsonResponse({'error': _('Se requiere xlsxwriter para exportar a Excel')}, status=400)
        
        fields = self.get_fields()
        headers = self.get_headers(fields)
        
        # Crear archivo Excel en memoria
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # Estilos
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        })
        
        alt_format = workbook.add_format({
            'border': 1,
            'bg_color': '#E6F1F5',
            'align': 'left',
            'valign': 'vcenter'
        })
        
        # Escribir encabezados
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Escribir datos
        for row_num, row in enumerate(data, start=1):
            # Alternar formatos para filas
            row_format = cell_format if row_num % 2 == 0 else alt_format
            for col, field in enumerate(fields):
                value = row.get(field, '')
                # Convertir cualquier valor no string a string para evitar problemas
                if value is None:
                    value = ''
                if not isinstance(value, str):
                    try:
                        value = str(value)
                    except:
                        value = ''
                worksheet.write(row_num, col, value, row_format)
        
        # Ajustar anchos de columna
        for col, _ in enumerate(headers):
            worksheet.set_column(col, col, 15)  # Ancho de 15 para todas las columnas
        
        # Cerrar el libro
        workbook.close()
        
        # Crear respuesta HTTP
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.filename_prefix}_export_{timestamp}.xlsx"
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Cerrar el buffer
        output.close()
        
        return response