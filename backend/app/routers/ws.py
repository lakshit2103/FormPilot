"""
WebSocket router — real-time agent event streaming to the frontend.
One WS connection per application session. Events are pulled from asyncio.Queue.
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
import app.services.application_service as svc

router = APIRouter()

# Reference the same queues from applications router
_event_queues = svc._event_queues if hasattr(svc, '_event_queues') else {}


@router.websocket("/ws/applications/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = "",  # passed as query param ?token=...
):
    """
    WebSocket endpoint for real-time agent event streaming.
    
    Frontend connects with: ws://localhost:8000/ws/applications/{session_id}?token={access_token}
    
    Events emitted:
    - agent_message: {type, node, text}
    - jobs_found: {type, count}
    - fields_extracted: {type, count}
    - mapping_complete: {type, ready, missing, ambiguous}
    - questions_ready: {type, count}
    - form_filled: {type, field, value}
    - manual_action_required: {type, reason, instructions}
    - validation_error: {type, field, message}
    - review_ready: {type, summary}
    - session_complete: {type}
    - error: {type, message, recoverable}
    - ping: keepalive
    """
    await websocket.accept()

    # Get or create the event queue for this session
    if session_id not in _event_queues:
        _event_queues[session_id] = asyncio.Queue()
    queue = _event_queues[session_id]

    try:
        while True:
            # Check for events with timeout (for keepalive pings)
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15.0)
                await websocket.send_text(json.dumps(event))
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e),
                "recoverable": False,
            }))
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
