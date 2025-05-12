# Añadir este código en un nuevo archivo: apps/waste/widgets.py

from django.forms import FileInput

class MultipleFileInput(FileInput):
    """
    Widget para la carga de archivos múltiples.
    Este widget extiende FileInput de Django para permitir el atributo multiple.
    """
    allow_multiple_selected = True  # Esta es la clave que permite múltiples archivos
    
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['multiple'] = True  # Asegurarse de que el atributo multiple está establecido
        super().__init__(attrs)