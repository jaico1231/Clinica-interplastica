let isChatOpen = false;

// Inicialización al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
});

function initializeChat() {
    addQuickButtons();
    setupEventListeners();
    
    // Mostrar mensaje de bienvenida del servidor si existe
    const serverWelcome = document.querySelector('.welcome-message');
    if (serverWelcome) {
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        serverWelcome.querySelector('.message-time').textContent = timestamp;
        serverWelcome.style.display = 'block';
    }
}

// Funciones principales
function toggleChat() {
    const chatWidget = document.getElementById('chat-widget');
    isChatOpen = !isChatOpen;
    chatWidget.classList.toggle('active', isChatOpen);
    
    // Solo mostrar mensaje de bienvenida cuando se abre el chat por primera vez
    if (isChatOpen && !hasMessages()) {
        showWelcomeMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const typingIndicator = document.getElementById('typing-indicator');
    
    if (!input.value.trim()) return;
    
    addMessage(input.value, false);
    showTypingIndicator(typingIndicator);
    
    try {
        const response = await simulateApiCall(input.value);
        addMessage(response, true);
    } catch (error) {
        handleError();
    } finally {
        hideTypingIndicator(typingIndicator);
        input.value = '';
        input.focus();
    }
}

// Funciones de soporte
function addMessage(text, isBot) {
    const messagesContainer = document.getElementById('chat-messages');
    const formattedText = text.replace(/\n/g, '<br>');
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const messageHTML = `
        <div class="message-container">
            <div class="message-bubble ${isBot ? 'bot-message' : 'user-message'}">
                ${formattedText}
                <div class="message-time">${timestamp}</div>
            </div>
        </div>
    `;
    
    messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showWelcomeMessage() {
    const messagesContainer = document.getElementById('chat-messages');
    const existingWelcome = document.querySelector('.welcome-message');
    
    if (existingWelcome) {
        existingWelcome.style.display = 'block';
        return;
    }

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const welcomeMessage = `
        <div class="message-container welcome-message">
            <div class="message-bubble bot-message">
                ¡Hola! Soy tu asistente virtual. Estoy aquí para ayudarte con:<br><br>
                • Información de productos<br>
                • Soporte técnico<br>
                • Consultas generales<br><br>
                ¿En qué puedo asistirte hoy?
                <div class="message-time">${timestamp}</div>
            </div>
        </div>
    `;
    
    messagesContainer.insertAdjacentHTML('afterbegin', welcomeMessage);
}

// Funciones de UI
function addQuickButtons() {
    const questions = {
        'Horarios': '¿Cuáles son sus horarios de atención?',
        'Contacto': '¿Cómo puedo contactar con servicio al cliente?',
        'Promociones': '¿Tienen promociones actuales?'
    };

    const buttons = Object.entries(questions).map(([text, question]) => 
        `<button class="btn btn-sm btn-outline-primary me-1" 
                onclick="quickQuestion('${question}')">${text}</button>`
    ).join('');

    const container = document.querySelector('.quick-buttons-container');
    if (container) {
        container.innerHTML = `<div class="quick-buttons mt-2 mb-2">${buttons}</div>`;
    }
}

function quickQuestion(question) {
    const input = document.getElementById('chat-input');
    input.value = question;
    sendMessage();
}

// Helpers
function showTypingIndicator(indicator) {
    indicator.style.display = 'flex';
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator(indicator) {
    indicator.style.display = 'none';
}

function hasMessages() {
    return document.querySelectorAll('#chat-messages .message-container:not(.welcome-message)').length > 0;
}

function setupEventListeners() {
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

function handleError() {
    const errorMessage = 'Lo siento, hubo un error. Por favor intenta nuevamente.';
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const errorHTML = `
        <div class="message-container">
            <div class="message-bubble bot-message">
                ${errorMessage}
                <div class="message-time">${timestamp}</div>
            </div>
        </div>
    `;
    
    document.getElementById('chat-messages').insertAdjacentHTML('beforeend', errorHTML);
}

// Simulación de API
async function simulateApiCall(message) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const responses = {
        '¿Cuáles son sus horarios de atención?': 'Nuestro horario de atención es de Lunes a Viernes de 9:00 a 18:00 hrs.',
        '¿Cómo puedo contactar con servicio al cliente?': 'Puedes contactarnos al teléfono 800-123-4567 o por email a soporte@empresa.com',
        '¿Tienen promociones actuales?': 'Actualmente tenemos un 20% de descuento en productos seleccionados. ¿Deseas que te envíe más información?'
    };

    return responses[message] || 'Gracias por tu mensaje. Un agente te responderá en breve.';
}