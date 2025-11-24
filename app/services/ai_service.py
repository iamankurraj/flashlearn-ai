import os
import google.generativeai as genai
import logging
import json
from fastapi import HTTPException
from dotenv import load_dotenv, find_dotenv
import os

# auto-detect .env anywhere in parent folders
load_dotenv(find_dotenv())
logger = logging.getLogger(__name__)

# --- AI Service Configuration ---

try:
    # Configure the Gemini API client
    api_key = os.getenv("GOOGLE_API_KEY")
    print(api_key)
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro-latest')
    logger.info("Gemini API client configured successfully.")
except Exception as e:
    logger.error(f"Error configuring Gemini API: {e}", exc_info=True)
    model = None

# --- Prompt Engineering ---

def get_generation_prompt(text_content: str) -> str:
    """
    Creates a detailed, structured prompt for the Gemini API.
    
    Args:
        text_content (str): The source text for generating materials.
        
    Returns:
        str: The full prompt string.
    """
    return f"""
    Analyze the following text and perform three tasks:
    1.  Generate a concise, easy-to-understand summary.
    2.  Create a multiple-choice quiz with 5 questions based on the key information in the text.
    3.  Generate a set of 5-10 flashcards with key terms and their definitions.

    The output MUST be a single, valid JSON object. Do not include any text or formatting outside of this JSON object.

    The JSON object should have the following structure:
    {{
        "summary": "<Your generated summary here>",
        "quiz": [
            {{
                "question": "<Question 1>",
                "options": [
                    "<Option A>",
                    "<Option B>",
                    "<Option C>",
                    "<Option D>"
                ],
                "answer": "<The correct option>"
            }},
            ...
        ],
        "flashcards": [
            {{
                "term": "<Key Term 1>",
                "definition": "<Definition of Term 1>"
            }},
            ...
        ]
    }}

    Here is the text to analyze:
    ---
    {text_content}
    ---
    """

# --- AI Content Generation ---

async def generate_learning_materials(text_content: str) -> dict:
    """
    Sends the content to the Gemini API and gets a summary, quiz, and flashcards.

    Args:
        text_content (str): The text to be processed.

    Returns:
        dict: A dictionary containing the summary, quiz, and flashcards.
    """
    if not model:
        raise HTTPException(status_code=500, detail="AI service is not configured. Check API key and configuration.")

    try:
        prompt = get_generation_prompt(text_content)
        
        # Generate content using the async method
        response = await model.generate_content_async(prompt)
        
        # Clean up the response and parse the JSON
        # The model might sometimes wrap the JSON in ```json ... ```
        response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        # Find the start of the JSON object
        json_start = response_text.find('{')
        if json_start == -1:
            raise ValueError("No JSON object found in the AI response.")
        
        # Extract the JSON part of the string
        json_string = response_text[json_start:]
        
        result = json.loads(json_string)
        
        logger.info("Successfully generated summary, quiz, and flashcards from AI service.")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {e}\nRaw AI Response:\n{response.text}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to parse the AI's response. The format was invalid.")
    except Exception as e:
        logger.error(f"An error occurred while generating AI content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred in the AI service: {str(e)}")
