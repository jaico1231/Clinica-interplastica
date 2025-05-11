/**
 * header.js - Script optimizado para el control del header
 * Coordina la interacción entre el header y el sidebar
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeHeader();
});

/**
 * Inicializa todas las funcionalidades del header
 */
function initializeHeader() {
    // Referencias a elementos DOM
    const header = document.querySelector('.main-header');
    const container = document.querySelector('.main-panel .container');
    
    // Inicializar funcionalidades
    setupHeaderHeight();
    setupScrollEffects();
    setupSidebarIntegration();
    setupMobileMenu();
    // setupDropdowns();
    setupDropdownAutoClose();
    // Nota: No inicializamos el theme switcher aquí, ahora se maneja en theme-switcher.js
    setupLanguageSwitcher();
}

/**
 * Configura la altura del header y ajusta el padding del contenedor
 */
function setupHeaderHeight() {
    const header = document.querySelector('.main-header');
    const container = document.querySelector('.main-panel .container');
    
    // Función para ajustar la altura del padding-top del contenedor
    function adjustContainerPadding() {
        if (header && container) {
            const headerHeight = header.offsetHeight;
            container.style.paddingTop = (headerHeight + 20) + 'px'; // 20px extra para espacio
            console.log('Header height adjusted:', headerHeight + 'px');
        }
    }
    
    // Ajustar padding inicial
    adjustContainerPadding();
    
    // Ajustar cuando cambie el tamaño de la ventana
    window.addEventListener('resize', function() {
        setTimeout(adjustContainerPadding, 100); // Pequeño retraso para asegurar que los cambios de DOM se completen
    });
    
    // Exponer la función para uso por otras funciones
    window.headerAdjustPadding = adjustContainerPadding;
}

/**
 * Configura efectos de scroll del header
 */
function setupScrollEffects() {
    const header = document.querySelector('.main-header');
    
    if (header) {
        // Añadir clase al hacer scroll
        window.addEventListener('scroll', function() {
            if (window.scrollY > 10) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
        
        // Verificar scroll inicial
        if (window.scrollY > 10) {
            header.classList.add('scrolled');
        }
    }
}

/**
 * Integra el comportamiento del header con el sidebar
 */
function setupSidebarIntegration() {
    // Botón de toggle del sidebar principal
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            // El cambio de clase lo maneja sidebar.js
            // Solo necesitamos ajustar el padding después del cambio
            setTimeout(window.headerAdjustPadding, 300); // Esperar a que termine la transición
        });
    }
    
    // Otros botones que afectan al sidebar
    const sidenavTogglerBtn = document.querySelector('.sidenav-toggler');
    if (sidenavTogglerBtn) {
        sidenavTogglerBtn.addEventListener('click', function() {
            setTimeout(window.headerAdjustPadding, 300); // Actualizar después de la transición
        });
    }
    
    const topbarTogglerBtn = document.querySelector('.topbar-toggler.more');
    if (topbarTogglerBtn) {
        topbarTogglerBtn.addEventListener('click', function() {
            setTimeout(window.headerAdjustPadding, 300); // Actualizar después de la transición
        });
    }
}

/**
 * Configura el comportamiento para dispositivos móviles
 */
function setupMobileMenu() {
    const body = document.body;
    const mobileMenuToggle = document.querySelector('.navbar-toggler, .mobile-menu-toggle');
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            body.classList.toggle('show-mobile-sidebar');
            setTimeout(window.headerAdjustPadding, 300);
        });
    }
    
    // Cerrar menú móvil al hacer clic en overlay
    const mobileOverlay = document.querySelector('.mobile-overlay');
    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', function() {
            body.classList.remove('show-mobile-sidebar');
            setTimeout(window.headerAdjustPadding, 300);
        });
    }
}

/**
 * Configura el comportamiento de los dropdowns del header
 */
function setupDropdowns() {
    // Dropdowns del header
    const dropdownToggles = document.querySelectorAll('.main-header .dropdown-toggle');
    
    // Para cada toggle de dropdown
    dropdownToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Encontrar el menú asociado
            const target = this.nextElementSibling;
            if (target && target.classList.contains('dropdown-menu')) {
                // Toggle la clase show
                target.classList.toggle('show');
                
                // Actualizar aria-expanded
                this.setAttribute('aria-expanded', 
                    target.classList.contains('show') ? 'true' : 'false');
            }
        });
    });
    
    // Cerrar dropdowns al hacer clic fuera
    document.addEventListener('click', function(event) {
        // Si no es un toggle de dropdown y no está dentro de un dropdown
        if (!event.target.closest('.dropdown-toggle') && 
            !event.target.closest('.dropdown-menu')) {
            
            // Cerrar todos los dropdowns abiertos
            document.querySelectorAll('.main-header .dropdown-menu.show')
                .forEach(function(dropdown) {
                    dropdown.classList.remove('show');
                    
                    // Actualizar aria-expanded en el toggle
                    const toggle = dropdown.previousElementSibling;
                    if (toggle && toggle.classList.contains('dropdown-toggle')) {
                        toggle.setAttribute('aria-expanded', 'false');
                    }
                });
        }
    });
}

/**
 * Configura el selector de idioma
 */
function setupLanguageSwitcher() {
    const languageSelect = document.getElementById('language-select');
    
    if (languageSelect) {
        // Restaurar idioma guardado
        const savedLanguage = localStorage.getItem('language');
        if (savedLanguage) {
            languageSelect.value = savedLanguage;
        }
        
        // Listener para cambio de idioma
        languageSelect.addEventListener('change', function() {
            const selectedLanguage = this.value;
            localStorage.setItem('language', selectedLanguage);
            
            // Aquí podrías implementar un cambio real de idioma
            // Por ejemplo, redirigir a una URL con el idioma seleccionado
            console.log('Language changed to:', selectedLanguage);
        });
    }
}
// funcion para cerrar los dropdowns al hacer scroll
function setupDropdownAutoClose() {
    // Cerrar dropdowns al hacer scroll
    window.addEventListener('scroll', () => {
        document.querySelectorAll('.main-header .dropdown-menu.show').forEach(dropdown => {
            dropdown.classList.remove('show');
            const toggle = dropdown.previousElementSibling;
            if (toggle) toggle.setAttribute('aria-expanded', 'false');
        });
    });
}