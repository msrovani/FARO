"""
WebSocket endpoints for real-time push notifications.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.core.config import settings
from app.db.base import User, UserRole
from app.services.websocket_service import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/user/{user_id}")
async def websocket_user_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for user-specific notifications.
    Mobile agents connect here for real-time feedback.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID for routing
        token: JWT token for authentication
        db: Database session
    """
    if not settings.websocket_enabled:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="WebSocket disabled")
        return
    
    try:
        # Authenticate user from token
        if token:
            try:
                current_user = await get_current_user(token=token, db=db)
                if current_user.id != user_id:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User ID mismatch")
                    return
            except Exception as e:
                logger.warning(f"WebSocket authentication failed for user {user_id}: {e}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
                return
        else:
            # Allow anonymous connections for development (remove in production)
            if settings.is_production:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
                return
        
        # Connect user
        await websocket_manager.connect_user(websocket, user_id)
        logger.info(f"WebSocket user connected: {user_id}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "message": "WebSocket connection established"
        })
        
        # Keep connection alive
        try:
            while True:
                # Wait for ping from client
                data = await websocket.receive_text()
                # Echo back pong
                await websocket.send_json({"type": "pong", "data": data})
        except WebSocketDisconnect:
            logger.info(f"WebSocket user disconnected: {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
        finally:
            websocket_manager.disconnect_user(websocket, user_id)
            
    except Exception as e:
        logger.error(f"WebSocket endpoint error for user {user_id}: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")


@router.websocket("/ws/broadcast")
async def websocket_broadcast_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for broadcast notifications.
    Intelligence console connects here for real-time observation updates.
    
    Args:
        websocket: WebSocket connection
        token: JWT token for authentication
        db: Database session
    """
    if not settings.websocket_enabled:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="WebSocket disabled")
        return
    
    try:
        # Authenticate user
        if token:
            try:
                current_user = await get_current_user(token=token, db=db)
                # Only intelligence, supervisor, and admin can connect to broadcast
                if current_user.role not in {
                    UserRole.INTELLIGENCE,
                    UserRole.SUPERVISOR,
                    UserRole.ADMIN,
                }:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Insufficient permissions")
                    return
            except Exception as e:
                logger.warning(f"WebSocket broadcast authentication failed: {e}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
                return
        else:
            if settings.is_production:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
                return
        
        # Connect broadcast
        await websocket_manager.connect_broadcast(websocket)
        logger.info(f"WebSocket broadcast connected: {current_user.id if 'current_user' in locals() else 'anonymous'}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Broadcast WebSocket connection established"
        })
        
        # Keep connection alive
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_json({"type": "pong", "data": data})
        except WebSocketDisconnect:
            logger.info("WebSocket broadcast disconnected")
        except Exception as e:
            logger.error(f"WebSocket broadcast error: {e}")
        finally:
            websocket_manager.disconnect_broadcast(websocket)
            
    except Exception as e:
        logger.error(f"WebSocket broadcast endpoint error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")


@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket connection statistics.
    """
    return {
        "enabled": settings.websocket_enabled,
        "connections": websocket_manager.get_connection_count()
    }
