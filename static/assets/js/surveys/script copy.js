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
        'email': 'email'
    };
    
    // Get the HTML input type from the Django question type
    const inputType = typeMapping[question.type] || 'text';
    
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

questionsPerPageSelect.addEventListener('change', () => {
    saveAnswers(); // Save before changing view
    currentPage = 1; // Reset to first page when changing items per page
    renderSurvey();
});

prevButton.addEventListener('click', () => {
    if (currentPage > 1) {
        saveAnswers(); // Save before navigating
        currentPage--;
        renderSurvey();
        window.scrollTo(0, 0); // Scroll to top
    }
});

nextButton.addEventListener('click', () => {
    const totalPages = (itemsPerPage > 0 && itemsPerPage !== totalQuestions) ? Math.ceil(totalQuestions / itemsPerPage) : 1;
    if (currentPage < totalPages) {
        saveAnswers(); // Save before navigating
        currentPage++;
        renderSurvey();
        window.scrollTo(0, 0); // Scroll to top
    }
});

questionsContainer.addEventListener('input', (event) => {
    // Save on 'input' for text fields, textareas, etc. for immediate feedback
    if (event.target.matches('input:not([type=radio]):not([type=checkbox]), textarea')) {
        saveAnswers();
    }
});
questionsContainer.addEventListener('change', (event) => {
     // Save on 'change' for selects, radios, checkboxes, date, etc.
    if (event.target.matches('input[type=radio], input[type=checkbox], input[type=date], select')) {
        saveAnswers();
    }
});

surveyForm.addEventListener('submit', (event) => {
    // Don't prevent default form submission - let the form submit normally to the server
    // event.preventDefault();
    saveAnswers(); // Save one last time before submitting

    // For testing/debugging only - comment this out for production
    // console.log('Form submitted!');
    // alert('Encuesta enviada (simulado). Revisa la consola para ver los datos.');
    // console.log('Final Survey Data (from storage):', loadAnswers());
});

// --- Initial Render ---
document.addEventListener('DOMContentLoaded', function() {
    // First load saved answers from the server (if any)
    renderSurvey();
});

// For debugging
function logQuestions() {
    console.log('Questions loaded:', questions);
    questions.forEach(q => {
        if (q.type === 'yes_no') {
            console.log('Yes/No question found:', q);
        }
    });
}

// Uncomment to debug
// setTimeout(logQuestions, 1000);