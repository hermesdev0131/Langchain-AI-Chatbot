let isFirstOpen = true; // Added FAQ flag
const MAX_RECORDING_TIME = 10 * 1000; // 10 seconds limit
const COOLDOWN_TIME = 5000; // 5 seconds cooldown
let isRecording = false;
let mediaRecorder;
let audioChunks = [];
let mediaStream;


function toggleChat() {
  const popup = document.getElementById('chatPopup');
  const isVisible = popup.classList.contains('show');

  if (isVisible) {
    // Start fade-out animation
    popup.classList.add('fade-out');

    // Listen for transition end to hide the popup once
    popup.addEventListener('transitionend', handleFadeOut, { once: true });

    const micButton = document.getElementById("record-btn");
    if (micButton) {
      micButton.addEventListener("click", toggleRecording);
    }
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

    // Load chat history when the chat is opened
    loadChatHistory();

    // Added FAQ display logic
    if (isFirstOpen) {
      displayFAQs();
      isFirstOpen = false;
    }
  }
}

async function toggleRecording() {
  const micButton = document.getElementById("record-btn");

  if (!isRecording) {
    await startRecording();
    micButton.style.backgroundColor = "red"; // Indicate recording
  } else {
    stopRecording();
    micButton.style.backgroundColor = "#FFC300"; // Reset button color

    // Disable the button during cooldown
    micButton.disabled = true;
    setTimeout(() => {
      micButton.disabled = false;
    }, COOLDOWN_TIME);
  }
}

// Start recording audio using MediaRecorder API
async function startRecording() {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(mediaStream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      await sendAudioToServer(audioBlob);
      stopMicrophoneStream(); // Release microphone after recording
    };

    mediaRecorder.start();
    isRecording = true;
    console.log("Recording started...");

    // Automatically stop recording after MAX_RECORDING_TIME
    setTimeout(() => {
      if (isRecording) {
        stopRecording();
        document.getElementById("record-btn").style.backgroundColor = "#FFC300"; // Reset button color
      }
    }, MAX_RECORDING_TIME);

  } catch (error) {
    alert("Error accessing microphone: " + error.message);
  }
}

// Stop recording and send to server
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    isRecording = false;
    console.log("Recording stopped.");
  }
}

// Release microphone after recording stops
function stopMicrophoneStream() {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop()); // Stop all audio tracks
  }
}

// Send audio file to server for transcription
async function sendAudioToServer(audioBlob) {
  const formData = new FormData();
  formData.append("file", audioBlob, "audio.webm");

  try {
    const response = await fetch('/api/transcribe', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    if (data.transcript) {
      document.getElementById("chatInput").value = data.transcript;
      sendMessage(); // Auto-send the transcribed message
    } else {
      console.error("Transcription failed:", data);
    }
  } catch (error) {
    console.error("Error sending audio to server:", error);
  }
}

async function displayFAQs() {
  const chatBody = document.getElementById('chatBody');
  try {
    // Fetch FAQ questions from the backend endpoint
    const response = await fetch('/api/faqs');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const faqQuestions = await response.json();

    // Create the FAQ container element with an ID for easy updating
    const faqContainer = document.createElement('div');
    faqContainer.className = 'faq-container';
    faqContainer.id = 'faq-container';

    // Create language dropdown container with a label (no persistent search display)
    const languageDiv = document.createElement('div');
    languageDiv.className = 'faq-language-dropdown';
    languageDiv.innerHTML = `
      <select id="faq-language" onchange="switchFaqLanguage()">
        <option value="en" selected>English</option>
        <option value="es">Español</option>
        <option value="fr">Français</option>
        <option value="de">Deutsch</option>
        <option value="zh">中文</option>
        <option value="ja">日本語</option>
        <option value="ru">Русский</option>
        <option value="ar">العربية</option>
        <option value="vi">Tiếng Việt</option>
        <option value="ko">한국어</option>
        <option value="hi">हिन्दी</option>
      </select>
    `;
    faqContainer.appendChild(languageDiv);

    // Create a container for the FAQ questions
    const faqQuestionsContainer = document.createElement('div');
    faqQuestionsContainer.id = 'faq-questions';
    faqQuestions.forEach(questionObj => {
      const question = typeof questionObj === 'string' ? questionObj : questionObj.question;
      const faqDiv = document.createElement('div');
      faqDiv.className = 'faq-question';
      faqDiv.innerHTML = `
        <div class="faq-icon">
          <i class="fas fa-comment-dots"></i>
        </div>
        <div class="faq-text" onclick="sendFAQ('${question}')">${question}</div>
      `;
      faqQuestionsContainer.appendChild(faqDiv);
    });
    faqContainer.appendChild(faqQuestionsContainer);

    // Append the FAQ container to the chat body
    chatBody.appendChild(faqContainer);
    scrollToBottom();

    // Initialize Select2 on the language dropdown with search disabled.
    if (window.$ && typeof $('#faq-language').select2 === 'function') {
      $('#faq-language').select2({
        minimumResultsForSearch: Infinity, // disable the search box
        width: 'resolve'
      });
    }
  } catch (error) {
    console.error("Error fetching FAQs:", error);
  }
}

async function switchFaqLanguage() {
  const langDropdown = document.getElementById("faq-language");
  const selectedLang = langDropdown.value;
  try {
    const response = await fetch(`/api/faqs/translate?lang=${selectedLang}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const translatedFaqs = await response.json();

    // Build new HTML for FAQ questions only.
    let newFaqQuestionsHtml = '';
    translatedFaqs.forEach(faq => {
      // Escape single quotes to avoid breaking the onclick handler.
      const escapedFaq = faq.replace(/'/g, "\\'");
      newFaqQuestionsHtml += `
        <div class="faq-question">
          <div class="faq-icon">
            <i class="fas fa-comment-dots"></i>
          </div>
          <div class="faq-text" onclick="sendFAQ('${escapedFaq}')">${faq}</div>
        </div>
      `;
    });

    // Update only the FAQ questions container.
    const faqQuestionsContainer = document.getElementById("faq-questions");
    if (faqQuestionsContainer) {
      faqQuestionsContainer.innerHTML = newFaqQuestionsHtml;
    } else {
      console.warn("FAQ questions container not found!");
    }
  } catch (error) {
    console.error("Error switching FAQ language:", error);
  }
}

function sendFAQ(question) {
  const input = document.getElementById('chatInput');
  input.value = question;
  sendMessage();
}

function updateSearchDisplay(e) {
  const currentValueDisplay = document.getElementById('current-search-value');
  if (currentValueDisplay) {
    currentValueDisplay.textContent = 'Search: ' + e.target.value;
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
  }
}

// Toggle color change of various sections
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

document.getElementById("close-notification").addEventListener("click", function () {
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
  // Save the message to sessionStorage
  saveChatHistory(message, 'user');

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

      // Save the message to sessionStorage
      saveChatHistory(data.response, 'bot');
    } else {
      addMessage('Sorry, something went wrong.', 'bot');

      // Save the message to sessionStorage
      saveChatHistory('Sorry, something went wrong.', 'bot');
    }
  } catch (err) {
    // Hide "Thinking..." and show error
    thinkingDiv.classList.add('hidden');
    addMessage('Error: ' + err.message, 'bot');

    // Save the message to sessionStorage
    saveChatHistory('Error: ' + err.message, 'bot');
  }
}

// Scroll to Bottom Function
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
    icon.src = "https://cdn-icons-png.flaticon.com/512/3870/3870822.png";
    icon.height = 30;
    icon.weight = 30;
  }
  else {
    icon.src = "https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/wichita.sidearmsports.com/images/responsive_2023/logo_main.svg";
    icon.height = 30;
    icon.weight = 30;
  }
  const labelDiv = document.createElement('div');
  labelDiv.className = 'chatbot__label';
  labelDiv.textContent = sender === 'user' ? 'You' : 'Shocker Assistant';

  const textDiv = document.createElement('div');
  textDiv.className = 'chatbot__text';
  if (sender === "bot") {
    textDiv.innerHTML = replaceLinks(content);
  } else {
    textDiv.textContent = content;
  }

  iconContainer.appendChild(icon);
  messageDiv.appendChild(iconContainer);
  messageDiv.appendChild(labelDiv);
  messageDiv.appendChild(textDiv);
  chatBody.appendChild(messageDiv);
  scrollToBottom();  // Automatically scroll to bottom
}

function replaceLinks(text) {
  if (!text || typeof text !== 'string' || text.trim() === "") {
    console.error("replaceLinks received empty or invalid text.");
    return "Please try again";
  }
  try {
    const DEBUG = true; // Set to false to disable debugging logs

    // Initial cleanup: remove stray opening parenthesis and whitespace before URLs
    text = text.replace(/\(\s*((https?:\/\/|www\.)[^\s]+)/g, '$1');

    // Helper to determine the MIME type for video links
    function getVideoType(link) {
      if (/\.mp4$/i.test(link)) {
        return "video/mp4";
      } else if (/\.webm$/i.test(link)) {
        return "video/webm";
      } else if (/\.ogg$/i.test(link)) {
        return "video/ogg";
      } else {
        return "";
      }
    }

    // Helper to extract a YouTube video ID from a URL
    function getYoutubeVideoId(url) {
      const regex = /(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
      const match = url.match(regex);
      if (DEBUG) {
        console.log("getYoutubeVideoId - URL:", url, "ID:", match ? match[1] : "none");
      }
      return match ? match[1] : null;
    }

    // --- Step 1: Process markdown links ---
    text = text.replace(/\[([^\]]+)\]\(([\s\S]+?)\)/g, function (match, linkText, linkContent) {
      let url = linkContent.trim();
      const anchorMatch = url.match(/<a\s+[^>]*href="([^"]+)"[^>]*>/i);
      if (anchorMatch) {
        url = anchorMatch[1];
        if (DEBUG) {
          console.log("Extracted URL from anchor tag:", url);
        }
      }
      url = url.trim().replace(/^\(|\)$/g, '').replace(/[\)\.,!?]+$/g, '');
      const youtubeVideoId = getYoutubeVideoId(url);
      if (youtubeVideoId) {
        const iframeHTML = `<iframe width="560" height="315" src="https://www.youtube.com/embed/${youtubeVideoId}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="max-width: 100%; border-radius: 8px; margin-top: 5px;"></iframe>`;
        if (DEBUG) {
          console.log("Markdown - Detected YouTube link:", url, "Embedding as iframe:", iframeHTML);
        }
        return iframeHTML;
      }
      if (/\.(mp4|webm|ogg)$/i.test(url)) {
        const videoHTML = `<video controls style="max-width: 100%; height: auto; border-radius: 8px; margin-top: 5px;">
                                    <source src="${url}" type="${getVideoType(url)}">
                                    Your browser does not support the video tag.
                               </video>`;
        if (DEBUG) {
          console.log("Markdown - Detected video file:", url, "Embedding as video:", videoHTML);
        }
        return videoHTML;
      }
      if (DEBUG) {
        console.log("Markdown - No video detected for URL:", url);
      }
      return match;
    });

    // --- Step 2: Process raw URLs in plain text segments only ---
    const parts = text.split(/(<[^>]+>)/);
    for (let i = 0; i < parts.length; i++) {
      if (!parts[i].startsWith("<")) {
        parts[i] = parts[i].replace(/((https?:\/\/|www\.)[^\s]+)/g, function (match) {
          match = match.trim().replace(/^\(+/, '');
          match = match.replace(/[\)\.,!?]+$/g, '');
          let link = match;
          if (!link.startsWith('http')) {
            link = 'http://' + link;
          }
          const youtubeVideoId = getYoutubeVideoId(link);
          if (youtubeVideoId) {
            const iframeHTML = `<iframe width="560" height="315" src="https://www.youtube.com/embed/${youtubeVideoId}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="max-width: 100%; border-radius: 8px; margin-top: 5px;"></iframe>`;
            return iframeHTML;
          }
          if (/\.(jpeg|jpg|png|gif|bmp|webp)$/i.test(link)) {
            const imgHTML = `<img src="${link}" alt="Image" style="max-width: 100%; height: auto; border-radius: 8px; margin-top: 5px;">`;
            return imgHTML;
          }
          if (/\.(mp4|webm|ogg)$/i.test(link)) {
            const videoHTML = `<video controls style="max-width: 100%; height: auto; border-radius: 8px; margin-top: 5px;">
                                <source src="${link}" type="${getVideoType(link)}">
                                Your browser does not support the video tag.
                           </video>`;
            return videoHTML;
          }
          const anchorHTML = `<a href="${link}" target="_blank" rel="noopener noreferrer" style="color: #0000FF; text-decoration: underline">
                            <img src="static/icons/redirect-grad.png" alt="External Link" style="width: 20px; height: 20px; vertical-align: middle;">
                            <img src="static/icons/open-eye-grad.png" alt="External Link" style="width: 22px; height: 22px; vertical-align: middle; cursor: pointer;" onclick="toggleLinkText(event, this, '${link}')">
                            <span class="hidden-link-text" style="display: none; margin-left: 5px;">${link}</span>
                        </a>`;
          return anchorHTML;
        });
      }
    }
    return parts.join("");
  } catch (error) {
    console.error("Error in replaceLinks:", error);
    return "Please try again";
  }
}

function toggleLinkText(event, imgElement, link) {
  event.preventDefault(); // Prevents navigation when clicking the image
  const span = imgElement.nextElementSibling; // Get the span next to the image

  if (span.style.display === 'none' || span.style.display === '') {
    span.style.display = 'inline';
    imgElement.src = "static/icons/close-eye-grad.png"; // Change to another image
  } else {
    span.style.display = 'none';
    imgElement.src = "static/icons/open-eye-grad.png"; // Change back to original image
  }
}

function typeWriterEffect(text, chatBody) {
  const formattedText = replaceLinks(text);
  const plainText = text.replace(/https?:\/\/[^\s]+/g, "");

  const messageDiv = document.createElement('div');
  messageDiv.className = 'chatbot__message chatbot__message--bot';

  const iconContainer = document.createElement('div');
  iconContainer.className = 'chatbot__icon-container';

  const labelDiv = document.createElement('div');
  labelDiv.className = 'chatbot__label';
  labelDiv.textContent = "Shocker Assistant";

  const textDiv = document.createElement('div');
  textDiv.className = 'chatbot__text';
  textDiv.innerHTML = "";  // Start empty, will be filled dynamically

  const icon = document.createElement('img');
  icon.src = "https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/wichita.sidearmsports.com/images/responsive_2023/logo_main.svg";
  icon.height = 30;
  icon.weight = 30;
  iconContainer.appendChild(icon);

  messageDiv.appendChild(iconContainer);
  messageDiv.appendChild(labelDiv);
  messageDiv.appendChild(textDiv);
  chatBody.appendChild(messageDiv);

  let i = 0;

  function type() {
    if (i < plainText.length) {
      textDiv.textContent += plainText.charAt(i);
      i++;
      scrollToBottom();
      setTimeout(type, 5);  // Adjust speed here if needed
    } else {
      textDiv.innerHTML = formattedText;
    }
  }

  type();  // Start the effect
}

document.addEventListener('click', function (event) {
  const popup = document.getElementById('chatPopup');
  const chatbotButton = document.querySelector('.chatbot__button');
  const micButton = document.getElementById("record-btn");

  // If popup is not visible, do nothing
  if (!popup.classList.contains('show')) return;

  // Check if the clicked element is inside the popup or the chatbot button
  if (!popup.contains(event.target) && !chatbotButton.contains(event.target)) {
    // Start fade-out animation
    popup.classList.add('fade-out');

    // Listen for transition end to hide the popup once
    popup.addEventListener('transitionend', handleFadeOut, { once: true });

    // Remove microphone event listener when chat is closed
    if (micButton.hasAttribute("listener")) {
      micButton.removeEventListener("click", toggleRecording);
      micButton.removeAttribute("listener");
    }
  } else {
    // Add microphone event listener only if chat is open and not already added
    if (!micButton.hasAttribute("listener")) {
      micButton.addEventListener("click", toggleRecording);
      micButton.setAttribute("listener", "true");
    }
  }
});

// Function to save chat history to sessionStorage
function saveChatHistory(message, sender) {
  let chatHistory = JSON.parse(sessionStorage.getItem('chatHistory')) || [];
  chatHistory.push({ content: message, sender: sender });
  sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));
}

// Function to load chat history from sessionStorage
function loadChatHistory() {
  const chatHistory = JSON.parse(sessionStorage.getItem('chatHistory')) || [];
  const chatBody = document.getElementById('chatBody');

  chatHistory.forEach(message => {
    addMessage(message.content, message.sender);
  });
}
