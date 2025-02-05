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

function toggleColorChange() {
    let count = parseInt(localStorage.getItem('count'), 10) || 0;
    if (count === 0 || count % 2 !== 0) { 
        document.getElementById('body').style.backgroundColor = '#3c3a3a';
        document.getElementById('hero').style.backgroundColor = '#FFC300';
        document.getElementById('features-section').style.backgroundColor = '#3c3a3a';
        localStorage.setItem('count', count + 1); 
    } else {
        document.getElementById('body').style.backgroundColor = 'white';
        document.getElementById('hero').style.backgroundColor = 'white';
        document.getElementById('features-section').style.backgroundColor = '#151313';
        localStorage.setItem('count', count + 1);
    }
}

document.getElementById("close-notification").addEventListener("click", function() {
    document.getElementById("chatbot-notification").style.display = "none";
  });
  

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

//Scroll to Bottom Function
function scrollToBottom() {
    const chatBody = document.getElementById('chatBody');
    chatBody.scrollTop = chatBody.scrollHeight;
}

// Add user's or bot's message to the chat
function addMessage(content, sender) {
    const chatBody = document.getElementById('chatBody');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot__message chatbot__message--${sender}`;

    const iconContainer = document.createElement('div');
    iconContainer.className = 'chatbot__icon-container';

    const icon = document.createElement('img');
    if (sender === 'user') {
        icon.src = "https://cdn-icons-png.flaticon.com/512/3870/3870822.png"
        icon.height = 30;
        icon.weight  = 30;
    }
    const labelDiv = document.createElement('div');
    labelDiv.className = 'chatbot__label';
    labelDiv.textContent = sender === 'user' ? 'You' : 'Shocker Assistant';

    const textDiv = document.createElement('div');
    textDiv.className = 'chatbot__text';
    textDiv.textContent = content;


    
    // Just Added
    if (sender === "bot") {
      textDiv.innerHTML = makeLinksClickable(content);
    } else {
      textDiv.textContent = content;
    }



    iconContainer.appendChild(icon);
    messageDiv.appendChild(iconContainer)
    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(textDiv);
    chatBody.appendChild(messageDiv);
    scrollToBottom();  // Automatically scroll to bottom
}





// Function to detect URLs in text and convert them into clickable links
function makeLinksClickable(text) {
    // This pattern looks for URLs starting with http(s):// or www.,
    // followed by non-whitespace characters.
    const urlPattern = /((https?:\/\/|www\.)[^\s]+)/g;
  
    return text.replace(urlPattern, function (match) {
      // Check if the URL ends with punctuation (like ., !, ?, etc.)
      // We'll specifically look for .?!, etc. Adjust if you want to
      // include or exclude other punctuation.
      let trailingPunctuation = '';
      const punctMatch = match.match(/[.,!?(){}\[\];:"'<>\s]+$/);
  
      if (punctMatch) {
        trailingPunctuation = punctMatch[0];         // e.g. "."
        // Remove trailing punctuation from the URL for the link
        match = match.slice(0, -trailingPunctuation.length);
      }
  
      // Construct the link. If it doesn't start with http, prepend it.
      let link = match;
      if (!match.startsWith('http')) {
        link = 'http://' + match;
      }
  
      // Return the clickable link plus any trailing punctuation that was removed.
      return `<a href="${link}" target="_blank" rel="noopener noreferrer" style="color: #0000FF; text-decoration: underline">${match}</a>${trailingPunctuation}`;
    });
  }
  




function typeWriterEffect(text, chatBody) {
    const words = text.split(' '); // Split text into words
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chatbot__message chatbot__message--bot';
    const iconContainer = document.createElement('div');
    iconContainer.className = 'chatbot__icon-container';
    
  
    const labelDiv = document.createElement('div');
    labelDiv.className = 'chatbot__label';
    labelDiv.textContent = "AI Assistant"; // Just Added
    
    messageDiv.appendChild(iconContainer) 
    const textDiv = document.createElement('div');
    textDiv.className = 'chatbot__text';
    labelDiv.textContent = 'Shocker Assistant';      
    textDiv.innerHTML = ""; // Will be populated letter by letter (Just Added)                                                                                                                     
    
    const icon = document.createElement('img');
    icon.src = "https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/wichita.sidearmsports.com/images/responsive_2023/logo_main.svg"
    icon.height = 30;
    icon.weight  = 30;
    iconContainer.appendChild(icon);
    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(textDiv);
    chatBody.appendChild(messageDiv);

    let formattedText = makeLinksClickable(text);  // Just added
    let i = 0;
    function type() {
        if (i < text.length) {
            textDiv.textContent += text.charAt(i);
            i++;
            // Scroll to the bottom gradually as text is typed
            scrollToBottom();
            setTimeout(type, 10); // Adjust typing speed here
        } else {
            textDiv.innerHTML = formattedText; // Ensure final result includes links (Just Added)
          }
    }
    type();
}

function scrollToBottom() {
    const chatBody = document.getElementById('chatBody');
    chatBody.scrollTop = chatBody.scrollHeight;
}

// Attach the click event listener once when the script loads
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







