// Function to toggle chatbot visibility with animations
function toggleChat() {
    const popup = document.getElementById('chatPopup');
    const isVisible = popup.classList.contains('show');

    if (isVisible) {
        // Start fade-out animation
        popup.classList.add('fade-out');

        // Listen for transition end to hide the popup once
        popup.addEventListener('transitionend', handleFadeOut, { once: true });
    } else {
        // Remove any existing fade-out class
        popup.classList.remove('fade-out');

        // Show popup and start fade-in animation
        popup.style.display = 'flex';
        // Force reflow to restart the transition
        void popup.offsetWidth;
        popup.classList.add('show');

        // Automatically focus on the input box after transition
        setTimeout(() => {
        document.getElementById('chatInput').focus();
        }, 300); // Match this timeout with the CSS transition duration
    }
    }

    // Handle fade-out transition end
function handleFadeOut(event) {
    const popup = document.getElementById('chatPopup');
    if (event.propertyName === 'opacity') {
        popup.style.display = 'none';
        popup.classList.remove('show', 'fade-out');
    }
}

// Toggle fullscreen mode and focus on input if entering fullscreen
function toggleFullscreen() {
    const popup = document.getElementById('chatPopup');
    const isFullscreen = popup.classList.toggle('fullscreen');

    if (isFullscreen) {
        // Automatically focus on the input box when entering fullscreen
        document.getElementById('chatInput').focus();
    } else {
        // Optionally, you can add actions when exiting fullscreen
    }
}

    // Handle Enter Key Press
function handleEnterKey(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// Send a message to the server
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    // Add user's message (on the left) with label
    addMessage(message, 'user');

    // Clear the input field
    input.value = '';

    // Send message to server
    try {
        const response = await fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userMessage: message })
        });
        const data = await response.json();

        if (data.response) {
        // Bot messages (on the right) with label
        addMessage(data.response, 'bot');
        } else {
        addMessage('Sorry, something went wrong.', 'bot');
        }
    } catch (err) {
        addMessage('Error: ' + err.message, 'bot');
    }
}

// Add a message to the chat with label
function addMessage(content, sender) {
    const chatBody = document.getElementById('chatBody');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot__message chatbot__message--${sender}`;

    // Create label
    const labelDiv = document.createElement('div');
    labelDiv.className = 'chatbot__label';
    labelDiv.textContent = sender === 'user' ? 'You' : 'AI Assistant';

    // Create text content
    const textDiv = document.createElement('div');
    textDiv.className = 'chatbot__text';
    textDiv.textContent = content;

    // Append label and text to message div
    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(textDiv);

    // Append message to chat body
    chatBody.appendChild(messageDiv);

    // Scroll to the bottom
    chatBody.scrollTop = chatBody.scrollHeight;

    // Close chatbot when clicking outside of it with fade-out animation
    document.addEventListener('click', function(event) {
    const popup = document.getElementById('chatPopup');
    const chatbotButton = document.querySelector('.chatbot__button');

    // If popup is not visible, do nothing
    if (!popup.classList.contains('show')) return;

    // Check if the clicked element is inside the popup or the chatbot button
    if (!popup.contains(event.target) && !chatbotButton.contains(event.target)) {
        // Start fade-out animation
        popup.classList.add('fade-out');

        // Listen for transition end to hide the popup once
        popup.addEventListener('transitionend', handleFadeOut, { once: true });
    }
    });
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    const chatBody = document.getElementById('chatBody');
    const thinkingDiv = document.getElementById('chatbot-thinking');}


    // Function to send a message with "Thinking..." and typewriter effect
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    const chatBody = document.getElementById('chatBody');
    const thinkingDiv = document.getElementById('chatbot-thinking');
  
    if (!message) return;
  
    // Add user's message
    addMessage(message, 'user');
    // Clear input and show "Thinking..."
    input.value = '';
    thinkingDiv.classList.remove('hidden');
  
    try {
      const response = await fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userMessage: message }),
      });
      const data = await response.json();
  
      // Hide "Thinking..."
      thinkingDiv.classList.add('hidden');
      if (data.response) {
        // Show response with typewriter effect
        typeWriterEffect(data.response, chatBody);
      } else {
        addMessage('Sorry, something went wrong.', 'bot');
      }
    } catch (err) {
      // Hide "Thinking..." and show error
      thinkingDiv.classList.add('hidden');
      addMessage('Error: ' + err.message, 'bot');
    }
}
  
// Function to simulate typing animation
function typeWriterEffect(text, chatBody) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chatbot__message chatbot__message--bot';
  
    const labelDiv = document.createElement('div');
    labelDiv.className = 'chatbot__label';
    labelDiv.textContent = 'AI Assistant';
  
    const textDiv = document.createElement('div');
    textDiv.className = 'chatbot__text';
    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(textDiv);
    chatBody.appendChild(messageDiv);
  
    let i = 0;
    function type() {
      if (i < text.length) {
        textDiv.textContent += text.charAt(i);
        i++;
        setTimeout(type, 50); // Adjust typing speed here
      }
    }
    type();
}
  
// Add user's or bot's message to the chat
function addMessage(content, sender) {
    const chatBody = document.getElementById('chatBody');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot__message chatbot__message--${sender}`;

    const labelDiv = document.createElement('div');
    labelDiv.className = 'chatbot__label';
    labelDiv.textContent = sender === 'user' ? 'You' : 'AI Assistant';

    const textDiv = document.createElement('div');
    textDiv.className = 'chatbot__text';
    textDiv.textContent = content;

    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(textDiv);
    chatBody.appendChild(messageDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
}