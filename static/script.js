document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const uploadForm = document.getElementById('upload-form');
    const submitButton = document.getElementById('submit-button');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorMessage = document.getElementById('error-message');
    
    const subjectTilesContainer = document.getElementById('subject-tiles');
    const contentContainer = document.getElementById('content-container');
    const currentSubjectTitle = document.getElementById('current-subject-title');
    const summaryContent = document.getElementById('summary-content');
    const flashcardsContent = document.getElementById('flashcards-content');
    const quizContent = document.getElementById('quiz-content');

    const qaForm = document.getElementById('qa-form');
    const qaInput = document.getElementById('qa-input');
    const qaResponse = document.getElementById('qa-response');

    const fileInput = document.getElementById('file-input');
    const youtubeInput = document.getElementById('youtube-url');
    const subjectInput = document.getElementById('subject-input');

    // --- State ---
    let activeTab = 'file';
    let currentSubject = null;
    let subjects = [];

    // --- Initialization ---
    async function init() {
        await fetchSubjects();
        renderSubjectTiles();
    }

    // --- Data Fetching ---
    async function fetchSubjects() {
        try {
            const response = await fetch('/api/subjects');
            if (!response.ok) throw new Error('Failed to fetch subjects.');
            const data = await response.json();
            subjects = data.subjects || [];
        } catch (error) {
            showError(error.message);
        }
    }

    // --- Rendering ---
    function renderSubjectTiles() {
        subjectTilesContainer.innerHTML = '';
        if (subjects.length === 0) {
            subjectTilesContainer.innerHTML = '<p>No subjects yet. Add one below!</p>';
            return;
        }
        subjects.forEach(subject => {
            const tile = document.createElement('div');
            tile.className = 'tile';
            tile.textContent = subject.name;
            tile.addEventListener('click', () => handleSubjectClick(subject.name));
            subjectTilesContainer.appendChild(tile);
        });
    }

    function renderSubjectContent(subjectName) {
        const subject = subjects.find(s => s.name === subjectName);
        if (!subject) {
            contentContainer.classList.add('hidden');
            return;
        }

        currentSubject = subjectName;
        currentSubjectTitle.textContent = subject.name;

        // Summary
        summaryContent.innerHTML = `<p>${subject.summary.replace(/\n/g, '<br>')}</p>`;

        // Flashcards
        renderFlashcards(subject.flashcards);

        // Quiz
        renderQuiz(subject.quiz);

        contentContainer.classList.remove('hidden');
    }

    function renderFlashcards(flashcards) {
        flashcardsContent.innerHTML = '';
        if (!flashcards || flashcards.length === 0) {
            flashcardsContent.innerHTML = '<p>No flashcards available.</p>';
            return;
        }
        flashcards.forEach(card => {
            const cardEl = document.createElement('div');
            cardEl.className = 'tile flashcard';
            cardEl.innerHTML = `<div class="flashcard-inner"><div class="flashcard-front">${card.term}</div><div class="flashcard-back">${card.definition}</div></div>`;
            cardEl.addEventListener('click', () => cardEl.classList.toggle('is-flipped'));
            flashcardsContent.appendChild(cardEl);
        });
    }

    function renderQuiz(quiz) {
        quizContent.innerHTML = '';
        if (!quiz || quiz.length === 0) {
            quizContent.innerHTML = '<p>No quiz available.</p>';
            return;
        }
        quiz.forEach((q, index) => {
            const questionEl = document.createElement('div');
            questionEl.className = 'question';
            
            let optionsHTML = q.options.map(opt => 
                `<li class="quiz-option" data-answer="${q.answer}">${opt}</li>`
            ).join('');

            questionEl.innerHTML = `<p>${index + 1}. ${q.question}</p><ul>${optionsHTML}</ul>`;
            quizContent.appendChild(questionEl);
        });

        // Add event listeners to new quiz options
        document.querySelectorAll('.quiz-option').forEach(option => {
            option.addEventListener('click', handleQuizOptionClick);
        });
    }

    // --- Event Handlers ---
    function handleSubjectClick(subjectName) {
        document.querySelectorAll('#subject-tiles .tile').forEach(tile => {
            if (tile.textContent === subjectName) {
                tile.classList.add('active');
            } else {
                tile.classList.remove('active');
            }
        });
        renderSubjectContent(subjectName);
    }

    function handleQuizOptionClick(e) {
        const selectedOption = e.target;
        const correctAnswer = selectedOption.dataset.answer;
        const isCorrect = selectedOption.textContent === correctAnswer;

        // Disable further clicks on this question
        const parentList = selectedOption.parentElement;
        parentList.querySelectorAll('.quiz-option').forEach(opt => {
            opt.removeEventListener('click', handleQuizOptionClick);
            opt.style.pointerEvents = 'none'; // Disable pointer events
            // Show correct answer
            if (opt.textContent === correctAnswer) {
                opt.classList.add('correct');
            }
        });

        if (!isCorrect) {
            selectedOption.classList.add('incorrect');
        }
    }

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        showLoading(true);

        const subject = subjectInput.value.trim();
        if (!subject) {
            showError('Please enter a subject name.');
            showLoading(false);
            return;
        }

        const formData = new FormData();
        formData.append('subject', subject);
        let endpoint = '/api/process/';

        if (activeTab === 'file') {
            if (fileInput.files.length === 0) {
                showError('Please select a file.');
                showLoading(false);
                return;
            }
            formData.append('file', fileInput.files[0]);
            endpoint += 'file';
        } else {
            if (youtubeInput.value.trim() === '') {
                showError('Please enter a YouTube URL.');
                showLoading(false);
                return;
            }
            formData.append('url', youtubeInput.value.trim());
            endpoint += 'youtube';
        }

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'An unknown error occurred.');
            }

            // Refresh subjects and display the new one
            await fetchSubjects();
            renderSubjectTiles();
            handleSubjectClick(subject);
            uploadForm.reset();

        } catch (error) {
            showError(error.message);
        } finally {
            showLoading(false);
        }
    });

    qaForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = qaInput.value.trim();
        if (!question || !currentSubject) return;

        const qaButton = qaForm.querySelector('button');
        qaButton.disabled = true;
        qaResponse.classList.remove('hidden');
        qaResponse.innerHTML = '<p>Thinking...</p>';

        const formData = new FormData();
        formData.append('subject', currentSubject);
        formData.append('question', question);

        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to get an answer.');
            }

            const data = await response.json();
            qaResponse.innerHTML = `<p>${data.answer.replace(/\n/g, '<br>')}</p>`;

        } catch (error) {
            qaResponse.innerHTML = `<p style="color: var(--error-color);">${error.message}</p>`;
        } finally {
            qaButton.disabled = false;
            qaInput.value = '';
        }
    });

    // --- Utility Functions ---
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
        setTimeout(() => errorMessage.classList.add('hidden'), 5000);
    }

    function showLoading(isLoading, element = loadingSpinner) {
        if (isLoading) {
            element.classList.remove('hidden');
            submitButton.disabled = true;
        } else {
            element.classList.add('hidden');
            submitButton.disabled = false;
        }
    }

    window.showTab = (tabName) => {
        activeTab = tabName;
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-link').forEach(link => link.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');
        document.querySelector(`.tab-link[onclick="showTab('${tabName}')"]`).classList.add('active');
    };

    // --- Initial Load ---
    init();
});