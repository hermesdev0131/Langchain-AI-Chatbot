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

  // Dynamically load Font Awesome for icons if not already loaded
  (function loadFontAwesome() {
    const existing = document.querySelector('link[href*="font-awesome"], link[href*="fontawesome"]');
    if (!existing) {
      const fa = document.createElement("link");
      fa.rel = "stylesheet";
      fa.href = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css";
      fa.crossOrigin = "anonymous";
      document.head.appendChild(fa);
    }
  })();

  // Display FAQs from server
  async function displayFAQs() {
    try {
      const response = await fetch(`${apiBaseUrl}/faqs`);
      const faqData = await response.json();

      const faqContainer = document.createElement('div');
      faqContainer.className = 'faq-container';
      faqContainer.id = 'faq-container';
      
      // Automatically apply theme class based on FAQ structure
      const isSubHeadingsStyle = Array.isArray(faqData) && typeof faqData[0] === 'object' && faqData[0].heading;
      faqContainer.classList.add(isSubHeadingsStyle ? 'SubHeadings-theme' : 'Headings-theme');

      // Language dropdown
      const languageDiv = document.createElement('div');
      languageDiv.className = 'faq-language-dropdown';
      languageDiv.innerHTML = `
        <select id="faq-language" onchange="switchFaqLanguage()">
          <option value="en" selected>English</option>
          <option value="es">Español</option>
          <option value="vi">Tiếng Việt</option>
          <option value="fr">Français</option>
          <option value="de">Deutsch</option>
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
      const fragment = document.createDocumentFragment(); // Create a DocumentFragment

      faqData.forEach((faq, index) => {
        const isFlat = typeof faq === "string";

        if (isFlat) {
          const questionDiv = document.createElement('div');
          questionDiv.className = 'faq-subquestion';
          questionDiv.innerHTML = `
            <div class="faq-icon"><i class="fas fa-comment-dots"></i></div>
            <div class="faq-text">${faq}</div>
          `;
          questionDiv.addEventListener('click', () => sendFAQ(faq));
          fragment.appendChild(questionDiv); // Append to fragment
        } else {
          const accordionItem = document.createElement('div');
          accordionItem.className = 'faq-accordion-item';

          const header = document.createElement('div');
          header.className = 'faq-accordion-header';
          header.innerHTML = `
            <div class="faq-icon rotate-icon" id="arrow-${index}">
              <i class="fas fa-chevron-down"></i>
            </div>
            <div class="faq-text">${faq.heading}</div>
          `;

          const content = document.createElement('div');
          content.className = 'faq-accordion-content';
          content.style.display = 'none';

          faq.subheading.forEach(sub => {
            const subDiv = document.createElement('div');
            subDiv.className = 'faq-subquestion';
            subDiv.innerHTML = `
              <div class="faq-icon"><i class="fas fa-comment-dots"></i></div>
              <div class="faq-text">${sub}</div>
            `;
            subDiv.addEventListener('click', event => {
              event.stopPropagation();
              sendFAQ(sub);
            });
            content.appendChild(subDiv);
          });

          header.addEventListener('click', () => {
            const isVisible = content.style.display === 'block';
            const allContents = document.querySelectorAll('.faq-accordion-content');
            const allIcons = document.querySelectorAll('.rotate-icon i');

            allContents.forEach(c => (c.style.display = 'none'));
            allIcons.forEach(icon => icon.style.transform = 'rotate(0deg)');

            if (!isVisible) {
              content.style.display = 'block';
              const iconEl = document.querySelector(`#arrow-${index} i`);
              iconEl.style.transform = 'rotate(180deg)';
            }
          });

          accordionItem.appendChild(header);
          accordionItem.appendChild(content);
          fragment.appendChild(accordionItem); // Append to fragment
        }
      });
      faqQuestionsContainer.appendChild(fragment); // Append fragment to container

      faqContainer.appendChild(faqQuestionsContainer);
      chatBody.appendChild(faqContainer);
      scrollToBottom();

      // Initialize language dropdown if using Select2
      if (window.$ && typeof $('#faq-language').select2 === 'function') {
        $('#faq-language').select2({ minimumResultsForSearch: Infinity, width: 'resolve' });
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
      const faqContainer = document.getElementById("faq-container");
      const faqQuestionsContainer = document.getElementById("faq-questions");

      // Show loading
      faqQuestionsContainer.innerHTML = '<div class="loading-message">Loading... Please wait</div>';

      const response = await fetch(`${apiBaseUrl}/faqs/translate?lang=${selectedLang}`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const translatedFaqs = await response.json();

      // Clear old content
      faqQuestionsContainer.innerHTML = '';
      const fragment = document.createDocumentFragment(); // Create a DocumentFragment

      // Remove old theme and apply correct one
      faqContainer.classList.remove('SubHeadings-theme', 'Headings-theme');
      const isSubHeadingsStyle = Array.isArray(translatedFaqs) && typeof translatedFaqs[0] === 'object' && translatedFaqs[0].heading;
      faqContainer.classList.add(isSubHeadingsStyle ? 'SubHeadings-theme' : 'Headings-theme');

      // Render questions
      translatedFaqs.forEach((faq, index) => {
        const accordionItem = document.createElement('div');
        accordionItem.className = 'faq-accordion-item';

        if (typeof faq === 'string') {
          // Flat Headings-style question
          const questionDiv = document.createElement('div');
          questionDiv.className = 'faq-subquestion';
          questionDiv.innerHTML = `
            <div class="faq-icon"><i class="fas fa-comment-dots"></i></div>
            <div class="faq-text">${faq}</div>
          `;
          questionDiv.addEventListener('click', () => sendFAQ(faq));
          fragment.appendChild(questionDiv); // Append to fragment
        } else if (faq.heading) {
          // SubHeadings-style question with subheadings
          const header = document.createElement('div');
          header.className = 'faq-accordion-header';
          header.innerHTML = `
            <div class="faq-icon rotate-icon" id="arrow-${index}">
              <i class="fas fa-chevron-down"></i>
            </div>
            <div class="faq-text">${faq.heading}</div>
          `;

          const content = document.createElement('div');
          content.className = 'faq-accordion-content';
          content.style.display = 'none';

          faq.subheading.forEach(sub => {
            const subDiv = document.createElement('div');
            subDiv.className = 'faq-subquestion';
            subDiv.innerHTML = `
              <div class="faq-icon"><i class="fas fa-comment-dots"></i></div>
              <div class="faq-text">${sub}</div>
            `;
            subDiv.addEventListener('click', event => {
              event.stopPropagation();
              sendFAQ(sub);
            });
            content.appendChild(subDiv);
          });

          header.addEventListener('click', () => {
            const isVisible = content.style.display === 'block';
            const allContents = document.querySelectorAll('.faq-accordion-content');
            const allIcons = document.querySelectorAll('.rotate-icon i');

            allContents.forEach(c => (c.style.display = 'none'));
            allIcons.forEach(icon => icon.style.transform = 'rotate(0deg)');

            if (!isVisible) {
              content.style.display = 'block';
              const iconEl = document.querySelector(`#arrow-${index} i`);
              iconEl.style.transform = 'rotate(180deg)';
            }
          });

          accordionItem.appendChild(header);
          accordionItem.appendChild(content);
          fragment.appendChild(accordionItem); // Append to fragment
        }
      });
      faqQuestionsContainer.appendChild(fragment); // Append fragment to container
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

      thinkingDiv.classList.add('hidden'); // Hide thinking indicator as soon as server responds

      if (!response.ok) {
        if (response.status === 429) {
          // Display user-requested message for 429 errors from the /qa route
          addMessage("Too many requests. Please try again later.", 'bot');
        } else {
          // Handle other HTTP errors (e.g., 500, 400, 401, etc.)
          let errorDetailMessage = `Error: ${response.status}`;
          try {
            // Attempt to parse error details from JSON response
            const errorData = await response.json();
            if (errorData && (errorData.detail || errorData.message)) {
              errorDetailMessage = errorData.detail || errorData.message;
            } else if (typeof errorData === 'string') {
              errorDetailMessage = errorData;
            } else {
              // Fallback if JSON is not structured as expected or is not a string
              errorDetailMessage = await response.text(); // Try to get raw text
            }
          } catch (e) {
            // If response is not JSON, try to get raw text
            try {
              errorDetailMessage = await response.text();
              if (!errorDetailMessage.trim()) { // If text is empty, use statusText
                errorDetailMessage = response.statusText || 'An unexpected error occurred.';
              }
            } catch (e_text) {
              // If getting text also fails, use statusText
              errorDetailMessage = response.statusText || 'An unexpected error occurred.';
            }
          }
          addMessage(`Error: ${response.status} - ${errorDetailMessage}`, 'bot');
        }
        return; // Stop further processing for non-ok responses
      }

      // If response.ok is true, proceed to parse JSON
      const data = await response.json();
      
      if (data.response) {
        if (data.response.error) {
          // Handle application-level errors returned in a 200 OK response
          const errorMsg = data.response.error === 'API request timed out'
            ? 'The API request timed out. Please try again.'
            : 'Error: ' + data.response.error;
          addMessage(errorMsg, 'bot');
        } else {
          // Successful response with answer
          typeWriterEffect(data.response);
        }
      } else {
        // Response is 200 OK, but the expected 'data.response' structure is missing
        addMessage('Sorry, the response from the server was not in the expected format.', 'bot');
      }
    } catch (err) {
      // Catches network errors (e.g., server down) or errors from response.json() if malformed
      thinkingDiv.classList.add('hidden');
      addMessage('Network error or issue processing the request: ' + err.message, 'bot');
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
    labelDiv.textContent = sender === 'user' ? 'You' : window.CHATBOT_NAME || 'Bot'; // Use CHATBOT_NAME for bot
    const textDiv = document.createElement('div');
    // For bot messages, parse markdown then replace links. For user messages, display as is (or sanitize).
    textDiv.innerHTML = sender === "bot" ? replaceLinks(marked.parse(content)) : content;
    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(textDiv);
    chatBody.appendChild(messageDiv);
    scrollToBottom();
  }

  // Helper: transform a YouTube URL into its embed form.
  function getYoutubeEmbedUrl(url) {
    const regex = /(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
    const match = url.match(regex);
    return match ? `https://www.youtube.com/embed/${match[1]}` : url;
  }

  // Helper: returns an iframe embed for known providers; otherwise, returns a plain clickable link.
  function embedUrl(url) {
    // Automatically embed YouTube links.
    if (url.includes("youtube.com") || url.includes("youtu.be")) {
      return `<iframe width="560" height="315" src="${getYoutubeEmbedUrl(url)}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="max-width: 100%; border-radius: 8px; margin-top: 5px;"></iframe>`;
    }

    // Embed direct video links using HTML5 <video> tag
    const videoExtensions = /\.(mp4|webm|ogv)$/i;
    if (videoExtensions.test(url)) {
      const typeMatch = url.match(videoExtensions);
      // Ensure typeMatch is not null and has the captured group for the extension
      const extension = typeMatch && typeMatch[1] ? typeMatch[1].toLowerCase() : 'mp4'; // Default to mp4 if somehow extension capture fails
      const videoType = `video/${extension === 'ogv' ? 'ogg' : extension}`;
      return `<video controls width="560" height="315" style="max-width: 100%; border-radius: 8px; margin-top: 5px;"><source src="${url}" type="${videoType}">Your browser does not support the video tag.</video>`;
    }

    // Embed direct image links using HTML <img> tag
    const imageExtensions = /\.(jpeg|jpg|gif|png|webp|svg)$/i;
    if (imageExtensions.test(url)) {
      // Extract filename for alt text, or use a generic alt text
      const filename = url.substring(url.lastIndexOf('/') + 1);
      const altText = filename ? `Image: ${decodeURIComponent(filename)}` : "Displayed image";
      return `<img src="${url}" alt="${altText}" style="max-width: 100%; height: auto; border-radius: 8px; margin-top: 5px;">`;
    }

    return `<a href="${url}" target="_blank" rel="noopener noreferrer" style="color: #0000FF; text-decoration: underline;">${url}</a>`;
  }

  // Helper: returns a plain clickable link (without embedding) regardless of provider.
  function plainLink(url) {
    return `<a href="${url}" target="_blank" rel="noopener noreferrer" style="color: #0000FF; text-decoration: underline;">${url}</a>`;
  }

  // Main function: process both markdown-style links and raw URLs.
  function replaceLinks(text) {
    if (!text || typeof text !== 'string' || text.trim() === "") {
      console.error("replaceLinks received empty or invalid text.");
      return "Please try again";
    }
    try {
      // Phase 1: Handle [embed] keyword transformations on the HTML string
      // Remove any extraneous parentheses around URLs that might have been missed.
      text = text.replace(/\(\s*((https?:\/\/|www\.)[^\s]+)/g, '$1');

      // Process [embed] <a href="url">text</a> -> iframe + plainLink
      text = text.replace(
        /\[embed\]\s*(<a\s+href="([^"]+)"[^>]*>[\s\S]*?<\/a>)/gi,
        (_, fullAnchor, url) => {
          url = url.trim();
          // Use a generic iframe for [embed] <a...> as the URL could be anything
          return `<iframe width="660" height="415" src="${url}" frameborder="0" allowfullscreen style="max-width: 100%; margin-top: 5px;"></iframe><br>${plainLink(url)}`;
        }
      );

      // Process [embed] raw_url -> iframe + plainLink
      text = text.replace(
        /\[embed\][\s:]*((https?:\/\/|www\.)[^\s<]+)/gi,
        (_, urlMatch) => {
          let url = urlMatch.trim().replace(/^\(+/, '').replace(/[\)\.,!?]+$/g, '');
          url = url.startsWith('http') ? url : 'http://' + url;
          // Use a generic iframe for [embed] raw_url
          return `<iframe width="660" height="415" src="${url}" frameborder="0" allowfullscreen style="max-width: 100%; margin-top: 5px;"></iframe><br>${plainLink(url)}`;
        }
      );

      // Phase 2: DOM-based processing
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = text;

      // Helper to replace a node with HTML string content
      function replaceNodeWithHtml(node, htmlString) {
        if (!node.parentNode) return; // Node already removed or detached
        const fragment = document.createRange().createContextualFragment(htmlString);
        node.parentNode.replaceChild(fragment, node);
      }

      // Process <a> tags: style them or replace with video/YouTube/image embeds if appropriate
      const anchors = Array.from(tempDiv.querySelectorAll('a')); // Use a static array for safe iteration
      anchors.forEach(anchor => {
        if (!anchor.parentNode) return; // Node might have been replaced by a previous operation

        const href = anchor.href;
        // Define extensions for different media types
        const imageExtensions = /\.(jpeg|jpg|gif|png|webp|svg)$/i;
        const videoExtensions = /\.(mp4|webm|ogv)$/i;
        
        const isImageHref = imageExtensions.test(href);
        const isVideoHref = videoExtensions.test(href);
        const isYouTubeHref = href.includes("youtube.com") || href.includes("youtu.be");

        // Check if the anchor's content is already a media element (img, video, iframe)
        const containsMediaElement = anchor.querySelector('img, video, iframe');

        if ((isImageHref || isVideoHref || isYouTubeHref) && !containsMediaElement) {
          // If href points to a media type and the anchor doesn't already contain such media,
          // replace the anchor with the direct embed (e.g., <img>, <video>, <iframe>).
          replaceNodeWithHtml(anchor, embedUrl(href));
        } else {
          // For all other <a> tags (including those that might already contain media,
          // or those whose href is not a special media type), ensure they are styled as standard links
          // if they aren't already.
          const anchorStyle = window.getComputedStyle(anchor);
          const isAlreadyStyled = 
            (anchorStyle.color === 'rgb(0, 0, 255)' || anchorStyle.color === 'blue') && // Check for blue color
            anchorStyle.textDecorationLine.includes('underline') &&
            anchor.target === '_blank'; // Check if it opens in a new tab

          if (!isAlreadyStyled) {
            anchor.style.color = "#0000FF"; // Standard link blue
          anchor.style.textDecoration = "underline";
          anchor.target = "_blank";
          anchor.rel = "noopener noreferrer";
          }
        }
      });

      // Process raw URLs in text nodes
      function processTextNodeForRawUrls(node) {
        const urlRegex = /((https?:\/\/|www\.)[^\s<]+)/gi;
        let match;
        const fragments = [];
        let lastIndex = 0;
        const nodeValue = node.nodeValue;

        while ((match = urlRegex.exec(nodeValue)) !== null) {
          if (match.index > lastIndex) {
            fragments.push(document.createTextNode(nodeValue.substring(lastIndex, match.index)));
          }
          let url = match[0].trim().replace(/^\(+/, '').replace(/[\)\.,!?]+$/g, '');
          url = url.startsWith('http') ? url : 'http://' + url;

          const embedHtml = embedUrl(url);
          const embedFragment = document.createRange().createContextualFragment(embedHtml);
          fragments.push(embedFragment);
          lastIndex = urlRegex.lastIndex;
        }

        if (lastIndex < nodeValue.length) {
          fragments.push(document.createTextNode(nodeValue.substring(lastIndex)));
        }

        if (fragments.length > 0 && (fragments.length > 1 || fragments[0].nodeType !== Node.TEXT_NODE || fragments[0].nodeValue !== nodeValue)) {
          const parent = node.parentNode;
          if (parent) {
            fragments.forEach(fragment => parent.insertBefore(fragment, node));
            parent.removeChild(node);
          }
        }
      }

      function walkDOMAndProcessTextNodes(element) {
        const childNodes = Array.from(element.childNodes);
        childNodes.forEach(childNode => {
          if (childNode.nodeType === Node.TEXT_NODE) {
            if (childNode.parentNode &&
              childNode.parentNode.nodeName !== 'A' &&
              childNode.parentNode.nodeName !== 'SCRIPT' &&
              childNode.parentNode.nodeName !== 'STYLE') {
              processTextNodeForRawUrls(childNode);
            }
          } else if (childNode.nodeType === Node.ELEMENT_NODE) {
            if (childNode.nodeName !== 'A' &&
              childNode.nodeName !== 'IFRAME' &&
              childNode.nodeName !== 'VIDEO' &&
              childNode.nodeName !== 'SCRIPT' &&
              childNode.nodeName !== 'STYLE') {
              walkDOMAndProcessTextNodes(childNode);
            }
          }
        });
      }

      walkDOMAndProcessTextNodes(tempDiv);

      return tempDiv.innerHTML;
    } catch (error) {
      console.error("Error in replaceLinks:", error);
      return text; // Return original/partially processed text on error
    }
  }

  // Typewriter effect for bot response
  async function typeWriterEffect(text) {
    // Fully process the markdown and embed links
    // Ensure marked.parse is called on the raw text before replaceLinks
    const htmlFromMarkdown = marked.parse(text);
    const formattedText = replaceLinks(htmlFromMarkdown); // No await needed if replaceLinks is synchronous

    // Create a temporary element to get the exact text content
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = formattedText;
    const plainText = tempDiv.textContent || tempDiv.innerText || "";
  
    // Create the message container
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chatbot__message chatbot__message--bot';
    
    const labelDiv = document.createElement('div');
    labelDiv.className = 'chatbot__label';
    labelDiv.textContent = window.CHATBOT_NAME;
    
    const textDiv = document.createElement('div');
    textDiv.className = 'chatbot__message';
    textDiv.innerHTML = ""; // Start empty
    
    messageDiv.appendChild(labelDiv);
    messageDiv.appendChild(textDiv);
    chatBody.appendChild(messageDiv);
    scrollToBottom();
  
    // Type out the plain text at a constant speed
    let i = 0;
    const TYPING_DELAY_MS = 5; // Increased delay for more stable performance
    const SCROLL_CHARS_INTERVAL = 3; // Scroll every N characters

    function type() {
      if (i < plainText.length) {
        textDiv.textContent += plainText.charAt(i);
        i++;
        if (i % SCROLL_CHARS_INTERVAL === 0 || i === plainText.length) {
          scrollToBottom();
        }
        setTimeout(type, TYPING_DELAY_MS);
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
        scrollToBottom(); // Ensure scrolled correctly after buttons are added
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
        const response = await fetch(`${apiBaseUrl}/ingest_document`, {
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

  // Get the URL input element
  const urlInput = document.getElementById("urlInput");

  // Helper function to validate URL
  function isValidUrl(url) {
    try {
      new URL(url);
      return true;
    } catch (e) {
      return false;
    }
  }

  // Add event listener for keypress on the URL input
  urlInput.addEventListener("keypress", async (event) => {
    if (event.key === "Enter") {
      const url = urlInput.value.trim();
      if (!isValidUrl(url)) {
        alert("Please enter a valid URL.");
        return;
      }
      try {
        const response = await fetch(`${apiBaseUrl}/ingest_url`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ url: url })
        });
        const data = await response.json();
        if (data.status === "success") {
          alert("URL ingested successfully!");
        } else {
          alert("URL ingestion failed: " + data.detail);
        }
      } catch (error) {
        console.error("Error ingesting URL:", error);
        alert("Error ingesting URL.");
      }
      // Clear the input so a new URL can be entered
      urlInput.value = "";
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
