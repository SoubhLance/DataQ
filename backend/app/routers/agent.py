import logging
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from app.utils.dataframe_cache import get_session
from app.models.session_model import SessionState
from app.services.agent_service import AgentService
from app.services.task_service import task_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["AI Agent"])

class AgentChatRequest(BaseModel):
    session_id: str = Field(..., description="Active session UUID.")
    message: str = Field(..., description="Message payload to ask the AI assistant.")

class AgentChatResponse(BaseModel):
    response: str = Field(..., description="Markdown response string from the AI assistant.")

def run_background_chat(session_id: str, message: str, task_id: str):
    """Background task runner for AI chat requests."""
    try:
        session = get_session(session_id)
        task_service.update_task_progress(task_id, 30, "AI analyzing dataset properties...")
        
        reply = AgentService.process_chat_message(session, message)
        
        task_service.update_task_progress(task_id, 85, "Formatting chat response...")
        task_service.complete_task(task_id, result={"response": reply})
    except Exception as e:
        logger.error(f"Background AI chat failed: {str(e)}")
        task_service.fail_task(task_id, str(e))

@router.post("/chat", response_model=dict)
async def chat_with_agent(
    request: AgentChatRequest,
    background_tasks: BackgroundTasks,
    background: bool = Query(False, description="Whether to run the agent chat asynchronously in the background.")
):
    """
    Chat with the AI Assistant. Provides data diagnostics, recommendations, 
    explains anomalies, and suggests suitable machine learning models.
    Supports synchronous and asynchronous background task updates.
    """
    if not background:
        session = get_session(request.session_id)
        try:
            reply = AgentService.process_chat_message(session, request.message)
            return AgentChatResponse(response=reply).model_dump()
        except Exception as e:
            logger.error(f"Error processing AI agent chat: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while generating agent response: {str(e)}"
            )
    else:
        task = task_service.create_task(request.session_id, "chat")
        background_tasks.add_task(run_background_chat, request.session_id, request.message, task.task_id)
        return {
            "task_id": task.task_id,
            "message": "AI agent chat requested in background."
        }
