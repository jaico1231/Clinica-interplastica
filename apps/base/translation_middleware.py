# translation_middleware.py
from django.utils.translation import gettext as _
from django.conf import settings
import requests

class AutoTranslationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.translation_cache = {}  # Para evitar traducir la misma cadena varias veces

    def __call__(self, request):
        # Procesa la solicitud antes de que llegue a la vista
        response = self.get_response(request)
        
        # Si la respuesta es HTML y el idioma no es el predeterminado
        if 'text/html' in response.get('Content-Type', '') and request.LANGUAGE_CODE != settings.LANGUAGE_CODE:
            self._translate_response(response, request.LANGUAGE_CODE)
        
        return response
    
    def _translate_response(self, response, target_language):
        # Aquí implementarías la lógica para traducir el contenido
        # Utilizando una API como Google Translate o DeepL
        pass

    def _translate_text(self, text, target_language):
        # Si ya está en caché, devuelve la traducción
        cache_key = f"{text}_{target_language}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
            
        # Aquí conectarías con tu API de traducción preferida
        # Ejemplo con un servicio ficticio:
        api_url = "https://translation-api.example.com/translate"
        params = {
            "text": text,
            "source": settings.LANGUAGE_CODE,
            "target": target_language
        }
        
        try:
            response = requests.post(api_url, json=params)
            translated = response.json().get("translated_text", text)
            # Guarda en caché para futuras solicitudes
            self.translation_cache[cache_key] = translated
            return translated
        except Exception as e:
            # En caso de error, devuelve el texto original
            return text