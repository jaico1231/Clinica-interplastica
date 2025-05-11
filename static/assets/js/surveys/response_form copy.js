// Load question data from the Django template context
const questions = [
    {% for question in questions %}
        {
            id: "{{ question.id }}",
            text: "{{ question.text|escapejs }}",
            order: {{ question.order }},
            required: {% if question.is_required %}true{% else %}false{% endif %},
            type: "{{ question.question_type.name|lower }}",
            helpText: "{{ question.help_text|default:""|escapejs }}",
            {% if question.dependent_on %}
            dependentOn: "{{ question.dependent_on.id }}",
            dependentValue: "{{ question.dependent_value|escapejs }}",
            {% endif %}
            {% if question.min_value is not None %}minValue: {{ question.min_value }},{% endif %}
            {% if question.max_value is not None %}maxValue: {{ question.max_value }},{% endif %}
            options: [
                {% if question.question_type.name in 'SINGLE_CHOICE,MULTIPLE_CHOICE,RATING,YES_NO' %}
                    {% for choice in question.choices.all %}
                        {
                            id: "{{ choice.id }}",
                            text: "{{ choice.text|escapejs }}",
                            value: "{{ choice.value|escapejs }}"
                        }{% if not forloop.last %},{% endif %}
                    {% endfor %}
                {% endif %}
            ]
        }{% if not forloop.last %},{% endif %}
    {% endfor %}
];

// --- State Variables ---
let currentPage = 1;
let itemsPerPage = 5; // Default value from the select dropdown
const totalQuestions = questions.length;
let answeredQuestions = 0;
const storageKey = 'surveyResponses_{{ survey.id }}'; // Use survey ID to avoid conflicts
let formResponses = {};

// --- DOM Elements ---
const questionsContainer = document.getElementById('questions-container');
const questionsPerPageSelect = document.getElementById('questions-per-page');
const prevButton = document.getElementById('prev-btn');
const nextButton = document.getElementById('next-btn');
const pageInfoSpan = document.getElementById('page-info');
const surveyForm = document.getElementById('survey-form');
const totalQuestionsSpan = document.getElementById('total-questions');
const totalQuestionsSpan2 = document.getElementById('total-questions2');
const answeredQuestionsSpan = document.getElementById('answered-questions');
const currentPageSpan = document.getElementById('current-page-info');
const totalPagesSpan = document.getElementById('total-pages-info');
const cachedAnswersField = document.getElementById('cached-answers');
const saveStatusEl = document.getElementById('save-status');

// --- Functions for Answer Storage ---

// Load answers from localStorage
function loadAnswers() {
    const savedAnswers = localStorage.getItem(storageKey);
    if (savedAnswers) {
        try {
            return JSON.parse(savedAnswers);
        } catch (e) {
            console.error('Error parsing saved answers:', e);
            return {};
        }
    }
    return {};
}

// Save current form values to localStorage
function saveAnswers() {
    const currentAnswers = loadAnswers(); // Load existing answers
    // Guardar todas las respuestas actuales incluso si no están en la página actual
    const currentInputs = questionsContainer.querySelectorAll('input:not([type="hidden"]), textarea, select');
    
    // Procesar los inputs de la página actual
    currentInputs.forEach(input => {
        const questionId = input.name;
        if (!questionId) return; // Omitir elementos sin nombre
        
        if (input.type === 'checkbox') {
            // Inicializar array si no existe
            if (!formResponses[questionId] || !Array.isArray(formResponses[questionId])) {
                formResponses[questionId] = [];
            }
            
            // Añadir/quitar del array según selección
            if (input.checked) {
                if (!formResponses[questionId].includes(input.value)) {
                    formResponses[questionId].push(input.value);
                }
            } else {
                // Sólo quitar si está presente
                const index = formResponses[questionId].indexOf(input.value);
                if (index > -1) {
                    formResponses[questionId].splice(index, 1);
                }
            }
            
            // Limpiar arrays vacíos
            if (formResponses[questionId].length === 0) {
                delete formResponses[questionId];
            }
        } else if (input.type === 'radio') {
            // Solo guardar si está marcado
            if (input.checked) {
                formResponses[questionId] = input.value;
            }
        } else {
            // Para texto, textarea, fecha, número
            if (input.value.trim() !== '') {
                formResponses[questionId] = input.value;
            } else {
                delete formResponses[questionId];
            }
        }
    });
    
    // Guardar en localStorage
    try {
        const serializedResponses = JSON.stringify(formResponses);
        localStorage.setItem(storageKey, serializedResponses);
        
        // Actualizar campo oculto para envío del formulario
        if (cachedAnswersField) {
            cachedAnswersField.value = serializedResponses;
        }
        
        // Mostrar mensaje de guardado exitoso
        showSaveStatus('success', '{% trans "Responses saved" %}');
        
        console.log('Saved answers:', formResponses);
    } catch (error) {
        console.error('Error saving answers:', error);
        showSaveStatus('error', '{% trans "Error saving responses" %}');
    }
    
    // Actualizar contador de preguntas respondidas
    updateAnsweredQuestionsCount();
}

// Show save status message
function showSaveStatus(type, message) {
    if (!saveStatusEl) return;
    
    saveStatusEl.textContent = message;
    saveStatusEl.className = `save-status ${type} show`;
    
    // Hide after 2 seconds
    setTimeout(() => {
        saveStatusEl.classList.remove('show');
    }, 2000);
}

function renderQuestion(question) {
    const card = document.createElement('div');
    card.className = 'card question-card mb-3';
    card.dataset.questionId = question.id;
    
    // Handle conditional display based on dependent questions
    if (question.dependentOn) {
        card.dataset.dependentOn = question.dependentOn;
        card.dataset.dependentValue = question.dependentValue;
        card.style.display = 'none'; // Initially hidden
    }

    const cardHeader = document.createElement('div');
    cardHeader.className = 'card-header';
    
    const questionTitle = document.createElement('h5');
    questionTitle.innerHTML = `${question.order}. ${question.text}`;
    cardHeader.appendChild(questionTitle);
    
    if (question.helpText) {
        const helpText = document.createElement('small');
        helpText.className = 'text-muted d-block mt-1';
        helpText.textContent = question.helpText;
        cardHeader.appendChild(helpText);
    }
    
    if (question.required) {
        const requiredBadge = document.createElement('span');
        requiredBadge.className = 'badge bg-danger ms-2';
        requiredBadge.textContent = '{% trans "Required" %}';
        cardHeader.appendChild(requiredBadge);
    }

    card.appendChild(cardHeader);

    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';

    // Render appropriate input based on question type
    switch(question.type.toLowerCase()) {
        case 'text':
        case 'text_area':
            if (question.type.toLowerCase() === 'text') {
                const input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-control';
                input.name = question.id;
                input.id = `question_${question.id}`;
                input.required = question.required;
                input.placeholder = '{% trans "Short answer" %}';
                // Restore value if exists
                if (formResponses[question.id]) {
                    input.value = formResponses[question.id];
                }
                cardBody.appendChild(input);
            } else {
                const textarea = document.createElement('textarea');
                textarea.className = 'form-control';
                textarea.name = question.id;
                textarea.id = `question_${question.id}`;
                textarea.required = question.required;
                textarea.rows = 3;
                textarea.placeholder = '{% trans "Detailed answer" %}';
                // Restore value if exists
                if (formResponses[question.id]) {
                    textarea.value = formResponses[question.id];
                }
                cardBody.appendChild(textarea);
            }
            break;
            
        case 'single_choice':
            const singleChoiceContainer = document.createElement('div');
            singleChoiceContainer.className = 'options-container';
            
            question.options.forEach((option, index) => {
                const formCheck = document.createElement('div');
                formCheck.className = 'form-check';
                
                const radioInput = document.createElement('input');
                radioInput.className = 'form-check-input';
                radioInput.type = 'radio';
                radioInput.name = question.id;
                radioInput.id = `choice_${option.id}`;
                radioInput.value = option.value;
                radioInput.required = question.required;
                // Restore checked state if exists
                if (formResponses[question.id] && formResponses[question.id] === option.value) {
                    radioInput.checked = true;
                }
                
                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.htmlFor = `choice_${option.id}`;
                label.textContent = option.text;
                
                formCheck.appendChild(radioInput);
                formCheck.appendChild(label);
                singleChoiceContainer.appendChild(formCheck);
            });
            
            cardBody.appendChild(singleChoiceContainer);
            break;
            
        case 'multiple_choice':
            const multipleChoiceContainer = document.createElement('div');
            multipleChoiceContainer.className = 'options-container';
            
            question.options.forEach((option, index) => {
                const formCheck = document.createElement('div');
                formCheck.className = 'form-check';
                
                const checkboxInput = document.createElement('input');
                checkboxInput.className = 'form-check-input';
                checkboxInput.type = 'checkbox';
                checkboxInput.name = `${question.id}`;
                checkboxInput.id = `choice_${option.id}`;
                checkboxInput.value = option.value;
                // Restore checked state if exists
                if (formResponses[question.id] && 
                    Array.isArray(formResponses[question.id]) && 
                    formResponses[question.id].includes(option.value)) {
                    checkboxInput.checked = true;
                }
                
                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.htmlFor = `choice_${option.id}`;
                label.textContent = option.text;
                
                formCheck.appendChild(checkboxInput);
                formCheck.appendChild(label);
                multipleChoiceContainer.appendChild(formCheck);
            });
            
            // Add hidden field for required validation
            if (question.required) {
                const hiddenValidator = document.createElement('input');
                hiddenValidator.type = 'hidden';
                hiddenValidator.className = 'multiple-choice-validator';
                hiddenValidator.dataset.name = question.id;
                hiddenValidator.required = true;
                multipleChoiceContainer.appendChild(hiddenValidator);
            }
            
            cardBody.appendChild(multipleChoiceContainer);
            break;
            
        case 'rating':
            const ratingContainer = document.createElement('div');
            ratingContainer.className = 'rating-container d-flex flex-wrap';
            
            question.options.forEach((option, index) => {
                const formCheck = document.createElement('div');
                formCheck.className = 'form-check form-check-inline me-3';
                
                const radioInput = document.createElement('input');
                radioInput.className = 'form-check-input';
                radioInput.type = 'radio';
                radioInput.name = question.id;
                radioInput.id = `rating_${option.id}`;
                radioInput.value = option.value;
                radioInput.required = question.required;
                // Restore checked state if exists
                if (formResponses[question.id] && formResponses[question.id] === option.value) {
                    radioInput.checked = true;
                }
                
                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.htmlFor = `rating_${option.id}`;
                label.textContent = option.text;
                
                formCheck.appendChild(radioInput);
                formCheck.appendChild(label);
                ratingContainer.appendChild(formCheck);
            });
            
            cardBody.appendChild(ratingContainer);
            break;
            
        case 'date':
            const dateInput = document.createElement('input');
            dateInput.type = 'date';
            dateInput.className = 'form-control';
            dateInput.name = question.id;
            dateInput.id = `question_${question.id}`;
            dateInput.required = question.required;
            // Restore value if exists
            if (formResponses[question.id]) {
                dateInput.value = formResponses[question.id];
            }
            cardBody.appendChild(dateInput);
            break;
            
        case 'number':
            const numberInput = document.createElement('input');
            numberInput.type = 'number';
            numberInput.className = 'form-control';
            numberInput.name = question.id;
            numberInput.id = `question_${question.id}`;
            numberInput.required = question.required;
            numberInput.step = 'any';
            
            if (question.minValue !== undefined) {
                numberInput.min = question.minValue;
            }
            if (question.maxValue !== undefined) {
                numberInput.max = question.maxValue;
            }
            
            // Restore value if exists
            if (formResponses[question.id]) {
                numberInput.value = formResponses[question.id];
            }
            
            cardBody.appendChild(numberInput);
            break;
            
        case 'yes_no':
            const yesNoContainer = document.createElement('div');
            yesNoContainer.className = 'd-flex';
            
            // Yes option
            const yesFormCheck = document.createElement('div');
            yesFormCheck.className = 'form-check form-check-inline';
            
            const yesInput = document.createElement('input');
            yesInput.className = 'form-check-input';
            yesInput.type = 'radio';
            yesInput.name = question.id;
            yesInput.id = `yes_${question.id}`;
            yesInput.value = 'YES';
            yesInput.required = question.required;
            // Restore checked state if exists
            if (formResponses[question.id] && formResponses[question.id] === 'YES') {
                yesInput.checked = true;
            }
            
            const yesLabel = document.createElement('label');
            yesLabel.className = 'form-check-label';
            yesLabel.htmlFor = `yes_${question.id}`;
            yesLabel.textContent = '{% trans "Yes" %}';
            
            yesFormCheck.appendChild(yesInput);
            yesFormCheck.appendChild(yesLabel);
            
            // No option
            const noFormCheck = document.createElement('div');
            noFormCheck.className = 'form-check form-check-inline';
            
            const noInput = document.createElement('input');
            noInput.className = 'form-check-input';
            noInput.type = 'radio';
            noInput.name = question.id;
            noInput.id = `no_${question.id}`;
            noInput.value = 'NO';
            // Restore checked state if exists
            if (formResponses[question.id] && formResponses[question.id] === 'NO') {
                noInput.checked = true;
            }
            
            const noLabel = document.createElement('label');
            noLabel.className = 'form-check-label';
            noLabel.htmlFor = `no_${question.id}`;
            noLabel.textContent = '{% trans "No" %}';
            
            noFormCheck.appendChild(noInput);
            noFormCheck.appendChild(noLabel);
            
            yesNoContainer.appendChild(yesFormCheck);
            yesNoContainer.appendChild(noFormCheck);
            cardBody.appendChild(yesNoContainer);
            break;
    }

    card.appendChild(cardBody);
    
    // Add change event listeners to update answered questions count and save responses
    const inputs = cardBody.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('change', function(event) {
            saveAnswers();
        });
        
        // For text inputs, also listen for keyup events to save while typing
        if (input.type === 'text' || input.tagName === 'TEXTAREA') {
            input.addEventListener('keyup', function(event) {
                // Only save after user stops typing (300ms delay)
                clearTimeout(input.saveTimeout);
                input.saveTimeout = setTimeout(() => {
                    saveAnswers();
                }, 300);
            });
        }
    });
    
    return card;
}

function renderSurvey() {
    // Guardar respuestas actuales antes de cambiar páginas
    saveAnswers();
    
    // Limpiar contenedor de preguntas
    questionsContainer.innerHTML = '';

    // Determinar cuántas preguntas mostrar por página
    const val = questionsPerPageSelect.value;
    itemsPerPage = (val === 'all') ? totalQuestions : parseInt(val, 10);

    // Calcular páginas totales y asegurar que la página actual sea válida
    const totalPages = Math.max(1, Math.ceil(totalQuestions / itemsPerPage));
    currentPage = Math.max(1, Math.min(currentPage, totalPages));

    // Determinar qué preguntas mostrar en la página actual
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, totalQuestions);
    const questionsToRender = questions.slice(startIndex, endIndex);

    // Renderizar cada pregunta
    questionsToRender.forEach(question => {
        questionsContainer.appendChild(renderQuestion(question));
    });

    // Actualizar controles de paginación
    pageInfoSpan.textContent = `{% trans "Page" %} ${currentPage} {% trans "of" %} ${totalPages}`;
    prevButton.disabled = currentPage === 1;
    nextButton.disabled = currentPage === totalPages;
    
    // Actualizar información de progreso
    totalQuestionsSpan.textContent = totalQuestions;
    totalQuestionsSpan2.textContent = totalQuestions;
    currentPageSpan.textContent = currentPage;
    totalPagesSpan.textContent = totalPages;

    // Ocultar paginación si solo hay una página
    const paginationControls = document.getElementById('pagination-controls');
    paginationControls.style.display = totalPages <= 1 ? 'none' : 'flex';
    
    // Comprobar preguntas condicionales
    updateConditionalQuestions();
}

function updateAnsweredQuestionsCount() {
    answeredQuestions = 0;
    const questionIds = Object.keys(formResponses);
    
    questionIds.forEach(id => {
        const value = formResponses[id];
        // Count question as answered if it has a non-empty value
        if (value && 
            ((typeof value === 'string' && value.trim() !== '') || 
             (Array.isArray(value) && value.length > 0))) {
            answeredQuestions++;
        }
    });
    
    answeredQuestionsSpan.textContent = answeredQuestions;
    
    // Update progress bar
    const progressBar = document.querySelector('.progress-bar');
    const progressPercentage = totalQuestions > 0 ? Math.round((answeredQuestions / totalQuestions) * 100) : 0;
    progressBar.style.width = `${progressPercentage}%`;
    progressBar.textContent = `${progressPercentage}%`;
    progressBar.setAttribute('aria-valuenow', progressPercentage);
}

function updateConditionalQuestions() {
    // Find all questions with dependencies
    const conditionalQuestions = document.querySelectorAll('[data-dependent-on]');
    
    conditionalQuestions.forEach(questionCard => {
        const dependentOnId = questionCard.dataset.dependentOn;
        const dependentValue = questionCard.dataset.dependentValue;
        const questionId = questionCard.dataset.questionId;
        
        // Check if parent question is answered with the dependent value
        let shouldShow = false;
        
        if (formResponses[dependentOnId]) {
            if (Array.isArray(formResponses[dependentOnId])) {
                // For checkboxes
                shouldShow = formResponses[dependentOnId].includes(dependentValue);
            } else {
                // For radio buttons and other inputs
                shouldShow = formResponses[dependentOnId] === dependentValue;
            }
        }
        
        // If the parent question input is on the current page, check its value directly
        const parentInputs = document.querySelectorAll(`input[name="${dependentOnId}"]`);
        parentInputs.forEach(input => {
            if (input.checked && input.value === dependentValue) {
                shouldShow = true;
            }
        });
        
        // Show or hide based on condition
        questionCard.style.display = shouldShow ? 'block' : 'none';
        
        // If hiding, clear inputs to avoid submitting data from hidden questions
        if (!shouldShow && formResponses[questionId]) {
            // Remove responses for hidden questions
            delete formResponses[questionId];
            
            // Also clear the DOM elements
            const inputs = questionCard.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                if (input.type === 'checkbox' || input.type === 'radio') {
                    input.checked = false;
                } else {
                    input.value = '';
                }
            });
        }
    });
    
    // Update answered count after showing/hiding questions
    updateAnsweredQuestionsCount();
}

// --- Event Listeners ---
questionsPerPageSelect.addEventListener('change', () => {
    // Guardar respuestas antes de cambiar opciones de visualización
    saveAnswers();
    // Reiniciar a primera página cuando se cambia el número de elementos por página
    currentPage = 1;
    // Renderizar la encuesta con la nueva configuración
    renderSurvey();
    // Desplazarse al inicio
    window.scrollTo(0, 0);
});

prevButton.addEventListener('click', () => {
    if (currentPage > 1) {
        // Guardar antes de navegar
        saveAnswers();
        currentPage--;
        renderSurvey();
        window.scrollTo(0, 0);
    }
});

nextButton.addEventListener('click', () => {
    const totalPages = Math.ceil(totalQuestions / itemsPerPage);
    if (currentPage < totalPages) {
        // Guardar antes de navegar
        saveAnswers();
        currentPage++;
        renderSurvey();
        window.scrollTo(0, 0);
    }
});

// Event delegation for conditional questions
document.addEventListener('change', function(e) {
    const target = e.target;
    if (target.tagName === 'INPUT' && (target.type === 'radio' || target.type === 'checkbox')) {
        saveAnswers(); // Guardar inmediatamente al cambiar opciones
        updateConditionalQuestions();
    }
});

// Multiple choice validation
surveyForm.addEventListener('submit', function(event) {
    // Save all responses before submission
    saveAnswers();
    
    // Validate multiple choice questions marked as required
    const validators = document.querySelectorAll('.multiple-choice-validator');
    let hasErrors = false;
    
    validators.forEach(validator => {
        const name = validator.dataset.name;
        
        // Check if we have any checked values in the responses
        let isChecked = false;
        if (formResponses[name] && Array.isArray(formResponses[name]) && formResponses[name].length > 0) {
            isChecked = true;
        } else {
            // Also check DOM in case it wasn't saved yet
            const checkboxes = document.querySelectorAll(`input[type="checkbox"][name="${name}"]`);
            checkboxes.forEach(checkbox => {
                if (checkbox.checked) {
                    isChecked = true;
                }
            });
        }
        
        if (!isChecked && validator.required) {
            hasErrors = true;
            
            // Find the parent card and highlight it
            const questionCard = validator.closest('.question-card');
            if (questionCard) {
                questionCard.scrollIntoView({ behavior: 'smooth' });
                questionCard.classList.add('border-danger');
                
                // Show validation message
                const errorMsg = document.createElement('div');
                errorMsg.className = 'alert alert-danger mt-2';
                errorMsg.textContent = '{% trans "Please select at least one option" %}';
                
                // Remove any existing error messages
                const existingErrors = questionCard.querySelectorAll('.alert-danger');
                existingErrors.forEach(err => err.remove());
                
                questionCard.querySelector('.card-body').appendChild(errorMsg);
            }
        }
    });
    
    if (hasErrors) {
        event.preventDefault();
        return false;
    } else {
        // Make sure the cached answers hidden field has the latest data
        if (cachedAnswersField) {
            cachedAnswersField.value = JSON.stringify(formResponses);
        }
    }
});

// Also handle 'respond for other' checkbox
if (document.getElementById('respond-for-other')) {
    document.getElementById('respond-for-other').addEventListener('change', function() {
        const otherFields = document.getElementById('other-respondent-fields');
        if (this.checked) {
            otherFields.style.display = 'block';
        } else {
            otherFields.style.display = 'none';
        }
    });
}

// Debug function to check saved responses
function debugSurvey() {
    console.log("Current formResponses:", formResponses);
    console.log("LocalStorage data:", localStorage.getItem(storageKey));
    console.log("Current page:", currentPage);
    console.log("Items per page:", itemsPerPage);
}

// Para activar la depuración, añade la siguiente línea y descomenta
// window.debugSurvey = debugSurvey;

// --- Initialize ---
window.addEventListener('DOMContentLoaded', () => {
    // Try to load responses from localStorage if available
    formResponses = loadAnswers();
    console.log('Loaded responses from localStorage:', formResponses);
    
    // Update the hidden field for form submission
    if (cachedAnswersField) {
        cachedAnswersField.value = JSON.stringify(formResponses);
    }
    
    // Set counters
    totalQuestionsSpan.textContent = totalQuestions;
    totalQuestionsSpan2.textContent = totalQuestions;
    
    // Render the survey
    renderSurvey();
    
    // Initial count of answered questions
    updateAnsweredQuestionsCount();
    
    // Periodically save responses to localStorage
    setInterval(() => {
        saveAnswers();
    }, 30000); // Every 30 seconds
    
    // Add window beforeunload event to save responses when page is closed
    window.addEventListener('beforeunload', function() {
        saveAnswers();
    });
});

// Clear localStorage when form is submitted successfully
surveyForm.addEventListener('submit', function() {
    // On successful submission (you may want to move this to an AJAX success callback)
    setTimeout(() => {
        localStorage.removeItem(storageKey);
        console.log('Survey submitted, localStorage cleared');
    }, 1000);
});