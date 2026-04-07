import requests
from fastapi import APIRouter, Form

# simplified router to avoid heavy langchain dependency
router = APIRouter()

@router.post("/Exam")
async def chat(language: str = Form(...), question_type: str = Form(...), difficulty: str = Form(...), Numberofquestions: str = Form(...)):
    """Stubbed endpoint; original implementation required LangChain and Ollama.
    This returns a placeholder response so the app can start without the package.
    """
    return {"output": [f"Requested {Numberofquestions} {difficulty} {question_type} questions in {language}"], "time_taken": 0.0}
    
