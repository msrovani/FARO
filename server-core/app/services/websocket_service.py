"""
WebSocket service for real-time push notifications.
Manages WebSocket connections and broadcasts events to connected clients.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import settings

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for real-time notifications.
    Supports user-specific channels and broadcast channels.
    """
    
    def __init__(self):
        # Active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Active connections for broadcast (intelligence console)
        self.broadcast_connections: Set[WebSocket] = set()
    
    async def connect_user(self, websocket: WebSocket, user_id: str):
        """
        Connect a user WebSocket for personalized notifications.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID for routing
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        # Enforce max connections limit
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        if total_connections > settings.websocket_max_connections:
            logger.warning(
                f"WebSocket connection limit reached: {total_connections} > {settings.websocket_max_connections}"
            )
    
    async def connect_broadcast(self, websocket: WebSocket):
        """
        Connect a WebSocket for broadcast notifications (intelligence console).
        
        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.broadcast_connections.add(websocket)
        
        if len(self.broadcast_connections) > settings.websocket_max_connections:
            logger.warning(
                f"Broadcast connection limit reached: {len(self.broadcast_connections)} > {settings.websocket_max_connections}"
            )
    
    def disconnect_user(self, websocket: WebSocket, user_id: str):
        """
        Disconnect a user WebSocket.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID for routing
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    def disconnect_broadcast(self, websocket: WebSocket):
        """
        Disconnect a broadcast WebSocket.
        
        Args:
            websocket: WebSocket connection
        """
        self.broadcast_connections.discard(websocket)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific user.
        
        Args:
            user_id: User ID to send to
            message: Message payload
        """
        if user_id not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = set()
        
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message to user {user_id}: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect_user(connection, user_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all broadcast connections.
        
        Args:
            message: Message payload
        """
        if not self.broadcast_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = set()
        
        for connection in self.broadcast_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Failed to broadcast WebSocket message: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect_broadcast(connection)
    
    def get_connection_count(self) -> Dict[str, int]:
        """
        Get current connection statistics.
        
        Returns:
            Dictionary with connection counts
        """
        return {
            "user_connections": sum(len(conns) for conns in self.active_connections.values()),
            "broadcast_connections": len(self.broadcast_connections),
            "total": sum(len(conns) for conns in self.active_connections.values()) + len(self.broadcast_connections),
        }


# Singleton instance
websocket_manager = WebSocketConnectionManager()
