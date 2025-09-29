document.addEventListener('DOMContentLoaded', () => {
    const subjectList = document.getElementById('subject-list');
    const chatTitle = document.getElementById('chat-title');
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Store the subject name instead of doc ID
    let currentSubjectName = null;
    let activeFileElement = null;

    const fetchSubjects = async () => {
        try {
            const response = await fetch('/api/subjects');
            if (!response.ok) throw new Error('Network response was not ok');
            const subjects = await response.json();
            
            subjectList.innerHTML = '';
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
                    // Store subject_name in the dataset
                    link.dataset.subjectName = subjectName; 
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
        }
    };

    const addMessage = (sender, text, isThinking = false) => {
        // ... (This function does not need to be changed) ...
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
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const handleFileSelection = (e) => {
        e.preventDefault();
        const link = e.target;
        // Get the subject name from the link's dataset
        currentSubjectName = link.dataset.subjectName;

        if (activeFileElement) activeFileElement.classList.remove('active');
        link.classList.add('active');
        activeFileElement = link;
        
        const subjectTitle = currentSubjectName.replace(/_/g, ' ');
        chatTitle.textContent = `Chatting with: Subject - ${subjectTitle}`;
        chatMessages.innerHTML = '';
        addMessage('bot', `You've selected the ${subjectTitle} subject. How can I help you?`);
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.placeholder = `Ask a question about ${subjectTitle}...`;
        userInput.focus();
    };

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
                // Send subject_name in the payload
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
        }
    };

    chatForm.addEventListener('submit', handleFormSubmit);
    fetchSubjects();
});