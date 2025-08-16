async function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (!message) return;

  const chatBox = document.getElementById("chat-box");

  // Append user's message
  chatBox.innerHTML += `<div class="user"><strong>You:</strong> ${message}</div>`;

  // Show loading message
  const loading = document.createElement("div");
  loading.className = "bot loading";
  loading.innerHTML = `<strong>Bot:</strong> ⏳ Thinking...`;
  chatBox.appendChild(loading);
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });

    const data = await res.json();
    let response = data.response || "⚠️ No response from server";

    // Extract image if present
    let imageTag = "";
    const imgUrlMatch = response.match(/https?:\/\/\S+\.(jpg|jpeg|png|gif)/i);
    if (imgUrlMatch) {
      imageTag = `<br><img src="${imgUrlMatch[0]}" alt="Image" style="max-width: 200px; margin-top: 10px; border-radius: 10px;" />`;
    }

    // Replace loading with actual response
    loading.remove();
    chatBox.innerHTML += `<div class="bot"><strong>Bot:</strong> ${response}${imageTag}</div>`;
  } catch (err) {
    loading.remove();
    chatBox.innerHTML += `<div class="bot error"><strong>Bot:</strong> ❌ Error: ${err.message}</div>`;
  }

  chatBox.scrollTop = chatBox.scrollHeight;
  input.value = "";
}

// Send on Enter key press
document.getElementById("user-input").addEventListener("keydown", function (e) {
  if (e.key === "Enter") {
    sendMessage();
  }
});



// const chatBox = document.getElementById('chat-box');
// const userInput = document.getElementById('user-input');
// const sendBtn = document.getElementById('send-btn');

// // Append messages to chat
// function appendMessage(sender, message) {
//   const msgDiv = document.createElement('div');
//   msgDiv.className = sender === 'user' ? 'user-message' : 'bot-message';
//   msgDiv.innerHTML = message.replace(/\n/g, "<br>"); // allow line breaks
//   chatBox.appendChild(msgDiv);
//   chatBox.scrollTop = chatBox.scrollHeight;
// }

// // Function to insert quick button text into input box
// function setQuickMessage(text) {
//   userInput.value = text; // just insert into the placeholder
//   userInput.focus(); // optional: focus so user can press Enter immediately
// }

// // Send manually via button click
// sendBtn.addEventListener('click', sendMessage);

// // Send via Enter key
// userInput.addEventListener('keypress', function (e) {
//   if (e.key === 'Enter') {
//     sendMessage();
//   }
// });

// // Main send function
// function sendMessage() {
//   const message = userInput.value.trim();
//   if (!message) return;

//   appendMessage('user', message);
//   userInput.value = '';

//   sendToBackend(message);
// }

// // Send to backend API
// function sendToBackend(message) {
//   fetch('http://127.0.0.1:8000/chat', {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify({ message: message })
//   })
//     .then(res => res.json())
//     .then(data => {
//       appendMessage('bot', data.response || '🤖 No response received.');
//     })
//     .catch(err => {
//       console.error(err);
//       appendMessage('bot', '❌ Error connecting to backend.');
//     });
// }

// // Attach event listener for quick buttons
// document.querySelectorAll('.quick-buttons button').forEach(btn => {
//   btn.addEventListener('click', () => {
//     const message = btn.getAttribute('data-message');
//     setQuickMessage(message); // only set in input, don't send yet
//   });
// });
