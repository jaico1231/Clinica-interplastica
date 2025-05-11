import 'bootstrap'; // Only if Bootstrap JS features like tooltips/popovers are needed, otherwise optional

// --- Load Questions Data from survey-data script tag ---
// This will replace the hardcoded 'questions' array
let questions = [];
let savedAnswers = {};

// Try to load from the survey-data script tag injected by Django
try {
    const surveyDataElement = document.getElementById('survey-data');
    if (surveyDataElement) {
        const surveyData = JSON.parse(surveyDataElement.textContent);
        questions = surveyData.questions || [];
        savedAnswers = surveyData.savedAnswers || {};
    }
} catch (error) {
    console.error('Error parsing survey data:', error);
    // Fallback to empty arrays if there's an error
    questions = [];
    savedAnswers = {};
}

// --- State Variables ---
let currentPage = 1;
let itemsPerPage = 5; // Default value from the select dropdown
const totalQuestions = questions.length;
const storageKey = 'surveyAnswers'; // Key for sessionStorage

// --- DOM Elements ---
const questionsContainer = document.getElementById('questions-container');
const questionsPerPageSelect = document.getElementById('questions-per-page');
const prevButton = document.getElementById('prev-btn');
const nextButton = document.getElementById('next-btn');
const pageInfoSpan = document.getElementById('page-info');
const surveyForm = document.getElementById('survey-form');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');

// --- Answer Storage Functions ---

function loadAnswers() {
    // First check if we have saved answers from the server
    if (Object.keys(savedAnswers).length > 0) {
        // Store server-provided answers in session storage
        sessionStorage.setItem(storageKey, JSON.stringify(savedAnswers));
        // Clear the saved answers to avoid overwriting new changes
        savedAnswers = {};
    }
    
    // Now load from session storage as normal
    const storedAnswers = sessionStorage.getItem(storageKey);
    return storedAnswers ? JSON.parse(storedAnswers) : {};
}

function saveAnswers() {
    const currentAnswers = loadAnswers(); // Load existing answers
    const inputs = questionsContainer.querySelectorAll('input, textarea, select'); // Select all relevant inputs within the container

    inputs.forEach(input => {
        const name = input.name;
        if (!name) return; // Skip elements without a name

        const questionId = name; // Assuming input name is the question ID

        switch (input.type) {
            case 'checkbox':
                if (!currentAnswers[questionId]) {
                    currentAnswers[questionId] = []; // Initialize as array if not exists
                }
                 // Remove value if unchecked, add if checked
                const index = currentAnswers[questionId].indexOf(input.value);
                 if (input.checked) {
                     if (index === -1) { // Add only if not already present
                        currentAnswers[questionId].push(input.value);
                     }
                 } else {
                     if (index > -1) { // Remove if present
                        currentAnswers[questionId].splice(index, 1);
                     }
                 }
                 // If the array is empty after modifications, store an empty array
                 if (currentAnswers[questionId].length === 0) {
                     // We could delete the key, but storing empty array might be clearer
                     // delete currentAnswers[questionId];
                 }
                break;
            case 'radio':
                if (input.checked) {
                    currentAnswers[questionId] = input.value;
                }
                break;
            default: // For text, email, date, number, textarea
                currentAnswers[questionId] = input.value;
                break;
        }
    });

    // Clean up empty checkbox arrays before saving
    Object.keys(currentAnswers).forEach(key => {
        if (Array.isArray(currentAnswers[key]) && currentAnswers[key].length === 0) {
             // Check if the question corresponding to this key is currently rendered
             const isRendered = Array.from(questionsContainer.querySelectorAll(`[name="${key}"]`)).length > 0;
             // Only delete if the question was rendered (meaning the user unchecked all)
             // Otherwise, keep potentially saved answers from other pages.
             if (isRendered) {
                 delete currentAnswers[key]; // Or keep as empty array: currentAnswers[key] = [];
             }
        } else if (currentAnswers[key] === '' && document.querySelector(`[name="${key}"]`)) {
             // Also remove empty strings for currently rendered inputs if desired
             // delete currentAnswers[key];
        }
    });


    sessionStorage.setItem(storageKey, JSON.stringify(currentAnswers));
    // console.log("Answers saved:", currentAnswers); // For debugging
    updateProgress(); // Update progress whenever answers are saved
}

function renderHierarchyQuestion(question, savedAnswers) {
    // Create main container
    const card = document.createElement('div');
    card.className = 'card question-card mb-3';
    
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';
    
    // Create question title
    const title = document.createElement('label');
    title.className = 'question-title d-block mb-2';
    title.textContent = question.text;
    
    if (question.required) {
        const requiredSpan = document.createElement('span');
        requiredSpan.className = 'question-required';
        requiredSpan.textContent = 'Obligatorio';
        title.appendChild(requiredSpan);
    }
    
    cardBody.appendChild(title);
    
    // Add help text if available
    if (question.help_text) {
        const helpText = document.createElement('p');
        helpText.className = 'text-muted mb-3 small';
        helpText.textContent = question.help_text;
        cardBody.appendChild(helpText);
    }
    
    // Create hierarchy structure container
    const hierarchyContainer = document.createElement('div');
    hierarchyContainer.className = 'hierarchy-container';
    hierarchyContainer.id = `hierarchy-container-${question.id}`;
    cardBody.appendChild(hierarchyContainer);
    
    // Get previously saved answer for this question
    const savedValue = savedAnswers[question.id] || [];
    
    // Create the hierarchy structure
    if (question.hierarchy_items && question.hierarchy_items.length > 0) {
        // Group items by level
        const itemsByLevel = {};
        question.hierarchy_items.forEach(item => {
            if (!itemsByLevel[item.level]) {
                itemsByLevel[item.level] = [];
            }
            itemsByLevel[item.level].push(item);
        });
        
        // Create level containers
        const levels = Object.keys(itemsByLevel).sort();
        
        // Create a level column for each level
        const hierarchyRow = document.createElement('div');
        hierarchyRow.className = 'row hierarchy-row';
        
        levels.forEach(level => {
            const levelContainer = document.createElement('div');
            levelContainer.className = 'col hierarchy-level';
            levelContainer.dataset.level = level;
            
            const levelHeader = document.createElement('h6');
            levelHeader.className = 'hierarchy-level-title';
            levelHeader.textContent = `Level ${parseInt(level) + 1}`;
            levelContainer.appendChild(levelHeader);
            
            const itemsList = document.createElement('ul');
            itemsList.className = 'list-group hierarchy-items';
            itemsList.dataset.level = level;
            itemsList.id = `hierarchy-level-${question.id}-${level}`;
            
            // Add items to this level
            itemsByLevel[level].forEach(item => {
                const itemElement = document.createElement('li');
                itemElement.className = 'list-group-item hierarchy-item';
                itemElement.draggable = true;
                itemElement.dataset.id = item.id;
                itemElement.dataset.level = item.level;
                itemElement.textContent = item.text;
                
                // Set item as selected in its level if saved
                const matchingAnswer = Array.isArray(savedValue) 
                    ? savedValue.find(answer => answer.item_id === item.id) 
                    : null;
                
                if (matchingAnswer) {
                    // If this level matches the saved level, mark it
                    if (parseInt(level) === matchingAnswer.position) {
                        itemElement.classList.add('active');
                        itemElement.dataset.selectedLevel = matchingAnswer.position;
                        
                        // If there's a parent selection, store it
                        if (matchingAnswer.parent_id) {
                            itemElement.dataset.parentId = matchingAnswer.parent_id;
                        }
                    }
                }
                
                itemsList.appendChild(itemElement);
            });
            
            levelContainer.appendChild(itemsList);
            hierarchyRow.appendChild(levelContainer);
        });
        
        hierarchyContainer.appendChild(hierarchyRow);
        
        // Add hidden input to store the final hierarchy structure
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = question.id;
        hiddenInput.id = `hierarchy-input-${question.id}`;
        
        // Set initial value from saved answers
        if (Array.isArray(savedValue) && savedValue.length > 0) {
            hiddenInput.value = JSON.stringify(savedValue);
        } else {
            hiddenInput.value = '[]';
        }
        
        cardBody.appendChild(hiddenInput);
        
        // Initialize drag and drop after everything is rendered
        setTimeout(() => {
            initHierarchyDragDrop(question.id);
        }, 0);
    } else {
        // No items, show a message
        const noItemsMsg = document.createElement('p');
        noItemsMsg.className = 'text-muted';
        noItemsMsg.textContent = 'No hay elementos jerárquicos disponibles para esta pregunta.';
        hierarchyContainer.appendChild(noItemsMsg);
    }
    
    card.appendChild(cardBody);
    return card;
}

function initHierarchyDragDrop(questionId) {
    const container = document.getElementById(`hierarchy-container-${questionId}`);
    if (!container) return;
    
    const itemLists = container.querySelectorAll('.hierarchy-items');
    
    itemLists.forEach(list => {
        new Sortable(list, {
            group: `hierarchy-group-${questionId}`,
            animation: 150,
            onEnd: function(evt) {
                // Handle item drop
                const item = evt.item;
                const fromList = evt.from;
                const toList = evt.to;
                
                // Update item's level based on its new list
                const newLevel = toList.dataset.level;
                item.dataset.level = newLevel;
                
                // Mark the item as active in its new level
                itemLists.forEach(list => {
                    const items = list.querySelectorAll(`.hierarchy-item[data-id="${item.dataset.id}"]`);
                    items.forEach(i => {
                        if (i === item) {
                            i.classList.add('active');
                            i.dataset.selectedLevel = newLevel;
                        } else {
                            i.classList.remove('active');
                            delete i.dataset.selectedLevel;
                        }
                    });
                });
                
                // Update the hidden input with the new structure
                updateHierarchyInput(questionId);
            }
        });
    });
    
    // Add click handler for selecting items
    container.querySelectorAll('.hierarchy-item').forEach(item => {
        item.addEventListener('click', function(e) {
            const clickedItem = e.currentTarget;
            const itemId = clickedItem.dataset.id;
            const level = clickedItem.closest('.hierarchy-items').dataset.level;
            
            // Toggle selection in current level
            const itemsInLevel = clickedItem.closest('.hierarchy-items').querySelectorAll('.hierarchy-item');
            itemsInLevel.forEach(i => {
                if (i === clickedItem) {
                    i.classList.toggle('active');
                    if (i.classList.contains('active')) {
                        i.dataset.selectedLevel = level;
                    } else {
                        delete i.dataset.selectedLevel;
                    }
                } else {
                    i.classList.remove('active');
                    delete i.dataset.selectedLevel;
                }
            });
            
            // Update the hidden input
            updateHierarchyInput(questionId);
        });
    });
}

function updateHierarchyInput(questionId) {
    const container = document.getElementById(`hierarchy-container-${questionId}`);
    const hiddenInput = document.getElementById(`hierarchy-input-${questionId}`);
    const hierarchyData = [];
    
    // Find all active/selected items
    const selectedItems = container.querySelectorAll('.hierarchy-item.active');
    
    selectedItems.forEach(item => {
        const itemData = {
            item_id: item.dataset.id,
            position: parseInt(item.dataset.selectedLevel || 0),
            level: parseInt(item.dataset.level || 0)
        };
        
        // Add parent_id if present
        if (item.dataset.parentId) {
            itemData.parent_id = item.dataset.parentId;
        }
        
        hierarchyData.push(itemData);
    });
    
    // Update the hidden input
    hiddenInput.value = JSON.stringify(hierarchyData);
    
    // Also save to session storage through the regular save function
    saveAnswers();
}

// --- Progress Calculation ---
function updateProgress() {
    const savedAnswers = loadAnswers();
    const requiredQuestions = questions.filter(q => q.required);
    const totalRequired = requiredQuestions.length;

    if (totalRequired === 0) {
        progressText.textContent = "No hay preguntas obligatorias.";
        progressBar.style.width = '100%';
        progressBar.setAttribute('aria-valuenow', 100);
        return;
    }

    let answeredRequiredCount = 0;
    requiredQuestions.forEach(q => {
        const answer = savedAnswers[q.id];
        let isAnswered = false;
        if (answer !== undefined && answer !== null) {
            if (q.type === 'multiple_choice') {
                // Checkbox is answered if the array exists and has at least one item
                isAnswered = Array.isArray(answer) && answer.length > 0;
            } else if (typeof answer === 'string') {
                // Text, textarea, radio, date, email, number (stored as string sometimes)
                isAnswered = answer.trim() !== '';
            } else {
                 // Should cover cases like number type if stored as number
                isAnswered = true;
            }
        }
         if (isAnswered) {
             answeredRequiredCount++;
         }
    });

    const percentage = totalRequired > 0 ? Math.round((answeredRequiredCount / totalRequired) * 100) : 0;

    progressText.textContent = `${answeredRequiredCount} de ${totalRequired} preguntas obligatorias respondidas.`;
    progressBar.style.width = `${percentage}%`;
    progressBar.setAttribute('aria-valuenow', percentage);
    progressBar.textContent = `${percentage}%`; // Optionally show percentage inside bar
}

// --- Functions ---

function renderQuestion(question, savedAnswers) {
    // Map question types from Django to input types
    const typeMapping = {
        'text': 'text',
        'text_area': 'textarea',
        'number': 'number',
        'date': 'date',
        'yes_no': 'radio',
        'single_choice': 'radio',
        'multiple_choice': 'checkbox',
        'rating': 'radio',
        'email': 'email',
        'hierarchy': 'hierarchy'
    };
    
    // Get the HTML input type from the Django question type
    const inputType = typeMapping[question.type] || 'text';
    
    if (inputType === 'hierarchy') {
        return renderHierarchyQuestion(question, savedAnswers);
    }
    
    // Create card and title
    const card = document.createElement('div');
    card.className = 'card question-card mb-3'; // Added mb-3 for spacing

    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';

    const title = document.createElement('label'); // Using label for better accessibility
    title.className = 'question-title d-block mb-2'; // d-block to ensure it takes full width
    title.textContent = question.text;
    if (question.required) {
        const requiredSpan = document.createElement('span');
        requiredSpan.className = 'question-required';
        requiredSpan.textContent = 'Obligatorio';
        title.appendChild(requiredSpan);
    }
    cardBody.appendChild(title);

    let inputElement;
    const savedValue = savedAnswers[question.id];

    switch (inputType) {
        case 'text':
        case 'email':
        case 'date':
        case 'number':
            inputElement = document.createElement('input');
            inputElement.type = inputType;
            inputElement.className = 'form-control';
            inputElement.id = question.id;
            inputElement.name = question.id;
            inputElement.required = question.required;
            if (question.placeholder) {
                inputElement.placeholder = question.placeholder;
            }
            // --- Load Answer ---
            if (savedValue !== undefined) {
                inputElement.value = savedValue;
            }
            // --- Set Label For ---
            title.htmlFor = question.id;
            cardBody.appendChild(inputElement);
            break;
        case 'textarea':
             inputElement = document.createElement('textarea');
             inputElement.className = 'form-control';
             inputElement.id = question.id;
             inputElement.name = question.id;
             inputElement.required = question.required;
             inputElement.rows = 3;
             if (question.placeholder) {
                 inputElement.placeholder = question.placeholder;
             }
             // --- Load Answer ---
             if (savedValue !== undefined) {
                inputElement.value = savedValue;
             }
             // --- Set Label For ---
            title.htmlFor = question.id;
             cardBody.appendChild(inputElement);
             break;
        case 'radio':
            // Special handling for yes_no type - create standard Yes/No options
            if (question.type === 'yes_no') {
                // Create default Yes/No options if not provided
                const yesNoOptions = [
                    { value: 'true', text: 'Sí' },
                    { value: 'false', text: 'No' }
                ];
                
                yesNoOptions.forEach((option, index) => {
                    const formCheck = document.createElement('div');
                    formCheck.className = 'form-check';
                    const inputId = `${question.id}-${index}`;

                    inputElement = document.createElement('input');
                    inputElement.type = 'radio';
                    inputElement.className = 'form-check-input';
                    inputElement.id = inputId;
                    inputElement.name = question.id;
                    inputElement.value = option.value;
                    inputElement.required = question.required && index === 0;

                    // Load answer - handle different yes/no value formats
                    if (savedValue !== undefined) {
                        if (typeof savedValue === 'boolean') {
                            // If boolean value
                            inputElement.checked = 
                                (option.value === 'true' && savedValue === true) || 
                                (option.value === 'false' && savedValue === false);
                        } else if (typeof savedValue === 'string') {
                            // If string value like 'true', 'false', 'yes', 'no'
                            const lowerSavedValue = savedValue.toLowerCase();
                            inputElement.checked = 
                                (option.value === 'true' && (lowerSavedValue === 'true' || lowerSavedValue === 'yes')) || 
                                (option.value === 'false' && (lowerSavedValue === 'false' || lowerSavedValue === 'no'));
                        }
                    }

                    const label = document.createElement('label');
                    label.className = 'form-check-label';
                    label.htmlFor = inputId;
                    label.textContent = option.text;

                    formCheck.appendChild(inputElement);
                    formCheck.appendChild(label);
                    cardBody.appendChild(formCheck);
                });
                
                // Set main label 'for' to the first option
                title.htmlFor = `${question.id}-0`;
            } 
            // Regular radio options for single_choice and rating
            else if (question.options && question.options.length > 0) {
                question.options.forEach((option, index) => {
                    const formCheck = document.createElement('div');
                    formCheck.className = 'form-check';
                    const inputId = `${question.id}-${index}`;

                    inputElement = document.createElement('input');
                    inputElement.type = 'radio';
                    inputElement.className = 'form-check-input';
                    inputElement.id = inputId;
                    inputElement.name = question.id; // Same name for radio buttons
                    
                    // Support both object and string formats for options
                    const optionValue = typeof option === 'object' ? option.value : option;
                    inputElement.value = optionValue;
                    
                    // Make first radio required for the group if the question is required
                    inputElement.required = question.required && index === 0;

                    // --- Load Answer ---
                    if (savedValue === optionValue) {
                        inputElement.checked = true;
                    }

                    const label = document.createElement('label');
                    label.className = 'form-check-label';
                    label.htmlFor = inputId;
                    label.textContent = typeof option === 'object' ? option.text : option;

                    formCheck.appendChild(inputElement);
                    formCheck.appendChild(label);
                    cardBody.appendChild(formCheck);
                });
                // Set main label 'for' to the first option
                title.htmlFor = `${question.id}-0`;
            }
            break;
         case 'checkbox':
            if (question.options && question.options.length > 0) {
                question.options.forEach((option, index) => {
                    const formCheck = document.createElement('div');
                    formCheck.className = 'form-check';
                    const inputId = `${question.id}-${index}`;

                    inputElement = document.createElement('input');
                    inputElement.type = 'checkbox';
                    inputElement.className = 'form-check-input';
                    inputElement.id = inputId;
                    inputElement.name = question.id; // Use question ID as name
                    
                    // Support both object and string formats for options
                    const optionValue = typeof option === 'object' ? option.value : option;
                    inputElement.value = optionValue;
                    
                    inputElement.required = question.required && index === 0;

                    // --- Load Answer ---
                    if (Array.isArray(savedValue) && savedValue.includes(optionValue)) {
                        inputElement.checked = true;
                    }

                    const label = document.createElement('label');
                    label.className = 'form-check-label';
                    label.htmlFor = inputId;
                    label.textContent = typeof option === 'object' ? option.text : option;

                    formCheck.appendChild(inputElement);
                    formCheck.appendChild(label);
                    cardBody.appendChild(formCheck);
                });
                // Set main label 'for' to the first option
                title.htmlFor = `${question.id}-0`;
            }
            break;
    }

    card.appendChild(cardBody);
    return card;
}

function renderSurvey() {
    const savedAnswers = loadAnswers(); // Load answers first
    // console.log("Rendering with answers:", savedAnswers); // For debugging

    questionsContainer.innerHTML = ''; // Clear previous questions

    const val = questionsPerPageSelect.value;
    itemsPerPage = (val === 'all') ? totalQuestions : parseInt(val, 10);

    const totalPages = (itemsPerPage > 0) ? Math.ceil(totalQuestions / itemsPerPage) : 1;
    // Clamp currentPage between 1 and totalPages
    currentPage = Math.max(1, Math.min(currentPage, totalPages));


    const startIndex = (currentPage - 1) * itemsPerPage;
    // If itemsPerPage is totalQuestions, endIndex should cover all
    const endIndex = (itemsPerPage === totalQuestions) ? totalQuestions : startIndex + itemsPerPage;

    const questionsToRender = questions.slice(startIndex, endIndex);

    questionsToRender.forEach(question => {
        // Pass savedAnswers to renderQuestion
        questionsContainer.appendChild(renderQuestion(question, savedAnswers));
    });

    // Update pagination controls
    pageInfoSpan.textContent = `Página ${currentPage} de ${totalPages}`;
    prevButton.disabled = currentPage === 1;
    nextButton.disabled = currentPage === totalPages;

     // Hide pagination if only one page
     const paginationControls = document.getElementById('pagination-controls');
     if (totalPages <= 1) {
         paginationControls.style.display = 'none';
     } else {
         paginationControls.style.display = 'flex';
     }

     // Update progress after rendering
     updateProgress();
}

// --- Event Listeners ---

// IMPORTANTE: Prevenir el envío del formulario en eventos de cambio
function preventFormSubmit(event) {
    // Evitar que el evento de cambio envíe el formulario
    event.preventDefault();
    // Aún guardar las respuestas
    saveAnswers();
}

questionsPerPageSelect.addEventListener('change', (event) => {
    event.preventDefault(); // Prevent form submission
    saveAnswers(); // Save before changing view
    currentPage = 1; // Reset to first page when changing items per page
    renderSurvey();
});

// UPDATED: Changed to handle client-side navigation instead of form submission
prevButton.addEventListener('click', (event) => {
    event.preventDefault(); // Prevent any form submission
    if (currentPage > 1) {
        saveAnswers(); // Save before navigating
        currentPage--;
        renderSurvey();
        window.scrollTo(0, 0); // Scroll to top
    }
});

// UPDATED: Changed to handle client-side navigation instead of form submission
nextButton.addEventListener('click', (event) => {
    event.preventDefault(); // Prevent any form submission
    const totalPages = (itemsPerPage > 0 && itemsPerPage !== totalQuestions) ? Math.ceil(totalQuestions / itemsPerPage) : 1;
    if (currentPage < totalPages) {
        saveAnswers(); // Save before navigating
        currentPage++;
        renderSurvey();
        window.scrollTo(0, 0); // Scroll to top
    }
});

// Modificar para prevenir envío automático del formulario
questionsContainer.addEventListener('input', (event) => {
    // Prevenir envío de formulario y solo guardar respuestas
    event.preventDefault();
    
    // Save on 'input' for text fields, textareas, etc. for immediate feedback
    if (event.target.matches('input:not([type=radio]):not([type=checkbox]), textarea')) {
        saveAnswers();
    }
    
    // Evitar que el evento se propague al formulario
    event.stopPropagation();
    return false;
});

// Modificar para prevenir envío automático del formulario
questionsContainer.addEventListener('change', (event) => {
    // Prevenir envío de formulario y solo guardar respuestas
    event.preventDefault();
    
    // Save on 'change' for selects, radios, checkboxes, date, etc.
    if (event.target.matches('input[type=radio], input[type=checkbox], input[type=date], select')) {
        saveAnswers();
    }
    
    // Evitar que el evento se propague al formulario
    event.stopPropagation();
    return false;
});

// Interceptar todos los eventos submit que no vengan del botón final
document.addEventListener('submit', function(event) {
    // Obtener el elemento que originó el submit
    const submitter = event.submitter;
    
    // Si no es el botón de enviar (submit_survey), evitar envío
    if (!submitter || submitter.name !== 'submit_survey') {
        event.preventDefault();
    }
    
    // Siempre guardar las respuestas
    saveAnswers();
}, true); // Usar la fase de captura

// Solo permita el envío cuando explícitamente haga clic en el botón de enviar
surveyForm.addEventListener('submit', (event) => {
    // Obtener el elemento que originó el submit
    const submitter = event.submitter;
    
    // Si no es el botón de enviar (submit_survey), evitar envío
    if (!submitter || submitter.name !== 'submit_survey') {
        event.preventDefault();
        return false;
    }
    
    // Si es el botón de enviar, guardar respuestas y permitir el envío
    saveAnswers(); // Save one last time before submitting
});

// --- Initial Render ---
document.addEventListener('DOMContentLoaded', function() {
    // Asegurarse de que los eventos por defecto no envíen el formulario
    const inputs = surveyForm.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('change', preventFormSubmit);
        if (input.type !== 'radio' && input.type !== 'checkbox') {
            input.addEventListener('input', preventFormSubmit);
        }
    });
    
    // First load saved answers from the server (if any)
    renderSurvey();
});