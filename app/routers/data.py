
from fastapi import APIRouter, HTTPException, Form
from app.utils import helpers
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/subjects", tags=["Data"])
async def get_all_subjects_endpoint():
    """
    Retrieves a list of all subjects that have been processed.
    """
    try:
        subjects = helpers.get_all_subjects()
        return {"subjects": subjects}
    except Exception as e:
        logger.error(f"Error retrieving all subjects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve subjects.")

@router.get("/subjects/{subject}", tags=["Data"])
async def get_subject_materials_endpoint(subject: str):
    """
    Retrieves all learning materials for a specific subject.
    """
    try:
        materials = helpers.get_subject_materials(subject)
        if not materials:
            raise HTTPException(status_code=404, detail="Subject not found.")
        return materials
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving materials for subject {subject}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve materials for subject.")

@router.post("/ask", tags=["RAG"])
async def ask_question_endpoint(subject: str = Form(...), question: str = Form(...)):
    """
    Answers a question using Retrieval-Augmented Generation (RAG) based on the
    documents associated with the given subject.
    """
    if not subject or subject.isspace():
        raise HTTPException(status_code=400, detail="Subject cannot be empty.")
    if not question or question.isspace():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        answer = await helpers.query_rag_for_answer(subject, question)
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error answering question for subject {subject}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get an answer: {str(e)}")
