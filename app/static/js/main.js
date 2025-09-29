document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element Selectors ---
    const container = document.getElementById('container');
    const sidebar = document.getElementById('sidebar');
    const collapseBtn = document.getElementById('collapse-btn');
    const openBtn = document.getElementById('open-btn');
    const subjectList = document.getElementById('subject-list');
    const chatTitle = document.getElementById('chat-title');
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const pdfViewerContainer = document.getElementById('pdf-viewer-container');
    const viewerPlaceholder = document.getElementById('viewer-placeholder');
    const pdfCanvas = document.getElementById('pdf-canvas');
    const pdfControls = document.getElementById('pdf-controls');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const pageNumSpan = document.getElementById('page-num');
    const pageCountSpan = document.getElementById('page-count');

    // --- State Management ---
    let currentSubjectName = null;
    let activeFileElement = null;
    let pdfDoc = null;
    let currentPageNum = 1;
    let pageIsRendering = false;
    let pageNumIsPending = null;

    // --- Core Functions ---

    /**
     * Fetches subjects and files from the API and populates the sidebar.
     */
    const fetchSubjects = async () => {
        try {
            const response = await fetch('/api/subjects');
            if (!response.ok) throw new Error('Network response was not ok');
            const subjects = await response.json();
            
            subjectList.innerHTML = ''; // Clear loading text
            for (const subjectName in subjects) {
                const details = document.createElement('details');
                details.className = 'subject-details';
                
                const summary = document.createElement('summary');
                summary.className = 'subject-summary';
                summary.textContent = subjectName.replace(/_/g, ' ');
                
                const fileList = document.createElement('ul');
                fileList.className = 'file-list';
                
                subjects[subjectName].forEach(file => {
                    const fileItem = document.createElement('li');
                    fileItem.className = 'file-item';
                    const link = document.createElement('a');
                    link.href = '#';
                    link.textContent = file.name;
                    link.dataset.subjectName = subjectName;
                    link.dataset.fileName = file.name; // Store filename for fetching
                    
                    link.addEventListener('click', handleFileSelection);
                    
                    fileItem.appendChild(link);
                    fileList.appendChild(fileItem);
                });
                
                details.appendChild(summary);
                details.appendChild(fileList);
                subjectList.appendChild(details);
            }
        } catch (error) {
            subjectList.innerHTML = '<p class="error-text">Failed to load subjects.</p>';
            console.error('Error fetching subjects:', error);
        }
    };

    /**
     * Adds a message to the chat window.
     * @param {string} sender - 'user' or 'bot'
     * @param {string} text - The message content
     * @param {boolean} isThinking - Optional flag for bot's thinking state
     */
    const addMessage = (sender, text, isThinking = false) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        if (isThinking) {
            messageDiv.classList.add('thinking');
            messageDiv.id = 'thinking-message';
        }

        if (sender === 'bot') {
            const botAvatar = document.createElement('img');
            botAvatar.src = "/static/logo.png";
            botAvatar.alt = "Bot";
            botAvatar.className = "avatar";
            messageDiv.appendChild(botAvatar);
        }

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = text;
        messageDiv.appendChild(messageContent);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll to bottom
    };

    // --- PDF Viewer Functions ---

    /**
     * Renders a specific page of the PDF onto the canvas.
     * @param {number} num - The page number to render.
     */
    const renderPage = async (num) => {
        pageIsRendering = true;
        
        const page = await pdfDoc.getPage(num);
        
        const viewport = page.getViewport({ scale: 1.5 });
        const canvasContext = pdfCanvas.getContext('2d');
        pdfCanvas.height = viewport.height;
        pdfCanvas.width = viewport.width;

        const renderContext = { canvasContext, viewport };
        await page.render(renderContext).promise;

        pageIsRendering = false;

        pageNumSpan.textContent = num;
        prevPageBtn.disabled = num <= 1;
        nextPageBtn.disabled = num >= pdfDoc.numPages;

        if (pageNumIsPending !== null) {
            renderPage(pageNumIsPending);
            pageNumIsPending = null;
        }
    };

    /**
     * Queues a page to be rendered to prevent conflicts.
     * @param {number} num - The page number to queue.
     */
    const queueRenderPage = (num) => {
        if (pageIsRendering) {
            pageNumIsPending = num;
        } else {
            renderPage(num);
        }
    };

    /**
     * Loads a PDF from a URL and initializes the viewer.
     * @param {string} subjectName - The name of the subject folder.
     * @param {string} fileName - The name of the PDF file.
     */
    const loadPdf = async (subjectName, fileName) => {
        const url = `/notes/${subjectName}/${fileName}`;
        pdfDoc = null;
        currentPageNum = 1;

        viewerPlaceholder.style.display = 'flex';
        pdfControls.style.display = 'none';

        try {
            const loadingTask = pdfjsLib.getDocument(url);
            pdfDoc = await loadingTask.promise;
            
            pdfControls.style.display = 'block';
            viewerPlaceholder.style.display = 'none';
            pageCountSpan.textContent = pdfDoc.numPages;

            renderPage(currentPageNum);
        } catch (error) {
            console.error('Error loading PDF:', error);
            viewerPlaceholder.innerHTML = '<p>Failed to load document.</p>';
            viewerPlaceholder.style.display = 'flex';
            pdfControls.style.display = 'none';
        }
    };


    // --- Event Handlers ---

    /**
     * Handles the click event on a file link.
     */
    const handleFileSelection = (e) => {
        e.preventDefault();
        const link = e.target;
        currentSubjectName = link.dataset.subjectName;
        const fileName = link.dataset.fileName;

        if (activeFileElement) {
            activeFileElement.classList.remove('active');
        }
        link.classList.add('active');
        activeFileElement = link;
        
        const subjectTitle = currentSubjectName.replace(/_/g, ' ');
        chatTitle.textContent = `Chatting with: ${fileName}`;
        chatMessages.innerHTML = '';
        addMessage('bot', `You've selected ${fileName}. How can I help you with this document?`);
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.placeholder = `Ask a question about ${subjectTitle}...`;
        userInput.focus();

        if (fileName.toLowerCase().endsWith('.pdf')) {
            loadPdf(currentSubjectName, fileName);
        } else {
            viewerPlaceholder.innerHTML = '<p>Live view is only available for PDF files.</p>';
            viewerPlaceholder.style.display = 'flex';
            pdfControls.style.display = 'none';
            pdfCanvas.height = 0; // Clear canvas
        }
    };

    /**
     * Handles the chat form submission.
     */
    const handleFormSubmit = async (e) => {
        e.preventDefault();
        const query = userInput.value.trim();
        if (!query || !currentSubjectName) return;

        addMessage('user', query);
        userInput.value = '';
        addMessage('bot', 'Sahayak is thinking...', true);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ subject_name: currentSubjectName, query: query }),
            });

            const thinkingMessage = document.getElementById('thinking-message');
            if (thinkingMessage) thinkingMessage.remove();

            if (!response.ok) throw new Error('API response was not ok.');

            const data = await response.json();
            addMessage('bot', data.answer);
        } catch (error) {
            const thinkingMessage = document.getElementById('thinking-message');
            if (thinkingMessage) thinkingMessage.remove();
            addMessage('bot', 'Sorry, I encountered an error. Please try again.');
            console.error('Error in chat submission:', error);
        }
    };

    // --- Initializations and Event Listeners ---
    chatForm.addEventListener('submit', handleFormSubmit);
    
    prevPageBtn.addEventListener('click', () => {
        if (currentPageNum <= 1) return;
        currentPageNum--;
        queueRenderPage(currentPageNum);
    });

    nextPageBtn.addEventListener('click', () => {
        if (currentPageNum >= pdfDoc.numPages) return;
        currentPageNum++;
        queueRenderPage(currentPageNum);
    });

    collapseBtn.addEventListener('click', () => {
        container.classList.add('sidebar-collapsed');
    });

    openBtn.addEventListener('click', () => {
        container.classList.remove('sidebar-collapsed');
    });

    fetchSubjects();
});