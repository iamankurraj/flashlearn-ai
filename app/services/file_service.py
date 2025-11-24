import logging
from pypdf import PdfReader
from pytube import YouTube
from io import BytesIO

logger = logging.getLogger(__name__)

# --- Text Extraction Service ---

def get_text_from_file(filename: str, contents: bytes) -> str:
    """
    Extracts text from an uploaded file based on its extension.

    Args:
        filename (str): The name of the file.
        contents (bytes): The byte content of the file.

    Returns:
        str: The extracted text content.
    """
    file_extension = filename.split('.')[-1].lower()
    text = ""

    try:
        if file_extension == 'pdf':
            pdf_reader = PdfReader(BytesIO(contents))
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        elif file_extension == 'txt':
            text = contents.decode('utf-8')
        else:
            # This case is already handled in the router, but good for safety
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        logger.info(f"Successfully extracted {len(text)} characters from {filename}")
        return text

    except Exception as e:
        logger.error(f"Failed to extract text from {filename}: {e}", exc_info=True)
        raise

def get_transcript_from_youtube(url: str) -> str:
    """
    Downloads the audio from a YouTube video and returns its transcription.
    Note: This uses pytube's caption functionality, which relies on YouTube's auto-generated captions.

    Args:
        url (str): The YouTube video URL.

    Returns:
        str: The video's transcript or an empty string if not available.
    """
    try:
        yt = YouTube(url)
        
        # Ensure the video is available
        yt.check_availability()

        # Get the English caption track
        # Pytube returns a list of available caption tracks
        caption = yt.captions.get_by_language_code('en')

        if not caption:
            logger.warning(f"No English captions found for YouTube video: {url}")
            # Try to get auto-generated captions if official ones aren't there
            caption = yt.captions.get_by_language_code('a.en')

        if caption:
            transcript = caption.generate_srt_captions()
            logger.info(f"Successfully fetched transcript for YouTube video: {url}")
            return transcript
        else:
            logger.error(f"Could not retrieve any English transcript for {url}")
            return ""

    except Exception as e:
        logger.error(f"Failed to get transcript from YouTube URL {url}: {e}", exc_info=True)
        raise
