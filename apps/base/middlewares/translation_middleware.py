# translation_middleware.py
from django.utils.translation import gettext as _
from django.conf import settings
from django.http import HttpResponse
import re
from bs4 import BeautifulSoup
from libretranslatepy import LibreTranslateAPI
import html

class AutoTranslationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.translation_cache = {}  # Cache para evitar traducir textos repetidos
        
        # Configura la instancia de LibreTranslate
        # Puedes usar una instancia pública o tu propia instancia
        libre_translate_url = getattr(settings, 'LIBRE_TRANSLATE_URL', 'https://translate.argosopentech.com')
        libre_translate_api_key = getattr(settings, 'LIBRE_TRANSLATE_API_KEY', None)
        
        self.translator = LibreTranslateAPI(libre_translate_url, api_key=libre_translate_api_key)
        
        # Obtener los idiomas soportados
        try:
            self.supported_languages = {lang['code']: lang['name'] for lang in self.translator.languages()}
        except Exception as e:
            if settings.DEBUG:
                print(f"Error al obtener idiomas soportados: {str(e)}")
            self.supported_languages = {}
        
        # Patrones de texto que no deben ser traducidos
        self.non_translatable_patterns = [
            r'{% [^%]+ %}',  # Etiquetas de template Django
            r'{{ [^}]+ }}',   # Variables de template Django
            r'<[^>]*>',       # Etiquetas HTML
        ]
    
    def __call__(self, request):
        # Guarda el idioma solicitado
        target_language = request.LANGUAGE_CODE
        
        # Procesa la respuesta
        response = self.get_response(request)
        
        # Solo traduce respuestas HTML y si el idioma es soportado y no es el predeterminado
        if ('text/html' in response.get('Content-Type', '') and 
            target_language in self.supported_languages and
            target_language != settings.LANGUAGE_CODE and
            not getattr(response, 'is_translated', False)):
            
            try:
                # Solo para respuestas HttpResponse que contienen contenido
                if isinstance(response, HttpResponse) and hasattr(response, 'content'):
                    # Traduce el contenido HTML
                    content = response.content.decode(response.charset)
                    translated_content = self._translate_html(content, target_language)
                    
                    # Reemplaza el contenido
                    response.content = translated_content.encode(response.charset)
                    
                    # Marca la respuesta como traducida
                    response.is_translated = True
            except Exception as e:
                # Registra el error pero permite que la aplicación continúe
                if settings.DEBUG:
                    print(f"Error de traducción: {str(e)}")
        
        return response
    
    def _translate_html(self, html_content, target_language):
        """Traduce el contenido HTML preservando las etiquetas y estructuras"""
        
        # Utiliza BeautifulSoup para analizar el HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Encuentra todos los nodos de texto
        text_nodes = self._extract_text_nodes(soup)
        
        # Prepara textos para traducción en lote
        texts_to_translate = []
        node_map = {}
        
        for i, node in enumerate(text_nodes):
            text = node.string.strip()
            
            # Solo traduce textos no vacíos y que no coincidan con patrones especiales
            if text and not self._is_non_translatable(text):
                texts_to_translate.append(text)
                node_map[i] = len(texts_to_translate) - 1
        
        # Realiza la traducción en lotes para eficiencia
        if texts_to_translate:
            translated_texts = self._batch_translate(texts_to_translate, target_language)
            
            # Reemplaza los nodos con sus traducciones
            for i, node in enumerate(text_nodes):
                if i in node_map:
                    translation_index = node_map[i]
                    node.string.replace_with(translated_texts[translation_index])
        
        return str(soup)
    
    def _extract_text_nodes(self, soup):
        """Extrae todos los nodos de texto del HTML"""
        text_nodes = []
        
        # Función recursiva para encontrar nodos de texto
        def extract_from_node(node):
            if node.string and node.string.strip():
                text_nodes.append(node)
            for child in node.children:
                if child.name:  # Si tiene nombre es un elemento HTML
                    # Ignorar scripts y estilos
                    if child.name not in ['script', 'style']:
                        extract_from_node(child)
        
        extract_from_node(soup)
        return text_nodes
    
    def _is_non_translatable(self, text):
        """Verifica si el texto no debe ser traducido"""
        for pattern in self.non_translatable_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _batch_translate(self, texts, target_language):
        """Traduce una lista de textos usando LibreTranslate"""
        
        # Verifica primero el caché
        cached_texts = []
        need_translation_indices = []
        texts_to_translate = []
        
        for i, text in enumerate(texts):
            cache_key = f"{text}_{target_language}"
            
            if cache_key in self.translation_cache:
                cached_texts.append((i, self.translation_cache[cache_key]))
            else:
                need_translation_indices.append(i)
                texts_to_translate.append(text)
        
        # Si hay textos que necesitan traducción
        translated_texts = texts.copy()  # Copia los textos originales
        
        # Aplica los textos ya en caché
        for i, translated in cached_texts:
            translated_texts[i] = translated
        
        # Traduce los textos restantes
        if texts_to_translate:
            # LibreTranslate solo permite traducir un texto a la vez,
            # así que traducimos cada texto individualmente
            for i, text in enumerate(texts_to_translate):
                try:
                    original_index = need_translation_indices[i]
                    
                    # Realiza la traducción
                    result = self.translator.translate(
                        text,
                        settings.LANGUAGE_CODE,
                        target_language
                    )
                    
                    translated_text = result
                    translated_texts[original_index] = translated_text
                    
                    # Actualiza el caché
                    cache_key = f"{texts[original_index]}_{target_language}"
                    self.translation_cache[cache_key] = translated_text
                
                except Exception as e:
                    # En caso de error, usa el texto original
                    if settings.DEBUG:
                        print(f"Error al traducir texto '{text}': {str(e)}")
        
        return translated_texts