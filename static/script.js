const messagesDiv = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const stopBtn = document.getElementById('stop-btn');
const printBtn = document.getElementById('print-btn');
const clearBtn = document.getElementById('clear-btn');

let isGenerating = false;
let abortController = null;
let chatHistory = []; // Array of {role: 'user'|'bot', content: '...'}

// Auto-resize textarea
userInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Handle Enter key
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

stopBtn.addEventListener('click', () => {
    if (abortController) {
        abortController.abort();
        isGenerating = false;
        toggleInputState(false);
    }
});

printBtn.addEventListener('click', () => {
    window.print();
});

clearBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear the conversation?')) {
        const intro = messagesDiv.querySelector('.intro');
        messagesDiv.innerHTML = '';
        if (intro) messagesDiv.appendChild(intro);
        chatHistory = []; // Reset history
    }
});

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isGenerating) return;

    // Reset UI
    userInput.value = '';
    userInput.style.height = 'auto';
    toggleInputState(true);

    // Add User Message to UI and History
    addMessage(text, 'user');
    chatHistory.push({ role: 'user', content: text });
    scrollToBottom();

    // Add Typing Indicator
    const typingId = addTypingIndicator();
    scrollToBottom();

    // Setup Abort Controller
    abortController = new AbortController();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: text,
                history: chatHistory.slice(0, -1) // Send previous history
            }),
            signal: abortController.signal
        });

        // Remove Typing Indicator
        removeMessage(typingId);

        if (!response.ok) {
            throw new Error('Network error');
        }

        // Create Bot Message Container
        const botMsgContent = addMessage('', 'bot');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            botMsgContent.textContent += chunk;
            fullResponse += chunk;
            scrollToBottom();
        }

        // Add Bot Message to History
        chatHistory.push({ role: 'bot', content: fullResponse });

    } catch (error) {
        removeMessage(typingId);
        if (error.name === 'AbortError') {
            const stopMsg = "Generation stopped by user.";
            addMessage(`_${stopMsg}_`, 'bot');
            chatHistory.push({ role: 'bot', content: `[${stopMsg}]` });
        } else {
            addMessage("Sorry, I encountered an error. Please try again.", 'bot');
            console.error(error);
        }
    } finally {
        isGenerating = false;
        abortController = null;
        toggleInputState(false);
    }
}

function addMessage(text, type) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (text) {
        contentDiv.textContent = text;
    }

    msgDiv.appendChild(contentDiv);
    messagesDiv.appendChild(msgDiv);

    return type === 'bot' ? contentDiv : msgDiv;
}

function addTypingIndicator() {
    const id = 'typing-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot';
    msgDiv.id = id;

    msgDiv.innerHTML = `
        <div class="typing">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    messagesDiv.appendChild(msgDiv);
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function scrollToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function toggleInputState(generating) {
    isGenerating = generating;
    if (generating) {
        sendBtn.classList.add('hidden');
        stopBtn.classList.remove('hidden');
        userInput.placeholder = "Generating response...";
    } else {
        sendBtn.classList.remove('hidden');
        stopBtn.classList.add('hidden');
        userInput.placeholder = "Ask a question...";
        userInput.focus();
    }
}
