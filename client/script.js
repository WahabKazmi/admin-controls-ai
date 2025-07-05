const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatBox = document.getElementById('chat-box');

function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = sender;
    msgDiv.textContent = `${sender === 'user' ? 'You' : 'Bot'}: ${text}`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;
    appendMessage('user', message);
    userInput.value = '';
    try {
        const res = await fetch('http://127.0.0.1:8000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await res.json();
        appendMessage('bot', data.response || 'No response');
    } catch (err) {
        appendMessage('bot', 'Error connecting to server.');
    }
});
