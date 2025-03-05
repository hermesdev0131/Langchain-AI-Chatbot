# Langflow-AI-Chatbot-Server

An advanced AI chatbot server powered by LangFlow, OpenAI, and Zilliz. This project provides a robust conversational pipeline for document processing, retrieval, response generation, and analytics logging.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Routes--API Endpoints](#routes--api-endpoints)
- [Installation and Setup](#installation-and-setup)
- [Usage](#usage)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Overview

**Langflow-AI-Chatbot-Server** integrates several key technologies to create an interactive, context-aware chatbot:

- **Document Processing:** Loads documents (PDFs, text files, etc.) and splits them into manageable chunks.
- **Embeddings & Retrieval:** Uses OpenAI to generate embeddings from the text chunks and stores them in Zilliz—a vector database—for efficient retrieval.
- **Conversational QA:** Combines retrieved text, conversation history, and prompt templates to generate answers via OpenAI’s language model.
- **Analytics:** Logs user queries into a dedicated Zilliz collection to enable detailed analytics.

## Architecture

The server is structured around several core components:

1. **Server Initialization and API Endpoints**  
   - Utilizes FastAPI to create a server that handles both static file serving and API requests.
   - Incorporates CORS middleware to allow cross-origin requests, making the API accessible to front-end applications.

2. **LangFlow Integration and Conversational Pipeline**  
   - Integrates a multi-step workflow where user messages are processed by the `run_flow` function from the LangFlow API.
   - Maintains conversation context and leverages OpenAI for both embedding generation and response creation.

3. **Zilliz Vector Database Usage**  
   - **Document Embeddings:** Processed documents are converted into embeddings and stored in a primary collection.
   - **User Query Logging:** User queries are stored in a separate Zilliz collection to support data analytics.
   - **FAQ Handling:** The server can fetch FAQs from a dedicated Zilliz collection and translate them when necessary.

4. **Audio Transcription**  
   - Provides an endpoint for transcribing audio files using OpenAI Whisper.
   - Implements rate limiting and file size constraints to manage audio transcription requests.

## Routes--API Endpoints

### Static Content & Navigation

- **GET /**  
  - **Description:** Serves the `index.html` file from the static directory.
  - **Usage:** Access via browser to load the front-end application.

### Chat & Conversational Flow

- **POST /**  
  - **Description:** Handles chat requests by accepting a JSON payload with a `userMessage` field.
  - **Flow:**  
    1. Extracts the user message.
    2. Calls `run_flow` with the message and API key.
    3. Returns the generated response as JSON.
  - **Example Request Body:**
    ```json
    {
      "userMessage": "How do I process documents?"
    }
    ```

### FAQ Management

- **GET /api/faqs**  
  - **Description:** Retrieves FAQs from the Zilliz `faq_collection`.
  - **Response:** A JSON array of FAQs.
  
- **GET /api/faqs/translate?lang=<target_language>**  
  - **Description:** Translates FAQs into a specified target language.
  - **Parameters:**  
    - `lang`: Target language code (default is 'en' for English).  
  - **Flow:**  
    1. If the target language is English, returns the original FAQs.
    2. Otherwise, translates each FAQ concurrently in a batch using OpenAI's language model.
  - **Example URL:** `/api/faqs/translate?lang=es` to translate FAQs to Spanish.

### Audio Transcription

- **POST /api/transcribe**  
  - **Description:** Accepts an audio file (with a maximum size of 2MB) and transcribes it using OpenAI Whisper.
  - **Rate Limiting:**  
    - Maximum 5 requests per minute per IP.
  - **Flow:**  
    1. Checks rate limits based on the user’s IP.
    2. Validates file size.
    3. Saves the audio to a temporary file and performs transcription.
    4. Returns the transcription result as JSON.
  - **Example Request:** Multipart/form-data containing an audio file.

## Installation and Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/BenjaminDanker/Langflow-AI-Chatbot-Server.git
   cd Langflow-AI-Chatbot-Server
   ```

2. **Install Dependencies:**
   Ensure you have Python 3.8+ installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables:**
   Create a `.env` file in the root directory and set the following variables:
   - `OPENAI_API_KEY` – Your OpenAI API key.
   - `RENDER_LANGFLOW_API_KEY` – API key for LangFlow.
   - `ZILLIZ_AUTH_TOKEN` – Authentication token for Zilliz.
   - `ZILLIZ_URL` – URL for connecting to your Zilliz instance.
   - (Other configuration options as needed.)

## Usage

- **Starting the Server:**
  Run the server locally with:
  ```bash
  python server.py
  ```
  The server will run on the specified port (default is 8000).

- **Accessing the Front-end:**
  Open a browser and navigate to `http://localhost:8000/` to view the static index page.

- **API Testing:**
  Use tools like Postman or cURL to test endpoints such as `/`, `/api/faqs`, `/api/faqs/translate`, and `/api/transcribe`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- **OpenAI** for their cutting-edge language models and embedding services.
- **Zilliz** for their high-performance vector database.
- **LangFlow** for providing a flexible framework for building conversational workflows.
