/**
 * sidebar.js - Script optimizado para el control del sidebar
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
    setupThemeChangeDetection();
});

function initializeSidebar() {
    // Esta función inicializa todos los componentes del sidebar. Llama a varias subfunciones:

    //     Crea el botón de alternar el sidebar
    //     Configura el estado inicial del sidebar
    //     Configura los listeners de eventos
    //     Marca la página actual en el menú
    //     Expande el menú activo automáticamente


    // Inicializar componentes
    createToggleButton();
    setupSidebarState();
    setupEventListeners();
    
    // Funcionalidades de menú
    markCurrentPage();
    expandActiveMenu();
}

// Crea dinámicamente un botón para mostrar/ocultar el sidebar si no existe. 
// El botón incluye un ícono de chevron (flecha) de Material Symbols.
function createToggleButton() {
    const sidebar = document.querySelector('.sidebar');
    if (!document.querySelector('.sidebar-toggle') && sidebar) {
        const toggleButton = document.createElement('div');
        toggleButton.className = 'sidebar-toggle';
        toggleButton.innerHTML = `
            <i class="material-symbols-outlined">
                chevron_left
            </i>
        `;
        sidebar.appendChild(toggleButton);
    }
}

// Restaura el estado del sidebar desde el almacenamiento local (localStorage). 
// Si el sidebar estaba minimizado en la sesión anterior, aplica esa configuración. 
// También adapta automáticamente el sidebar para dispositivos móviles.
function setupSidebarState() {
    const body = document.body;
    const toggleButton = document.querySelector('.sidebar-toggle');
    
    // Restaurar estado de minimizado desde localStorage
    if (localStorage.getItem('sidebar-minimize') === 'true' || 
        localStorage.getItem('sidebarState') === 'collapsed') {
        body.classList.add('sidebar-minimize');
        
        if (toggleButton) {
            const icon = toggleButton.querySelector('i');
            if (icon) icon.textContent = 'chevron_right';
        }
        console.log('Sidebar restaurado a estado minimizado (solo iconos)');
    }

    // Adaptar para móviles automáticamente
    handleWindowResize();
}

// Configura todos los manejadores de eventos relacionados con el sidebar:
// Eventos para el botón principal de alternar el sidebar
// Eventos para botones alternativos que también controlan el sidebar
// Manejadores para menús desplegables (colapsables)
// Eventos para cerrar el sidebar en dispositivos móviles
// Eventos para cambios de tamaño de ventana
// Detección de cambios de tema
function setupEventListeners() {
    const body = document.body;

    // Toggle colapso sidebar mediante botón principal
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebarCollapse();
        });
    }
    
    // Toggle con botón sidenav-toggler
    const sidenavTogglerBtn = document.querySelector('.sidenav-toggler');
    if (sidenavTogglerBtn) {
        sidenavTogglerBtn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebarCollapse();
        });
    }
    
    // Toggle con el botón topbar-toggler
    const topbarTogglerBtn = document.querySelector('.topbar-toggler.more');
    if (topbarTogglerBtn) {
        topbarTogglerBtn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebarCollapse();
        });
    }
    
    // Toggle menús anidados
    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(toggle => {
        toggle.addEventListener('click', handleMenuToggle);
    });
    
    // Cerrar sidebar en móvil al hacer clic fuera
    const mobileOverlay = document.querySelector('.mobile-overlay');
    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', function() {
            body.classList.remove('show-mobile-sidebar');
        });
    }
    
    // Botón móvil para mostrar sidebar
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            body.classList.toggle('show-mobile-sidebar');
        });
    }
    
    // Manejar resize para adaptarse a diferentes tamaños
    window.addEventListener('resize', handleWindowResize);
    
    // Escuchar cambios de tema
    const themeToggleButtons = document.querySelectorAll('.theme-toggle, .toggle-theme, [data-toggle="theme"]');
    themeToggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Actualizar logo basado en el tema
            setTimeout(updateLogoBasedOnTheme, 50);
        });
    });
}

// Alterna el estado del sidebar entre expandido y minimizado. 
// Cambia la clase CSS, actualiza el ícono del botón y guarda el estado en localStorage.
function toggleSidebarCollapse() {
    const body = document.body;
    const toggleButton = document.querySelector('.sidebar-toggle i');
    
    // Toggle sidebar-minimize
    body.classList.toggle('sidebar-minimize');
    const isCollapsed = body.classList.contains('sidebar-minimize');
    
    // Actualizar icono y estado
    if (toggleButton) {
        toggleButton.textContent = isCollapsed ? 'chevron_right' : 'chevron_left';
    }
    
    // Guardar estado
    localStorage.setItem('sidebar-minimize', isCollapsed ? 'true' : 'false');
    localStorage.setItem('sidebarState', isCollapsed ? 'collapsed' : 'expanded');
    
    console.log('Sidebar minimizado:', isCollapsed);
}

// Maneja la apertura y cierre de submenús dentro del sidebar, alternando la clase "show" y actualizando el atributo "aria-expanded".
function handleMenuToggle(e) {
    const body = document.body;
    
    // Prevenir comportamiento default solo si es necesario
    const target = document.querySelector(this.getAttribute('href'));
    if (!target) {
        e.preventDefault();
        return;
    }
    
    // Toggle del submenú 
    // No expandimos automáticamente al hacer clic en submenús
    target.classList.toggle('show');
    this.setAttribute('aria-expanded', target.classList.contains('show'));
}

// Identifica y marca el enlace correspondiente a la página actual en el sidebar, añadiendo la clase "active" y el atributo "aria-current".
function markCurrentPage() {
    const currentPath = window.location.pathname;
    
    document.querySelectorAll('.sidebar-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && (href === currentPath || currentPath.startsWith(href))) {
            link.classList.add('active');
            link.closest('li')?.classList.add('active');
            
            // Marca como actual usando atributo aria
            link.setAttribute('aria-current', 'page');
        }
    });
}

// Expande automáticamente cualquier menú colapsable que contenga el elemento activo (correspondiente a la página actual).
function expandActiveMenu() {
    document.querySelectorAll('.sidebar-item.active, li.active').forEach(item => {
        const parentMenu = item.closest('.collapse');
        if (parentMenu) {
            parentMenu.classList.add('show');
            const toggleButton = document.querySelector(`[href="#${parentMenu.id}"]`);
            if (toggleButton) {
                toggleButton.setAttribute('aria-expanded', 'true');
                toggleButton.classList.remove('collapsed');
            }
        }
    });
}

// Maneja el comportamiento del sidebar cuando cambia el tamaño de la ventana, adaptándolo para pantallas móviles o de escritorio.
function handleWindowResize() {
    const body = document.body;
    const mobileOverlay = document.querySelector('.mobile-overlay');
    
    if (window.innerWidth < 992) {
        // En móvil - gestionamos solo el overlay
        if (mobileOverlay) {
            mobileOverlay.style.display = 
                body.classList.contains('show-mobile-sidebar') ? 'block' : 'none';
        }
    } else {
        // En escritorio
        body.classList.remove('show-mobile-sidebar');
        
        // Ocultar overlay siempre en escritorio
        if (mobileOverlay) {
            mobileOverlay.style.display = 'none';
        }
    }
}

/**
 * Updates logo visibility based on current theme
 * Actualiza la visibilidad de los logos dependiendo del tema actual (claro u oscuro). 
 * Muestra el logo apropiado según el tema detectado.
 */
function updateLogoBasedOnTheme() {
    // Check if dark theme is active
    const isDarkTheme = document.body.classList.contains('dark-theme') || 
                        document.body.classList.contains('dark-mode') || 
                        document.documentElement.getAttribute('data-theme') === 'dark';
    
    // Get both logo elements
    const logoLight = document.querySelector('.logo-light');
    const logoDark = document.querySelector('.logo-dark');
    
    if (logoLight && logoDark) {
        // Show appropriate logo based on theme
        if (isDarkTheme) {
            logoLight.style.display = 'block';
            logoDark.style.display = 'none';
            console.log('Dark theme detected: Showing light logo');
        } else {
            logoLight.style.display = 'none';
            logoDark.style.display = 'block';
            console.log('Light theme detected: Showing dark logo');
        }
    }
}

// Configura observadores de mutación para detectar cambios en el tema de la aplicación (tanto en el elemento body como en el elemento html) y actualiza el logo correspondiente.
// Function to detect theme changes
function setupThemeChangeDetection() {
    // Run once on initial load
    updateLogoBasedOnTheme();
    
    // Watch for class changes on body - for frameworks that modify body classes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'class' || mutation.attributeName === 'data-theme') {
                updateLogoBasedOnTheme();
            }
        });
    });
    
    observer.observe(document.body, { attributes: true });
    
    // Also observe HTML for data-theme attribute changes
    const htmlObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'data-theme') {
                updateLogoBasedOnTheme();
            }
        });
    });
    
    htmlObserver.observe(document.documentElement, { attributes: true });
}