document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element Selectors ---
    const subjectList = document.getElementById('subject-list');
    const chatTitle = document.getElementById('chat-title');
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    let currentDocId = null;
    let activeFileElement = null;

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
                    link.dataset.docId = file.id;
                    link.dataset.docName = file.name;
                    
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

        let contentHTML = '';
        if (sender === 'bot') {
            const botAvatar = document.createElement('img');
            botAvatar.src = "/static/logo.png"; // Make sure logo.png is in static folder
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

    // --- Event Handlers ---

    /**
     * Handles the click event on a file link.
     */
    const handleFileSelection = (e) => {
        e.preventDefault();
        const link = e.target;
        currentDocId = link.dataset.docId;
        const docName = link.dataset.docName;

        // Update UI for active selection
        if (activeFileElement) {
            activeFileElement.classList.remove('active');
        }
        link.classList.add('active');
        activeFileElement = link;
        
        // Update chat interface
        chatTitle.textContent = `Chatting with: ${docName}`;
        chatMessages.innerHTML = ''; // Clear previous messages
        addMessage('bot', `You've selected ${docName}. How can I help you with this document?`);
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.placeholder = `Ask a question about ${docName}...`;
        userInput.focus();
    };

    /**
     * Handles the chat form submission.
     */
    const handleFormSubmit = async (e) => {
        e.preventDefault();
        const query = userInput.value.trim();
        if (!query || !currentDocId) return;

        addMessage('user', query);
        userInput.value = ''; // Clear input field immediately
        addMessage('bot', 'Sahayak is thinking...', true); // Show thinking indicator
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ doc_id: currentDocId, query: query }),
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

    // --- Initializations ---
    chatForm.addEventListener('submit', handleFormSubmit);
    fetchSubjects();
});