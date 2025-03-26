(() => {
  // Constants and state variables
  const MAX_RECORDING_TIME = 10000; // 10 seconds
  const COOLDOWN_TIME = 5000; // 5 seconds cooldown
  let isRecording = false;
  let isFirstOpen = true;
  let mediaRecorder, mediaStream;
  let audioChunks = [];

  // Cache DOM elements
  const chatPopup = document.getElementById('chatPopup');
  const chatInput = document.getElementById('chatInput');
  const chatBody = document.getElementById('chatBody');
  const recordBtn = document.getElementById('record-btn');
  const thinkingDiv = document.getElementById('chatbot-thinking');
  const closeNotification = document.getElementById("close-notification");

  // upload document button
  const uploadBtn = document.getElementById("uploadDocumentButton");
  const uploadInput = document.getElementById("uploadFileInput");


  // Toggle chat popup
  function toggleChat() {
    const isVisible = chatPopup.classList.contains('show');
    if (isVisible) {
      chatPopup.classList.add('fade-out');
      chatPopup.addEventListener('transitionend', handleFadeOut, { once: true });
    } else {
      chatPopup.classList.remove('fade-out');
      chatPopup.style.display = 'flex';
      void chatPopup.offsetWidth; // force reflow
      chatPopup.classList.add('show');
      setTimeout(() => chatInput.focus(), 300);
      if (isFirstOpen) {
        displayFAQs();
        isFirstOpen = false;
      }
    }
  }

  // Toggle recording state
  async function toggleRecording() {
    if (!isRecording) {
      await startRecording();
      recordBtn.style.backgroundColor = "red";
    } else {
      stopRecording();
      recordBtn.style.backgroundColor = "#FFC300";
      recordBtn.disabled = true;
      setTimeout(() => (recordBtn.disabled = false), COOLDOWN_TIME);
    }
  }

  // Start audio recording
  async function startRecording() {
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Initialize RecordRTC to record audio as WAV
      recorder = RecordRTC(mediaStream, {
        type: 'audio',
        mimeType: 'audio/wav',
        recorderType: StereoAudioRecorder, // Use StereoAudioRecorder
        desiredSampRate: 16000,            // Set sample rate to 16 kHz
        numberOfAudioChannels: 1           // Record mono audio
      });
      recorder.startRecording();
      isRecording = true;
      console.log("Recording started...");

      // Auto-stop after the max time limit
      setTimeout(() => {
        if (isRecording) {
          stopRecording();
          recordBtn.style.backgroundColor = "#FFC300";
        }
      }, MAX_RECORDING_TIME);

    } catch (error) {
      alert("Error accessing microphone: " + error.message);
    }
  }

  // Stop audio recording
  async function stopRecording() {
    if (recorder) {
      await recorder.stopRecording(() => {
        const audioBlob = recorder.getBlob();
        sendAudioToServer(audioBlob);
        stopMicrophoneStream();
      });
      isRecording = false;
      console.log("Recording stopped.");
    }
  }

  // Stop all audio tracks
  function stopMicrophoneStream() {
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
    }
  }

  // Send recorded audio to server for transcription
  async function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append("file", audioBlob, "audio.wav");
    try {
      const response = await fetch(`${apiBaseUrl}/transcribe`, {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      if (data.transcript) {
        chatInput.value = data.transcript;
        sendMessage();
      } else {
        console.error("Transcription failed:", data);
      }
    } catch (error) {
      console.error("Error sending audio to server:", error);
    }
  }

// Display FAQs from server
async function displayFAQs() {
  try {
    const response = await fetch(`${apiBaseUrl}/faqs`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const faqData = await response.json();
    console.log(faqData);

    const faqQuestions = Array.isArray(faqData) ? faqData : [];

    const faqContainer = document.createElement('div');
    faqContainer.className = 'faq-container';
    faqContainer.id = 'faq-container';

    const languageDiv = document.createElement('div');
    languageDiv.className = 'faq-language-dropdown';
    languageDiv.innerHTML = `
      <select id="faq-language" onchange="switchFaqLanguage()">
        <option value="en" selected>English</option>
        <option value="es">Español</option>
        <option value="vi">Tiếng Việt</option>
        <option value="fr">Français</option>
        <option value="de">Deutsch</option>
        <option value="zh">中文</option>
        <option value="ja">日本語</option>
        <option value="ru">Русский</option>
        <option value="ar">العربية</option>
        <option value="ko">한국어</option>
        <option value="hi">हिन्दी</option>
        <option value="bn">বাংলা</option>
      </select>
    `;
    faqContainer.appendChild(languageDiv);

    const faqQuestionsContainer = document.createElement('div');
    faqQuestionsContainer.id = 'faq-questions';
    const fragment = document.createDocumentFragment();

    faqQuestions.forEach(faqObj => {
      // If faqObj is an object with a heading, use that; otherwise, use faqObj directly.
      const question = (typeof faqObj === 'object' && faqObj.heading) ? faqObj.heading : faqObj;
      
      const faqDiv = document.createElement('div');
      faqDiv.className = 'faq-question';
      faqDiv.addEventListener('click', event => {
        event.stopPropagation();
        sendFAQ(question);
      });
      
      const iconDiv = document.createElement('div');
      iconDiv.className = 'faq-icon';
      iconDiv.innerHTML = '<i class="fas fa-comment-dots"></i>';
      faqDiv.appendChild(iconDiv);
      
      const textDiv = document.createElement('div');
      textDiv.className = 'faq-text';
      textDiv.textContent = question;
      faqDiv.appendChild(textDiv);
      
      fragment.appendChild(faqDiv);
    });

    faqQuestionsContainer.appendChild(fragment);
    faqContainer.appendChild(faqQuestionsContainer);
    chatBody.appendChild(faqContainer);
    scrollToBottom();

    // Initialize language dropdown if using Select2
    if (window.$ && typeof $('#faq-language').select2 === 'function') {
      $('#faq-language').select2({
        minimumResultsForSearch: Infinity,
        width: 'resolve'
      });
    }
  } catch (error) {
    console.error("Error fetching FAQs:", error);
  }
}

// Switch FAQ language by fetching translated questions
async function switchFaqLanguage() {
  const langDropdown = document.getElementById("faq-language");
  const selectedLang = langDropdown.value;
  try {
    const response = await fetch(`${apiBaseUrl}/faqs/translate?lang=${selectedLang}`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const translatedFaqs = await response.json();
    const faqQuestionsContainer = document.getElementById("faq-questions");
    faqQuestionsContainer.innerHTML = '';
    const fragment = document.createDocumentFragment();
    translatedFaqs.forEach(faq => {
      // Expecting faq to be the translated heading
      const faqDiv = document.createElement('div');
      faqDiv.className = 'faq-question';
      faqDiv.addEventListener('click', event => {
        event.stopPropagation();
        sendFAQ(faq);
      });
      const iconDiv = document.createElement('div');
      iconDiv.className = 'faq-icon';
      iconDiv.innerHTML = '<i class="fas fa-comment-dots"></i>';
      faqDiv.appendChild(iconDiv);
      const textDiv = document.createElement('div');
      textDiv.className = 'faq-text';
      textDiv.textContent = faq;
      faqDiv.appendChild(textDiv);
      fragment.appendChild(faqDiv);
    });
    faqQuestionsContainer.appendChild(fragment);
  } catch (error) {
    console.error("Error switching FAQ language:", error);
  }
}


  // Send FAQ question as a chat message
  function sendFAQ(question) {
    chatInput.value = question;
    sendMessage();
  }

  // Handle fade-out transition of the popup
  function handleFadeOut(event) {
    if (event.propertyName === 'opacity') {
      chatPopup.style.display = 'none';
      chatPopup.classList.remove('show', 'fade-out', 'fullscreen');
    }
  }

  // Toggle fullscreen mode for chat
  function toggleFullscreen() {
    const isFullscreen = chatPopup.classList.toggle('fullscreen');
    if (isFullscreen) chatInput.focus();
  }

  // Toggle color theme and update localStorage counter
  function toggleColorChange() {
    let count = parseInt(localStorage.getItem('count'), 10) || 0;
    if (count === 0 || count % 2 !== 0) {
      document.getElementById('body').style.backgroundColor = '#3c3a3a';
      document.getElementById('hero').style.backgroundColor = '#FFC300';
      document.getElementById('features-section').style.backgroundColor = '#3c3a3a';
    } else {
      document.getElementById('body').style.backgroundColor = 'white';
      document.getElementById('hero').style.backgroundColor = 'white';
      document.getElementById('features-section').style.backgroundColor = '#151313';
    }
    localStorage.setItem('count', count + 1);
  }

  // Close chatbot notification
  closeNotification.addEventListener("click", () => {
    document.getElementById("chatbot-notification").style.display = "none";
  });

  // Handle Enter key press to send message
  function handleEnterKey(event) {
    if (event.key === 'Enter') sendMessage();
  }

  // Send chat message to server
  async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    addMessage(message, 'user');
    chatInput.value = '';
    thinkingDiv.classList.remove('hidden');
    try {
      const response = await fetch(`${apiBaseUrl}/qa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userMessage: message }),
      });
      const data = await response.json();
      thinkingDiv.classList.add('hidden');
      if (data.response) {
        if (data.response.error) {
          const errorMsg = data.response.error === 'API request timed out'
            ? 'The API request timed out. Please try again.'
            : 'Error: ' + data.response.error;
          addMessage(errorMsg, 'bot');
        } else {
          typeWriterEffect(data.response);
        }
      } else {
        const errMsg = 'Sorry, something went wrong.';
        addMessage(errMsg, 'bot');
      }
    } catch (err) {
      thinkingDiv.classList.add('hidden');
      addMessage('Error: ' + err.message, 'bot');
    }
  }

  // Scroll chat to bottom
  function scrollToBottom() {
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  // Add a message to the chat
  function addMessage(content, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot__message chatbot__message--${sender}`;
    const labelDiv = document.createElement('div');
    labelDiv.className = 'chatbot__label';
    labelDiv.textContent = 'You';
    const textDiv = document.createElement('div');
    textDiv.innerHTML = sender === "bot" ? replaceLinks(content) : content;
    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(textDiv);
    chatBody.appendChild(messageDiv);
    scrollToBottom();
  }

  // Replace raw URLs and markdown links with embedded content
  function replaceLinks(text) {
    if (!text || typeof text !== 'string' || text.trim() === "") {
      console.error("replaceLinks received empty or invalid text.");
      return "Please try again";
    }
    try {
      const DEBUG = false; // Disable debugging logs in production
      text = text.replace(/\(\s*((https?:\/\/|www\.)[^\s]+)/g, '$1');

      // Helper functions
      const getVideoType = link => {
        if (/\.mp4$/i.test(link)) return "video/mp4";
        if (/\.webm$/i.test(link)) return "video/webm";
        if (/\.ogg$/i.test(link)) return "video/ogg";
        return "";
      };

      const getYoutubeVideoId = url => {
        const regex = /(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
        const match = url.match(regex);
        if (DEBUG) console.log("getYoutubeVideoId - URL:", url, "ID:", match ? match[1] : "none");
        return match ? match[1] : null;
      };

      // Process markdown links
      text = text.replace(/\[([^\]]+)\]\(([\s\S]+?)\)/g, (match, linkText, linkContent) => {
        let url = linkContent.trim();
        const anchorMatch = url.match(/<a\s+[^>]*href="([^"]+)"[^>]*>/i);
        if (anchorMatch) {
          url = anchorMatch[1];
          if (DEBUG) console.log("Extracted URL from anchor tag:", url);
        }
        url = url.trim().replace(/^\(|\)$/g, '').replace(/[\)\.,!?]+$/g, '');
        const youtubeVideoId = getYoutubeVideoId(url);
        if (youtubeVideoId) {
          return `<iframe width="560" height="315" src="https://www.youtube.com/embed/${youtubeVideoId}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="max-width: 100%; border-radius: 8px; margin-top: 5px;"></iframe>`;
        }
        if (/\.(mp4|webm|ogg)$/i.test(url)) {
          return `<video controls style="max-width: 100%; height: auto; border-radius: 8px; margin-top: 5px;">
                    <source src="${url}" type="${getVideoType(url)}">
                    Your browser does not support the video tag.
                  </video>`;
        }
        return match;
      });

      // Process raw URLs in plain text segments only
      const parts = text.split(/(<[^>]+>)/);
      for (let i = 0; i < parts.length; i++) {
        if (!parts[i].startsWith("<")) {
          parts[i] = parts[i].replace(/((https?:\/\/|www\.)[^\s]+)/g, match => {
            match = match.trim().replace(/^\(+/, '').replace(/[\)\.,!?]+$/g, '');
            let link = match.startsWith('http') ? match : 'http://' + match;
            const youtubeVideoId = getYoutubeVideoId(link);
            if (youtubeVideoId) {
              return `<iframe width="560" height="315" src="https://www.youtube.com/embed/${youtubeVideoId}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="max-width: 100%; border-radius: 8px; margin-top: 5px;"></iframe>`;
            }
            if (/\.(jpeg|jpg|png|gif|bmp|webp)$/i.test(link)) {
              return `<img src="${link}" alt="Image" style="max-width: 100%; height: auto; border-radius: 8px; margin-top: 5px;">`;
            }
            if (/\.(mp4|webm|ogg)$/i.test(link)) {
              return `<video controls style="max-width: 100%; height: auto; border-radius: 8px; margin-top: 5px;">
                        <source src="${link}" type="${getVideoType(link)}">
                        Your browser does not support the video tag.
                      </video>`;
            }
            return `<a href="${link}" target="_blank" rel="noopener noreferrer" style="color: #0000FF; text-decoration: underline">
                      <img src="static/img/icons/redirect-grad.png" alt="External Link" style="width: 20px; height: 20px; vertical-align: middle;">
                      <img src="static/img/icons/open-eye-grad.png" alt="External Link" style="width: 22px; height: 22px; vertical-align: middle; cursor: pointer;" onclick="toggleLinkText(event, this, '${link}')">
                      <span class="hidden-link-text" style="display: none; margin-left: 5px;">${link}</span>
                    </a>`;
          });
        }
      }
      return parts.join("");
    } catch (error) {
      console.error("Error in replaceLinks:", error);
      return "Please try again";
    }
  }

  // Expose toggleLinkText to global scope for inline onclick usage
  window.toggleLinkText = function(event, imgElement, link) {
    event.preventDefault();
    const span = imgElement.nextElementSibling;
    if (span.style.display === 'none' || span.style.display === '') {
      span.style.display = 'inline';
      imgElement.src = "static/img/icons/close-eye-grad.png";
    } else {
      span.style.display = 'none';
      imgElement.src = "static/img/icons/open-eye-grad.png";
    }
  };

  // Typewriter effect for bot response
  function typeWriterEffect(text) {
    const formattedText = replaceLinks(marked.parse(text));
    const plainText = text.replace(/https?:\/\/[^\s]+/g, "");
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chatbot__message chatbot__message--bot';
    const labelDiv = document.createElement('div');
    labelDiv.className = 'chatbot__label';
    labelDiv.textContent = window.CHATBOT_NAME;
    const textDiv = document.createElement('div');
    textDiv.className = 'chatbot__message';
    textDiv.innerHTML = "";
    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(textDiv);
    chatBody.appendChild(messageDiv);
    let i = 0;
    function type() {
      if (i < plainText.length) {
        textDiv.textContent += plainText.charAt(i);
        i++;
        scrollToBottom();
        setTimeout(type, 5);
      } else {
        textDiv.innerHTML = formattedText;
        const buttonsContainer = document.createElement('div');
        buttonsContainer.className = 'chatbot__buttons';
        const copyButton = document.createElement('button');
        copyButton.className = 'btn-copy';
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        copyButton.addEventListener('click', () => {
          navigator.clipboard.writeText(text);
          copyButton.classList.add('btn-clicked');
          setTimeout(() => {
            copyButton.classList.remove('btn-clicked');
          }, 1000); // Change back to original color after 1 second
        });
        buttonsContainer.appendChild(copyButton);

        const likeButton = document.createElement('button');
        likeButton.className = 'btn-like';
        likeButton.innerHTML = '<i class="fas fa-thumbs-up"></i>';
        likeButton.addEventListener('click', () => {
          // TODO: Implement like functionality
          likeButton.classList.add('btn-clicked');
          setTimeout(() => {
            likeButton.classList.remove('btn-clicked');
          }, 1000); // Change back to original color after 1 second
        });
        buttonsContainer.appendChild(likeButton);

        const dislikeButton = document.createElement('button');
        dislikeButton.className = 'btn-dislike';
        dislikeButton.innerHTML = '<i class="fas fa-thumbs-down"></i>';
        dislikeButton.addEventListener('click', () => {
          // TODO: Implement like functionality;
          dislikeButton.classList.add('btn-clicked');
          setTimeout(() => {
            dislikeButton.classList.remove('btn-clicked');
          }, 1000); // Change back to original color after 1 second
        });
        buttonsContainer.appendChild(dislikeButton);
        messageDiv.appendChild(buttonsContainer);
      }
    }
    type();
  }

  // Global click listener to fade out chat popup when clicking outside
  document.addEventListener('click', event => {
    const chatbotButton = document.querySelector('.chatbot__button');
    if (!chatPopup.classList.contains('show')) return;
    if (!chatPopup.contains(event.target) && !chatbotButton.contains(event.target)) {
      chatPopup.classList.add('fade-out');
      chatPopup.addEventListener('transitionend', handleFadeOut, { once: true });
    }
  });

  uploadBtn.addEventListener("click", () => {
    uploadInput.click();
  });

  uploadInput.addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (file) {
      try {
        const formData = new FormData();
        formData.append("file", file);
        const response = await fetch(`${apiBaseUrl}/ingest`, {
          method: "POST",
          body: formData
        });
        const data = await response.json();
        if (data.status === "success") {
          alert("Document ingested successfully!");
        } else {
          alert("Ingestion failed: " + data.detail);
        }
      } catch (error) {
        console.error("Error uploading document:", error);
        alert("Error uploading document.");
      }
      // Clear the input so the same file can be re-selected if needed
      uploadInput.value = "";
    }
  });

  // Register event listeners once during initialization
  if (recordBtn) recordBtn.addEventListener("click", toggleRecording);
  if (chatInput) chatInput.addEventListener('keypress', handleEnterKey);

  // Expose functions to global scope if needed
  window.toggleChat = toggleChat;
  window.toggleFullscreen = toggleFullscreen;
  window.toggleColorChange = toggleColorChange;
  window.switchFaqLanguage = switchFaqLanguage;
  window.sendMessage = sendMessage;
})();
