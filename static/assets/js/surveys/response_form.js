import 'bootstrap'; // Only if Bootstrap JS features like tooltips/popovers are needed, otherwise optional

// --- Sample Questions Data ---
const questions = [
    { id: 'q1', type: 'text', text: '1. Respuesta de texto', required: true, placeholder: 'Respuesta detallada' },
    { id: 'q2', type: 'text', text: '2. Respuesta pequeña', required: true, placeholder: 'Respuesta breve' },
    { id: 'q3', type: 'email', text: 'Información del Encuestado: Your Email (optional)', required: false, placeholder: 'you@example.com' },
    { id: 'q10', type: 'text', text: '10. ¿Qué es?', required: true, placeholder: '' },
    { id: 'q20', type: 'radio', text: '20. Segunda pregunta', required: true, options: ['Opción 1', 'Opción 2', 'Opción 3'] },
    { id: 'q30', type: 'radio', text: '30. Número', required: false, options: ['Sí', 'No'] },
    { id: 'q40', type: 'date', text: '40. Data', required: true },
    { id: 'q50', type: 'checkbox', text: '50. Selección Múltiple', required: true, options: ['Opción 1', 'Opción 2', 'Opción 3', 'Opción 4'] },
    { id: 'q60', type: 'radio', text: '60. Única selección', required: true, options: ['Te gusta la primera', 'Te gusta la 5', 'Te gusta la 6', 'Te gusta la segunda', 'Te gusta la tercera'] },
    { id: 'q70', type: 'textarea', text: '70. Comentarios adicionales', required: false, placeholder: 'Escribe tus comentarios aquí...' },
    { id: 'q80', type: 'number', text: '80. ¿Cuántos años tienes?', required: false, placeholder: 'Edad' },
];

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

// --- Answer Storage Functions ---

function loadAnswers() {
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
}


// --- Functions ---

function renderQuestion(question, savedAnswers) {
    // ... existing card and title creation code ...
    const card = document.createElement('div');
    card.className = 'card question-card mb-3'; // Added mb-3 for spacing

    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';

    const title = document.createElement('label'); // Using label for better accessibility
    title.className = 'question-title d-block mb-2'; // d-block to ensure it takes full width
    // title.htmlFor = question.id; // Set htmlFor later based on input type
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

    switch (question.type) {
        case 'text':
        case 'email':
        case 'date':
        case 'number':
            inputElement = document.createElement('input');
            inputElement.type = question.type;
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
            question.options.forEach((option, index) => {
                const formCheck = document.createElement('div');
                formCheck.className = 'form-check';
                const inputId = `${question.id}-${index}`;

                inputElement = document.createElement('input');
                inputElement.type = question.type;
                inputElement.className = 'form-check-input';
                inputElement.id = inputId;
                inputElement.name = question.id; // Same name for radio buttons
                inputElement.value = option;
                // Make first radio required for the group if the question is required
                inputElement.required = question.required && index === 0;

                // --- Load Answer ---
                if (savedValue === option) {
                    inputElement.checked = true;
                }

                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.htmlFor = inputId;
                label.textContent = option;

                formCheck.appendChild(inputElement);
                formCheck.appendChild(label);
                cardBody.appendChild(formCheck);
            });
             // Set main label 'for' to the first option
             if (question.options.length > 0) {
                 title.htmlFor = `${question.id}-0`;
             }
            break;
         case 'checkbox':
            question.options.forEach((option, index) => {
                const formCheck = document.createElement('div');
                formCheck.className = 'form-check';
                const inputId = `${question.id}-${index}`;

                inputElement = document.createElement('input');
                inputElement.type = question.type;
                inputElement.className = 'form-check-input';
                inputElement.id = inputId;
                // Checkbox names should indicate they belong to a group, but use unique value
                inputElement.name = question.id; // Use question ID as name
                inputElement.value = option;
                // Requirement handled by form validation (checking if at least one is checked if required)
                // We might add custom validation later if needed. Bootstrap handles basic 'required' on first element.
                // For true "at least one" validation, JS is needed on submit.
                inputElement.required = question.required && index === 0; // Still useful for browser validation hints


                // --- Load Answer ---
                if (Array.isArray(savedValue) && savedValue.includes(option)) {
                    inputElement.checked = true;
                }


                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.htmlFor = inputId;
                label.textContent = option;

                formCheck.appendChild(inputElement);
                formCheck.appendChild(label);
                cardBody.appendChild(formCheck);
            });
            // Set main label 'for' to the first option
             if (question.options.length > 0) {
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

surveyForm.addEventListener('submit', (event) => {
    event.preventDefault(); // Prevent default form submission
    saveAnswers(); // Save one last time before submitting

    console.log('Form submitted!');
    alert('Encuesta enviada (simulado). Revisa la consola para ver los datos.');

    // Gather final data from storage
    const finalAnswers = loadAnswers();
    console.log('Final Survey Data (from storage):', finalAnswers);

    // Optionally clear storage after submission
    sessionStorage.removeItem(storageKey);
    console.log('Session storage cleared.');

    // Here you would typically send 'finalAnswers' to a server
    // For example:
    // fetch('/submit-survey', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify(finalAnswers)
    // })
    // .then(response => response.json())
    // .then(data => console.log('Server response:', data))
    // .catch(error => console.error('Error submitting survey:', error));

     // Maybe redirect or show a thank you message
     // surveyForm.innerHTML = '<div class="alert alert-success">¡Gracias por completar la encuesta!</div>';
     // document.getElementById('pagination-controls').style.display = 'none';
});

// --- Initial Render ---
// No need to explicitly load here, renderSurvey does it
renderSurvey();