/**
 * theme-switcher.js - Controla el cambio de tema claro/oscuro
 * Este archivo maneja la funcionalidad para alternar entre temas claros y oscuros en la aplicación
 */

// Ejecuta la inicialización del cambiador de tema cuando el DOM está completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    // Llama a la función principal de inicialización
    initializeThemeSwitcher();
});

/**
 * Función principal que inicializa todas las características del cambiador de tema
 * Recupera preferencias guardadas, aplica el tema y configura los controles
 */
function initializeThemeSwitcher() {
    // Recupera la preferencia de tema guardada en localStorage
    const savedTheme = localStorage.getItem('theme');
    
    // Aplica el tema guardado o establece el tema por defecto (ahora dark por defecto)
    if (savedTheme === 'light') {
        // Si el tema guardado es 'light', añade la clase correspondiente al body
        document.body.classList.add('theme-light');
        document.body.classList.remove('dark-theme', 'dark-mode');
        document.documentElement.setAttribute('data-theme', 'light');
        // Actualiza la hoja de estilos para que use el tema claro
        updateThemeStylesheet('light');
    } else {
        // Si no hay tema guardado o es 'dark', configura el tema oscuro
        document.body.classList.remove('theme-light');
        document.body.classList.add('dark-theme', 'dark-mode');
        document.documentElement.setAttribute('data-theme', 'dark');
        // Actualiza la hoja de estilos para usar el tema oscuro
        updateThemeStylesheet('dark');
    }
    
    // Actualiza el estado de todos los controles de tema
    updateAllThemeControls();
    
    // Verifica si ya existe un botón para alternar el tema
    if (!document.querySelector('.theme-toggle:not(input)')) {
        // Si no existe, crea el botón de cambio de tema
        createThemeToggleButton();
    }
    
    // Configura el evento de todos los controles para cambiar el tema
    setupAllThemeToggleEvents();
}

/**
 * Actualiza el estado de todos los controles de tema basados en el tema actual
 */
function updateAllThemeControls() {
    // Determina si el tema actual es claro
    const isLightTheme = document.body.classList.contains('theme-light');
    
    // Actualiza el estado del checkbox de tema
    const themeCheckbox = document.getElementById('theme-toggle');
    if (themeCheckbox) {
        themeCheckbox.checked = !isLightTheme; // Checked para tema oscuro
    }
    
    // Actualiza todos los botones de tema
    const themeButtons = document.querySelectorAll('.theme-toggle:not(input)');
    themeButtons.forEach(button => {
        const icon = button.querySelector('.material-symbols-outlined');
        if (icon) {
            icon.textContent = isLightTheme ? 'dark_mode' : 'light_mode';
        }
    });
    
    // Maneja la visibilidad de los iconos separados de sol/luna
    updateThemeIcons(isLightTheme);
}

/**
 * Actualiza la visibilidad de los iconos de sol y luna según el tema actual
 * @param {boolean} isLightTheme - Indica si el tema actual es claro
 */
function updateThemeIcons(isLightTheme) {
    // Iconos de Material Symbols
    const sunIcon = document.querySelector('.theme-icon-light');
    const moonIcon = document.querySelector('.theme-icon-dark');
    
    if (sunIcon && moonIcon) {
        // En tema claro: mostrar luna
        // En tema oscuro: mostrar sol
        if (isLightTheme) {
            sunIcon.style.display = 'none';
            sunIcon.style.opacity = '0';
            moonIcon.style.display = 'inline-block';
            moonIcon.style.opacity = '1';
        } else {
            sunIcon.style.display = 'inline-block';
            sunIcon.style.opacity = '1';
            moonIcon.style.display = 'none';
            moonIcon.style.opacity = '0';
        }
    }
    
    // Iconos de Font Awesome (alternativa)
    const faSun = document.querySelector('.theme-switcher .fa-sun');
    const faMoon = document.querySelector('.theme-switcher .fa-moon');
    
    if (faSun && faMoon) {
        if (isLightTheme) {
            faSun.style.display = 'none';
            faSun.style.opacity = '0';
            faMoon.style.display = 'inline-block';
            faMoon.style.opacity = '1';
        } else {
            faSun.style.display = 'inline-block';
            faSun.style.opacity = '1';
            faMoon.style.display = 'none';
            faMoon.style.opacity = '0';
        }
    }
    
    // Añadir manejo para los iconos del slider
    const lightModeIcon = document.querySelector('.light-mode-icon');
    const darkModeIcon = document.querySelector('.dark-mode-icon');
    
    if (lightModeIcon && darkModeIcon) {
        if (isLightTheme) {
            // En tema claro: mostrar icono de luna (dark-mode-icon)
            lightModeIcon.style.display = 'none';
            lightModeIcon.style.opacity = '0';
            darkModeIcon.style.display = 'inline-block';
            darkModeIcon.style.opacity = '1';
        } else {
            // En tema oscuro: mostrar icono de sol (light-mode-icon)
            lightModeIcon.style.display = 'inline-block';
            lightModeIcon.style.opacity = '1';
            darkModeIcon.style.display = 'none';
            darkModeIcon.style.opacity = '0';
        }
    }
}

/**
 * Crea dinámicamente un botón para cambiar entre temas si no existe en el HTML
 * El botón incluye un ícono que se ajusta al tema actual
 */
function createThemeToggleButton() {
    // Crea un elemento button para el cambio de tema
    const themeButton = document.createElement('button');
    // Asigna la clase theme-toggle para su posterior referencia
    themeButton.className = 'theme-toggle';
    // Añade un atributo de accesibilidad para lectores de pantalla
    themeButton.setAttribute('aria-label', 'Cambiar tema');
    
    // Determina si el tema actual es claro verificando la clase en el body
    const isLightTheme = document.body.classList.contains('theme-light');
    // Crea el HTML interior con un ícono de Material Symbols apropiado para el tema actual
    themeButton.innerHTML = `
        <span class="material-symbols-outlined">
            ${isLightTheme ? 'dark_mode' : 'light_mode'}
        </span>
    `;
    
    // Añade el botón recién creado al final del body
    document.body.appendChild(themeButton);
}

/**
 * Configura eventos para todos los controles de cambio de tema
 */
function setupAllThemeToggleEvents() {
    // Configura evento para el botón creado por JavaScript
    setupThemeToggleEvent();
    
    // Configura evento para el checkbox en el header
    const themeCheckbox = document.getElementById('theme-toggle');
    if (themeCheckbox) {
        themeCheckbox.addEventListener('change', function() {
            // Cambiar tema basado en el estado del checkbox
            toggleTheme(this.checked ? 'dark' : 'light');
        });
    }
    
    // Configura eventos para botones adicionales
    const additionalButtons = document.querySelectorAll('.toggle-theme, [data-toggle="theme"]');
    additionalButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Determinar el tema actual y cambiar al opuesto
            const isLight = document.body.classList.contains('theme-light');
            toggleTheme(isLight ? 'dark' : 'light');
        });
    });
}

/**
 * Configura el evento click para el botón principal de cambio de tema
 */
function setupThemeToggleEvent() {
    // Obtiene referencia al botón de cambio de tema
    const themeButton = document.querySelector('.theme-toggle:not(input)');
    // Verifica que el botón exista antes de configurarlo
    if (themeButton) {
        // Añade un event listener para el evento click
        themeButton.addEventListener('click', function() {
            // Determinar el tema actual y cambiar al opuesto
            const isLight = document.body.classList.contains('theme-light');
            toggleTheme(isLight ? 'dark' : 'light');
        });
    }
}

/**
 * Función unificada para cambiar el tema
 * @param {string} theme - El tema a aplicar ('light' o 'dark')
 */
function toggleTheme(theme) {
    const body = document.body;
    const html = document.documentElement;
    
    // Gestionar clases en función del tema
    if (theme === 'light') {
        body.classList.add('theme-light');
        body.classList.remove('dark-theme', 'dark-mode');
        html.setAttribute('data-theme', 'light');
    } else {
        body.classList.remove('theme-light');
        body.classList.add('dark-theme', 'dark-mode');
        html.setAttribute('data-theme', 'dark');
    }
    
    // Actualizar todos los controles visuales
    updateAllThemeControls();
    
    // Actualizar hoja de estilos
    updateThemeStylesheet(theme);
    
    // Guardar preferencia
    localStorage.setItem('theme', theme);
    
    // Actualizar logos (función de sidebar.js)
    if (typeof updateLogoBasedOnTheme === 'function') {
        setTimeout(updateLogoBasedOnTheme, 50);
    }
    
    console.log('Tema cambiado a:', theme === 'light' ? 'claro' : 'oscuro');
}

/**
 * Actualiza la hoja de estilo del tema en el documento HTML
 * Busca el elemento link con ID 'theme-style' y modifica su href
 * @param {string} theme - El tema a aplicar ('light' o 'dark')
 */
function updateThemeStylesheet(theme) {
    // Busca el elemento link que contiene la hoja de estilo del tema
    const themeStyle = document.getElementById('theme-style');
    // Verifica que exista el elemento
    if (themeStyle) {
        // Obtiene la ruta actual de la hoja de estilo
        const currentPath = themeStyle.getAttribute('href');
        // Extrae la ruta base (directorio) manteniendo todo hasta la última barra
        const basePath = currentPath.substring(0, currentPath.lastIndexOf('/') + 1);
        
        // Actualiza el atributo href con la nueva hoja de estilo según el tema
        themeStyle.href = `${basePath}${theme === 'light' ? 'light' : 'dark'}-theme.css`;
    }
}

/**
 * Detecta la preferencia de esquema de color del sistema operativo
 * Aplica el tema correspondiente basado en esta preferencia
 */
function detectPreferredColorScheme() {
    // Verifica si el navegador soporta media queries y detecta preferencia de tema
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
        // Si el sistema prefiere tema claro, aplica ese tema
        toggleTheme('light');
    } else {
        // Si el sistema prefiere tema oscuro o no hay preferencia, usa tema oscuro
        toggleTheme('dark');
    }
}

// Esta línea está comentada por defecto
// Si se descomenta, la aplicación usará la preferencia de color del sistema del usuario
// detectPreferredColorScheme();