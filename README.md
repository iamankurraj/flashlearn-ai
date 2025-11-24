# FlashLearn AI

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

FlashLearn AI is a web application that helps you study and learn more effectively. It uses AI to automatically generate a summary, flashcards, and quizzes from your study materials. You can upload PDF or text files, or provide a YouTube URL, and FlashLearn AI will create a personalized study guide for you.

## Features

*   **AI-Powered Content Generation:** Automatically generates summaries, flashcards, and quizzes from your content.
*   **Multiple Content Sources:** Supports PDF files, text files, and YouTube videos.
*   **Retrieval-Augmented Generation (RAG):** Ask questions about your study materials and get answers from the AI.
*   **Simple and Intuitive Interface:** Easy-to-use web interface for uploading content and viewing your study guides.

## How It Works

FlashLearn AI is built with a Python backend and a simple HTML, CSS, and JavaScript frontend.

### Backend

The backend is a FastAPI application that handles the following:

*   **File and URL Processing:** It extracts text from uploaded files (PDF, TXT) and transcripts from YouTube videos.
*   **AI Content Generation:** It uses the Google Generative AI (Gemini Pro) to generate the summary, flashcards, and quiz.
*   **Vector Database:** It uses ChromaDB to store the text from your documents as vector embeddings.
*   **RAG:** When you ask a question, it uses the vector embeddings in ChromaDB to find the most relevant parts of your documents and then uses the AI to generate an answer based on that context.
*   **API:** It provides a set of API endpoints for the frontend to interact with.

### Frontend

The frontend is a simple web page that allows you to:

*   Create "subjects" to organize your study materials.
*   Upload a file or provide a YouTube URL for a subject.
*   View the generated summary, flashcards, and quiz.
*   Ask questions about the subject.

## How to Run

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up Environment Variables:**
    Create a `.env` file in the root of the project and add your Google API key:
    ```
    GOOGLE_API_KEY=your_google_api_key
    ```

3.  **Run the Application:**
    ```bash
    uvicorn app.main:app --reload
    ```

4.  **Open in Browser:**
    Open your web browser and go to `http://127.0.0.1:8000`.
