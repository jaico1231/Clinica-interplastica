import os
import hashlib
from datetime import datetime, timedelta
from io import BytesIO

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.http import HttpResponse, FileResponse
from django.utils.translation import gettext as _
from django.views.generic import View
from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image


class GenericPDFReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Vista genérica para generar reportes en PDF detallados para un modelo específico.
    Incluye soporte para caché de PDFs.

    Configuración:
    - model: Modelo Django para el reporte
    - permission_required: Permiso requerido (por defecto 'view_modelname')
    - template_name: Nombre de la plantilla para el PDF (opcional)
    - filename_prefix: Prefijo para el nombre del archivo (por defecto es el nombre del modelo)
    - page_size: Tamaño de página (por defecto letter)
    - logo_path: Ruta al logo para el encabezado (opcional)
    - cache_timeout: Tiempo en segundos que el PDF permanecerá en caché (por defecto 1 hora)
    - use_cache: Si se debe usar caché para los PDFs (por defecto True)
    - force_refresh: Parámetro URL para forzar la regeneración del PDF (por defecto 'refresh')
    """
    model = None  # Debe ser definido en la clase hija
    permission_required = 'view_model'  # Debe ser definido en la clase hija o se auto-configurará
    template_name = None  # Opcional, para usar una plantilla específica
    filename_prefix = None  # Prefijo para el nombre del archivo
    page_size = letter  # Tamaño de página por defecto
    logo_path = None  # Ruta al logo para el encabezado
    cache_timeout = 3600  # 1 hora por defecto
    use_cache = True  # Usar caché por defecto
    force_refresh = 'refresh'  # Parámetro URL para forzar la regeneración del PDF

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
        # Verificar si se debe forzar la regeneración del PDF
        force_refresh = request.GET.get(self.force_refresh, False)

        # Obtener el objeto específico si se proporciona un pk
        pk = kwargs.get('pk')
        if pk:
            obj = self.get_object(pk)
            if not obj:
                return HttpResponse(_('Objeto no encontrado'), status=404)

            # Generar o recuperar el PDF de la caché
            return self.get_pdf_response(obj, force_refresh)
        else:
            # Si no se proporciona pk, generar un reporte para todos los objetos
            queryset = self.get_queryset()

            # Generar o recuperar el PDF de la caché
            return self.get_pdf_list_response(queryset, force_refresh)

    def get_object(self, pk):
        """Obtener el objeto específico por pk"""
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def get_queryset(self):
        """Obtener el queryset de objetos"""
        return self.model.objects.all()

    def get_filename(self, obj=None):
        """Obtener el nombre del archivo para el PDF"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if obj:
            return f"{self.filename_prefix}_{obj.pk}_{timestamp}.pdf"
        return f"{self.filename_prefix}_list_{timestamp}.pdf"

    def get_title(self, obj=None):
        """Obtener el título para el reporte"""
        if obj:
            return f"{self.model._meta.verbose_name.capitalize()} #{obj.pk}"
        return f"Listado de {self.model._meta.verbose_name_plural.capitalize()}"

    def get_styles(self):
        """Obtener los estilos para el PDF"""
        styles = getSampleStyleSheet()

        # Modificar estilos existentes
        styles['Title'].fontSize = 16
        styles['Title'].alignment = 1  # Centrado
        styles['Title'].spaceAfter = 12

        styles['Heading2'].fontSize = 14
        styles['Heading2'].spaceAfter = 6

        styles['BodyText'].fontSize = 10
        styles['BodyText'].spaceAfter = 3

        # Agregar estilo 'Subtitle'
        styles.add(ParagraphStyle(
            name='Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=6
        ))

        # Agregar otros estilos personalizados
        if 'Bold' not in styles:
            styles.add(ParagraphStyle(
                name='Bold',
                parent=styles['BodyText'],
                fontSize=10,
                fontName='Helvetica-Bold'
            ))

        if 'Footer' not in styles:
            styles.add(ParagraphStyle(
                name='Footer',
                parent=styles['BodyText'],
                fontSize=8,
                textColor=colors.gray
            ))

        return styles

    def get_header_elements(self, styles, title):
        """Obtener los elementos del encabezado del PDF"""
        elements = []

        # Agregar logo si está definido
        if self.logo_path and os.path.exists(self.logo_path):
            img = Image(self.logo_path, width=1.5*inch, height=0.5*inch)
            elements.append(img)
            elements.append(Spacer(1, 12))

        # Agregar título
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Spacer(1, 12))

        # Agregar fecha
        date_text = f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        elements.append(Paragraph(date_text, styles['BodyText']))
        elements.append(Spacer(1, 12))

        return elements

    def get_footer_elements(self, styles):
        """Obtener los elementos del pie de página del PDF"""
        elements = []

        elements.append(Spacer(1, 12))
        footer_text = f"© {datetime.now().year} - {_('Generado por el sistema')}"
        elements.append(Paragraph(footer_text, styles['Footer']))

        return elements

    def generate_pdf_report(self, obj):
        """
        Generar un reporte PDF detallado para un objeto específico.
        Este método debe ser implementado por las clases hijas.
        """
        raise NotImplementedError("Las clases hijas deben implementar este método")

    def generate_pdf_list_report(self, queryset):
        """
        Generar un reporte PDF con una lista de objetos.
        Este método debe ser implementado por las clases hijas.
        """
        raise NotImplementedError("Las clases hijas deben implementar este método")

    def get_cache_key(self, obj=None):
        """
        Generar una clave única para la caché basada en el objeto o queryset.
        """
        if obj:
            # Clave para un objeto específico
            key = f"pdf_report_{self.model_name}_{obj.pk}"

            # Incluir la fecha de última modificación si está disponible
            if hasattr(obj, 'updated_at'):
                key += f"_{obj.updated_at.strftime('%Y%m%d%H%M%S')}"
            elif hasattr(obj, 'modified_at'):
                key += f"_{obj.modified_at.strftime('%Y%m%d%H%M%S')}"

            return key
        else:
            # Clave para un listado
            # Incluir un hash del queryset para diferenciar entre diferentes filtros
            queryset = self.get_queryset()
            queryset_str = str(queryset.query)
            queryset_hash = hashlib.md5(queryset_str.encode()).hexdigest()

            return f"pdf_list_report_{self.model_name}_{queryset_hash}"

    def get_pdf_response(self, obj, force_refresh=False):
        """
        Obtener la respuesta HTTP con el PDF, ya sea de la caché o generándolo.
        """
        if self.use_cache and not force_refresh:
            # Intentar obtener el PDF de la caché
            cache_key = self.get_cache_key(obj)
            cached_pdf = cache.get(cache_key)

            if cached_pdf:
                # Si el PDF está en caché, devolverlo
                filename = self.get_filename(obj)
                response = HttpResponse(cached_pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response

        # Si no está en caché o se fuerza la regeneración, generar el PDF
        response = self.generate_pdf_report(obj)

        # Guardar el PDF en caché si está habilitado
        if self.use_cache:
            cache_key = self.get_cache_key(obj)
            cache.set(cache_key, response.content, self.cache_timeout)

        return response

    def get_pdf_list_response(self, queryset, force_refresh=False):
        """
        Obtener la respuesta HTTP con el PDF de lista, ya sea de la caché o generándolo.
        """
        if self.use_cache and not force_refresh:
            # Intentar obtener el PDF de la caché
            cache_key = self.get_cache_key()
            cached_pdf = cache.get(cache_key)

            if cached_pdf:
                # Si el PDF está en caché, devolverlo
                filename = self.get_filename()
                response = HttpResponse(cached_pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response

        # Si no está en caché o se fuerza la regeneración, generar el PDF
        response = self.generate_pdf_list_report(queryset)

        # Guardar el PDF en caché si está habilitado
        if self.use_cache:
            cache_key = self.get_cache_key()
            cache.set(cache_key, response.content, self.cache_timeout)

        return response

    def create_pdf_response(self, elements, obj=None, inline=True):
        """
        Crear la respuesta HTTP con el PDF generado.

        Args:
            elements: Elementos del PDF a generar
            obj: Objeto relacionado con el PDF (opcional)
            inline: Si es True, el PDF se mostrará en el navegador; si es False, se descargará directamente
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.page_size)

        # Construir el PDF
        doc.build(elements)

        # Crear respuesta HTTP
        filename = self.get_filename(obj)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')

        # Configurar el encabezado Content-Disposition
        if inline:
            # Para mostrar en el navegador (inline)
            response['Content-Disposition'] = f'inline; filename="{filename}"'
        else:
            # Para descargar directamente (attachment)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Cerrar el buffer
        buffer.close()

        return response

    def create_table(self, data, colWidths=None, style=None):
        """Crear una tabla con estilo para el PDF"""
        table = Table(data, colWidths=colWidths)

        # Estilo por defecto si no se proporciona uno
        if style is None:
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ])

            # Alternar colores para filas
            for i in range(1, len(data)):
                if i % 2 == 0:
                    style.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)

        table.setStyle(style)
        return table