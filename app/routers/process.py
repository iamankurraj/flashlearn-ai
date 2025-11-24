from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services import file_service, ai_service
from app.utils import helpers
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process/file", tags=["Processing"])
async def process_file_endpoint(subject: str = Form(...), file: UploadFile = File(...)):
    """
    Processes an uploaded file, generates learning materials, and saves them under a subject.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")
    if not subject or subject.isspace():
        raise HTTPException(status_code=400, detail="Subject cannot be empty.")

    allowed_extensions = {"pdf", "txt"}
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file type: .{file_extension}.")

    try:
        contents = await file.read()
        text_content = file_service.get_text_from_file(file.filename, contents)

        if not text_content or text_content.isspace():
            raise HTTPException(status_code=400, detail="Could not extract any text from the file.")

        # Store document for RAG
        helpers.upsert_document(subject, text_content)

        # Generate learning materials
        materials = await ai_service.generate_learning_materials(text_content)

        # Save materials to the subject
        helpers.save_learning_materials(subject, materials)

        # Return all materials for the subject
        return helpers.get_subject_materials(subject)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing file {file.filename} for subject {subject}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.post("/process/youtube", tags=["Processing"])
async def process_youtube_endpoint(subject: str = Form(...), url: str = Form(...)):
    """
    Processes a YouTube URL, generates learning materials, and saves them under a subject.
    """
    if not url or "youtube.com" not in url and "youtu.be" not in url:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL provided.")
    if not subject or subject.isspace():
        raise HTTPException(status_code=400, detail="Subject cannot be empty.")

    try:
        transcript = file_service.get_transcript_from_youtube(url)
        if not transcript or transcript.isspace():
            raise HTTPException(status_code=400, detail="Could not retrieve transcript for this video.")

        # Store document for RAG
        helpers.upsert_document(subject, transcript)

        # Generate learning materials
        materials = await ai_service.generate_learning_materials(transcript)

        # Save materials to the subject
        helpers.save_learning_materials(subject, materials)

        # Return all materials for the subject
        return helpers.get_subject_materials(subject)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing YouTube URL {url} for subject {subject}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process YouTube URL: {str(e)}")