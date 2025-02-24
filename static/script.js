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

// Updated function to fetch FAQs from the server
async function displayFAQs() {
    const chatBody = document.getElementById('chatBody');
    try {
        // Fetch FAQ questions from the backend endpoint
        const response = await fetch('/api/faqs');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        // Expecting a JSON array of questions (either strings or objects)
        const faqQuestions = await response.json();

        // Create the FAQ container element
        const faqContainer = document.createElement('div');
        faqContainer.className = 'faq-container';

        // Iterate through each question and create a clickable FAQ entry
        faqQuestions.forEach(questionObj => {
            // If your endpoint returns an object, use a property (like questionObj.question)
            // Otherwise, if it's a simple string, use it directly.
            const question = typeof questionObj === 'string' ? questionObj : questionObj.question;
            const faqDiv = document.createElement('div');
            faqDiv.className = 'faq-question';
            faqDiv.innerHTML = `
                <div class="faq-icon">
                    <i class="fas fa-comment-dots"></i>
                </div>
                <div class="faq-text" onclick="sendFAQ('${question}')">${question}</div>
            `;
            faqContainer.appendChild(faqDiv);
        });

        chatBody.appendChild(faqContainer);
        scrollToBottom();
    } catch (error) {
        console.error("Error fetching FAQs:", error);
    }
}

function sendFAQ(question) {
    const input = document.getElementById('chatInput');
    input.value = question;
    sendMessage();
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

// Attach the click event listener once when the script loads
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
        icon.weight = 30;
    }
    else {
        icon.src = "https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/wichita.sidearmsports.com/images/responsive_2023/logo_main.svg"
        icon.height = 30;
        icon.weight = 30;
    }
    const labelDiv = document.createElement('div');
    labelDiv.className = 'chatbot__label';
    labelDiv.textContent = sender === 'user' ? 'You' : 'Shocker Assistant';

    const textDiv = document.createElement('div');
    textDiv.className = 'chatbot__text';
    textDiv.textContent = content;


    if (sender === "bot") {
        textDiv.innerHTML = replaceLinks(content);
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

function replaceLinks(text) {
    const DEBUG = true; // Set to false to disable debugging logs

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
        // Matches youtube.com (watch?v= or embed/) and youtu.be formats.
        const regex = /(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
        const match = url.match(regex);
        if (DEBUG) {
            console.log("getYoutubeVideoId - URL:", url, "ID:", match ? match[1] : "none");
        }
        return match ? match[1] : null;
    }

    // --- Step 1: Process markdown links ---
    // This regex matches markdown links of the form [text](URL)
    text = text.replace(/\[([^\]]+)\]\(([\s\S]+?)\)/g, function(match, linkText, linkContent) {
        let url = linkContent.trim();

        // If linkContent is already an HTML anchor tag, extract the href attribute.
        const anchorMatch = url.match(/<a\s+[^>]*href="([^"]+)"[^>]*>/i);
        if (anchorMatch) {
            url = anchorMatch[1];
            if (DEBUG) {
                console.log("Extracted URL from anchor tag:", url);
            }
        }

        // Check for YouTube link
        const youtubeVideoId = getYoutubeVideoId(url);
        if (youtubeVideoId) {
            const iframeHTML = `<iframe width="560" height="315" src="https://www.youtube.com/embed/${youtubeVideoId}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="max-width: 100%; border-radius: 8px; margin-top: 5px;"></iframe>`;
            if (DEBUG) {
                console.log("Markdown - Detected YouTube link:", url, "Embedding as iframe:", iframeHTML);
            }
            return iframeHTML;
        }

        // Check if URL is a video file
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
        // For non-video URLs, return the original markdown link unchanged.
        return match;
    });

    // --- Step 2: Process raw URLs in plain text segments only ---
    // Split the text into parts: HTML tags and plain text.
    const parts = text.split(/(<[^>]+>)/);
    for (let i = 0; i < parts.length; i++) {
        // Process only parts that are not HTML tags.
        if (!parts[i].startsWith("<")) {
            parts[i] = parts[i].replace(/((https?:\/\/|www\.)[^\s]+)/g, function(match) {
                // Remove trailing punctuation if present.
                let trailingPunctuation = '';
                const punctMatch = match.match(/[.,!?(){}\[\];:"'<>\s]+$/);
                if (punctMatch) {
                    trailingPunctuation = punctMatch[0];
                    match = match.slice(0, -trailingPunctuation.length);
                }

                let link = match;
                if (!link.startsWith('http')) {
                    link = 'http://' + link;
                }

                // Check for YouTube links
                const youtubeVideoId = getYoutubeVideoId(link);
                if (youtubeVideoId) {
                    const iframeHTML = `<iframe width="560" height="315" src="https://www.youtube.com/embed/${youtubeVideoId}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="max-width: 100%; border-radius: 8px; margin-top: 5px;"></iframe>${trailingPunctuation}`;
                    if (DEBUG) {
                        console.log("Raw URL - Detected YouTube link:", link, "Embedding as iframe:", iframeHTML);
                    }
                    return iframeHTML;
                }
                // If the link is an image, return an <img> element.
                if (/\.(jpeg|jpg|png|gif|bmp|webp)$/i.test(link)) {
                    const imgHTML = `<img src="${link}" alt="Image" style="max-width: 100%; height: auto; border-radius: 8px; margin-top: 5px;">${trailingPunctuation}`;
                    if (DEBUG) {
                        console.log("Raw URL - Detected image link:", link, "Embedding as image:", imgHTML);
                    }
                    return imgHTML;
                }
                // If the link is a video file, return a <video> element.
                if (/\.(mp4|webm|ogg)$/i.test(link)) {
                    const videoHTML = `<video controls style="max-width: 100%; height: auto; border-radius: 8px; margin-top: 5px;">
                                            <source src="${link}" type="${getVideoType(link)}">
                                            Your browser does not support the video tag.
                                       </video>${trailingPunctuation}`;
                    if (DEBUG) {
                        console.log("Raw URL - Detected video file:", link, "Embedding as video:", videoHTML);
                    }
                    return videoHTML;
                }
                // Otherwise, return the usual clickable link with icons.
                const anchorHTML = `<a href="${link}" target="_blank" rel="noopener noreferrer" style="color: #0000FF; text-decoration: underline">
                                        <img src="static/icons/redirect-grad.png" alt="External Link" style="width: 20px; height: 20px; vertical-align: middle;">
                                        <img src="static/icons/open-eye-grad.png" alt="External Link" style="width: 22px; height: 22px; vertical-align: middle; cursor: pointer;" onclick="toggleLinkText(event, this, '${link}')">
                                        <span class="hidden-link-text" style="display: none; margin-left: 5px;">${link}</span>
                                    </a>${trailingPunctuation}`;
                if (DEBUG) {
                    console.log("Raw URL - No video or image detected for link:", link, "Returning anchor:", anchorHTML);
                }
                return anchorHTML;
            });
        }
    }

    return parts.join("");
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

function scrollToBottom() {
    const chatBody = document.getElementById('chatBody');
    chatBody.scrollTop = chatBody.scrollHeight;
}
