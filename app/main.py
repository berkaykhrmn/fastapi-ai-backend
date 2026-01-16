import os
from datetime import datetime
from typing import Annotated
from typing import List

from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Depends, HTTPException, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from app import auth
import app.models as models
from ai.gemini import Gemini
from app.auth import get_current_user_optional, get_current_user
from app.database import engine, SessionLocal
from app.throttling import apply_rate_limit

app = FastAPI()
app.include_router(auth.router)

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["health"], summary="API Health Check",
    description="Simple health check endpoint to verify that the API is running and reachable.")
async def health_check():
    return {"status": "running"}

def load_prompt(file_path: str) -> str | None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

system_prompt = load_prompt("prompts/system_prompt.md")
summary_prompt = load_prompt("prompts/summary_prompt.md")
translate_prompt = load_prompt("prompts/translate_prompt.md")

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

ai_platform = Gemini(
    api_key=gemini_api_key,
    system_prompt=system_prompt,
    summary_prompt=summary_prompt,
    translate_prompt=translate_prompt
)

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

class ChatHistoryResponse(BaseModel):
    id: int
    created_at: datetime
    user_message: str
    ai_response: str

    class Config:
        from_attributes = True

class TranslateResponse(BaseModel):
    translated_text: str

@app.post("/chat", response_model=ChatResponse, tags=["chat"], summary="Chat with AI",
          description=(
                  "Send a user prompt to the AI and receive a generated response.\n\n"
                  "• Authenticated users have their chat history stored.\n"
                  "• Unauthenticated users are rate-limited and responses are not stored.\n"
                  "• Requests exceeding the rate limit are rejected."
          ))
async def chat(request: ChatRequest, db: db_dependency, user=Depends(get_current_user_optional)):
    if user:
        user_id = user["id"]
    else:
        user_id = "global_unauthenticated_user"
    apply_rate_limit(str(user_id))
    response_text = await ai_platform.chat(request.prompt)
    if user:
        chat_record = models.ChatHistory(
            user_id=user["id"],
            user_message=request.prompt,
            ai_response=response_text
        )
        db.add(chat_record)
        db.commit()
    return ChatResponse(response=response_text)

@app.post(
    "/chat/summarize",
    response_model=ChatResponse,
    tags=["summary"],
    summary="Summarize a text",
    description=(
        "Summarizes the given text.\n\n"
        "• Returns a summary in the original language and in English.\n"
        "• Very short texts return a warning instead of a summary.\n"
        "• Commands or non-textual inputs are rejected.\n"
        "• Authenticated users have summaries stored in chat history."
    )
)
async def summarize_chat(request: ChatRequest, db: db_dependency, user=Depends(get_current_user_optional)):
    if user:
        user_id = user["id"]
    else:
        user_id = "global_unauthenticated_user"
    apply_rate_limit(str(user_id))
    response_text = await ai_platform.summarize(request.prompt)
    if user:
        chat_record = models.ChatHistory(
            user_id=user["id"],
            user_message=request.prompt,
            ai_response=response_text
        )
        db.add(chat_record)
        db.commit()
    return ChatResponse(response=response_text)

@app.get(
    "/chat/history",
    response_model=List[ChatHistoryResponse],
    tags=["chat"],
    summary="Get chat history",
    description=(
        "Retrieve the authenticated user's chat history.\n\n"
        "• Chats are ordered from newest to oldest.\n"
        "• Only the requesting user's chats are returned.\n"
        "• Authentication is required."
    )
)
async def get_chat_history(db: db_dependency, user=Depends(get_current_user)):
    chats = (
        db.query(models.ChatHistory)
        .filter(models.ChatHistory.user_id == user["id"])
        .order_by(models.ChatHistory.created_at.desc())
        .all()
    )
    return chats

@app.delete(
    "/chat/history/{chat_id}",
    status_code=status.HTTP_200_OK,
    tags=["chat"],
    summary="Delete a chat history entry",
    description=(
        "Delete a specific chat history entry by its ID.\n\n"
        "• Only the owner of the chat can delete it.\n"
        "• Returns 404 if the chat does not exist or does not belong to the user.\n"
        "• Authentication is required."
    )
)
async def delete_chat_history(chat_id: int, db: db_dependency, user=Depends(get_current_user)):
    chats = (
        db.query(models.ChatHistory).filter(models.ChatHistory.id == chat_id, models.ChatHistory.user_id == user["id"]).first()
    )
    if not chats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    db.delete(chats)
    db.commit()
    return {"message": "Chat deleted",
            "deleted_chat_id": chat_id
            }

ALLOWED_LANGUAGES = {"en", "tr", "fr", "de", "es"}
@app.post(
    "/chat/translate",
    response_model=TranslateResponse,
    tags=["translate"],
    summary="Translate text to a target language",
    description=(
        "Translate the given text into the specified target language.\n\n"
        "• Source language is detected automatically.\n"
        "• Target language must be different from the source language.\n"
        "• Supported languages:\n"
        "  - en (English)\n"
        "  - tr (Turkish)\n"
        "  - fr (French)\n"
        "  - de (German)\n"
        "  - es (Spanish)\n\n"
        "• Empty prompts or unsupported languages are rejected.\n"
        "• Authenticated users have translations stored in chat history."
    )
)
async def translate_chat(
    db: db_dependency,
    prompt: str = Form(...),
    target_language: str = Form(...),
    user=Depends(get_current_user_optional)):
    target_lang = target_language.lower()
    if target_lang not in ALLOWED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target language '{target_language}'. Supported languages: {', '.join(ALLOWED_LANGUAGES)}"
        )

    if not prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty."
        )

    source_lang = await ai_platform.detect_language(prompt)
    if source_lang == target_lang:
        raise HTTPException(
            status_code=400,
            detail="Target language must be different from the source language."
        )
    user_id = user["id"] if user else "global_unauthenticated_user"
    apply_rate_limit(str(user_id))
    translated_text = await ai_platform.translate(prompt, target_lang)

    if user:
        chat_record = models.ChatHistory(
            user_id=user["id"],
            user_message=f"{prompt} (translate to {target_lang})",
            ai_response=translated_text
        )
        db.add(chat_record)
        db.commit()

    return TranslateResponse(translated_text=translated_text)