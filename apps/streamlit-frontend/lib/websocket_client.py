"""
WebSocket client for real-time updates
Implements reconnection logic and message handling
"""

import asyncio
import json
import logging
import threading
from typing import Callable, Dict, Optional, Any
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
import streamlit as st
from dataclasses import dataclass
from enum import Enum
from queue import Queue, Empty
import time

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class WebSocketConfig:
    """Configuration for WebSocket connection."""
    url: str
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    heartbeat_interval: int = 30
    message_timeout: int = 60
    auto_reconnect: bool = True


class WebSocketManager:
    """
    Manages WebSocket connections with automatic reconnection and message handling.
    Thread-safe implementation for Streamlit.
    """
    
    def __init__(self, config: WebSocketConfig):
        """
        Initialize WebSocket manager.
        
        Args:
            config: WebSocket configuration
        """
        self.config = config
        self.state = ConnectionState.DISCONNECTED
        self.websocket = None
        self.loop = None
        self.thread = None
        self.message_queue = Queue()
        self.handlers: Dict[str, Callable] = {}
        self.reconnect_attempts = 0
        self.last_heartbeat = None
        self.should_stop = False
        
        # Statistics
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'connection_time': None,
            'last_message_time': None,
            'errors': []
        }
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register a message handler.
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        self.handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    def start(self) -> None:
        """Start WebSocket connection in background thread."""
        if self.thread and self.thread.is_alive():
            logger.warning("WebSocket already running")
            return
        
        self.should_stop = False
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        logger.info("WebSocket manager started")
    
    def stop(self) -> None:
        """Stop WebSocket connection."""
        self.should_stop = True
        
        if self.loop and self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.close(),
                self.loop
            )
        
        if self.thread:
            self.thread.join(timeout=5)
        
        self.state = ConnectionState.DISCONNECTED
        logger.info("WebSocket manager stopped")
    
    def _run_event_loop(self) -> None:
        """Run event loop in background thread."""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._connect_and_listen())
        except Exception as e:
            logger.error(f"Event loop error: {str(e)}")
            self.state = ConnectionState.ERROR
        finally:
            self.loop.close()
    
    async def _connect_and_listen(self) -> None:
        """Connect to WebSocket and listen for messages."""
        while not self.should_stop:
            try:
                await self._connect()
                await self._listen()
            except Exception as e:
                logger.error(f"Connection error: {str(e)}")
                
                if self.config.auto_reconnect and not self.should_stop:
                    await self._handle_reconnection()
                else:
                    break
    
    async def _connect(self) -> None:
        """Establish WebSocket connection."""
        self.state = ConnectionState.CONNECTING
        logger.info(f"Connecting to {self.config.url}")
        
        try:
            self.websocket = await websockets.connect(
                self.config.url,
                ping_interval=self.config.heartbeat_interval,
                ping_timeout=10
            )
            
            self.state = ConnectionState.CONNECTED
            self.reconnect_attempts = 0
            self.stats['connection_time'] = datetime.now()
            
            logger.info("WebSocket connected successfully")
            
            # Send initial authentication if needed
            if st.session_state.get('api_token'):
                await self.send_message({
                    'type': 'auth',
                    'token': st.session_state.api_token
                })
            
        except Exception as e:
            self.state = ConnectionState.ERROR
            logger.error(f"Connection failed: {str(e)}")
            raise
    
    async def _listen(self) -> None:
        """Listen for incoming messages."""
        try:
            async for message in self.websocket:
                if self.should_stop:
                    break
                
                await self._handle_message(message)
                
        except ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.state = ConnectionState.DISCONNECTED
        except WebSocketException as e:
            logger.error(f"WebSocket error: {str(e)}")
            self.state = ConnectionState.ERROR
            raise
    
    async def _handle_message(self, raw_message: str) -> None:
        """
        Handle incoming WebSocket message.
        
        Args:
            raw_message: Raw message string
        """
        try:
            message = json.loads(raw_message)
            self.stats['messages_received'] += 1
            self.stats['last_message_time'] = datetime.now()
            
            logger.debug(f"Received message: {message.get('type', 'unknown')}")
            
            # Handle different message types
            message_type = message.get('type', 'unknown')
            
            if message_type == 'heartbeat':
                self.last_heartbeat = datetime.now()
                await self.send_message({'type': 'heartbeat_ack'})
                
            elif message_type == 'error':
                logger.error(f"Server error: {message.get('error', 'Unknown error')}")
                self.stats['errors'].append({
                    'time': datetime.now(),
                    'error': message.get('error')
                })
                
            elif message_type in self.handlers:
                # Call registered handler
                handler = self.handlers[message_type]
                try:
                    handler(message)
                except Exception as e:
                    logger.error(f"Handler error for {message_type}: {str(e)}")
            
            else:
                # Queue message for processing
                self.message_queue.put(message)
                
                # Trigger Streamlit rerun if needed
                if message.get('requires_update', False):
                    st.rerun()
                    
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {str(e)}")
        except Exception as e:
            logger.error(f"Message handling error: {str(e)}")
    
    async def _handle_reconnection(self) -> None:
        """Handle reconnection logic."""
        if self.reconnect_attempts >= self.config.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            self.state = ConnectionState.ERROR
            return
        
        self.state = ConnectionState.RECONNECTING
        self.reconnect_attempts += 1
        
        wait_time = min(
            self.config.reconnect_interval * (2 ** self.reconnect_attempts),
            60  # Max wait time of 60 seconds
        )
        
        logger.info(f"Reconnecting in {wait_time} seconds (attempt {self.reconnect_attempts})")
        await asyncio.sleep(wait_time)
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send message through WebSocket.
        
        Args:
            message: Message to send
            
        Returns:
            True if sent successfully
        """
        if self.state != ConnectionState.CONNECTED or not self.websocket:
            logger.warning("Cannot send message - not connected")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            self.stats['messages_sent'] += 1
            logger.debug(f"Sent message: {message.get('type', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
    
    def send_message_sync(self, message: Dict[str, Any]) -> bool:
        """
        Send message synchronously (from main thread).
        
        Args:
            message: Message to send
            
        Returns:
            True if sent successfully
        """
        if not self.loop or not self.websocket:
            return False
        
        future = asyncio.run_coroutine_threadsafe(
            self.send_message(message),
            self.loop
        )
        
        try:
            return future.result(timeout=5)
        except Exception as e:
            logger.error(f"Sync send failed: {str(e)}")
            return False
    
    def get_messages(self, timeout: float = 0.1) -> list:
        """
        Get all pending messages from queue.
        
        Args:
            timeout: Timeout for getting messages
            
        Returns:
            List of messages
        """
        messages = []
        
        try:
            while True:
                message = self.message_queue.get(timeout=timeout)
                messages.append(message)
                self.message_queue.task_done()
        except Empty:
            pass
        
        return messages
    
    def get_state(self) -> ConnectionState:
        """Get current connection state."""
        return self.state
    
    def get_stats(self) -> Dict:
        """Get connection statistics."""
        return self.stats.copy()
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.state == ConnectionState.CONNECTED


# Streamlit-specific WebSocket integration
class StreamlitWebSocketClient:
    """
    WebSocket client optimized for Streamlit applications.
    """
    
    def __init__(self, ws_url: str, site_id: Optional[str] = None):
        """
        Initialize Streamlit WebSocket client.
        
        Args:
            ws_url: WebSocket server URL
            site_id: Optional site ID to subscribe to
        """
        # Build WebSocket URL with site subscription
        if site_id:
            ws_url = f"{ws_url}/ws/{site_id}"
        
        config = WebSocketConfig(url=ws_url)
        self.manager = WebSocketManager(config)
        
        # Register default handlers
        self._register_default_handlers()
        
        # Store in session state for persistence
        if 'websocket_client' not in st.session_state:
            st.session_state.websocket_client = self
    
    def _register_default_handlers(self) -> None:
        """Register default message handlers."""
        
        def handle_performance_update(message: Dict) -> None:
            """Handle performance update messages."""
            data = message.get('data', {})
            site_id = data.get('site_id')
            
            if site_id:
                # Update session state
                if 'real_time_data' not in st.session_state:
                    st.session_state.real_time_data = {}
                
                st.session_state.real_time_data[site_id] = {
                    'timestamp': datetime.now(),
                    'data': data
                }
                
                logger.info(f"Performance update for site {site_id}")
        
        def handle_alert(message: Dict) -> None:
            """Handle alert messages."""
            alert = message.get('alert', {})
            severity = alert.get('severity', 'info')
            
            # Store alert in session state
            if 'alerts' not in st.session_state:
                st.session_state.alerts = []
            
            st.session_state.alerts.append({
                'timestamp': datetime.now(),
                'severity': severity,
                'message': alert.get('message', 'Unknown alert'),
                'site_id': alert.get('site_id')
            })
            
            # Keep only last 50 alerts
            if len(st.session_state.alerts) > 50:
                st.session_state.alerts = st.session_state.alerts[-50:]
            
            logger.info(f"Alert received: {severity}")
        
        self.manager.register_handler('performance_update', handle_performance_update)
        self.manager.register_handler('alert', handle_alert)
    
    def connect(self) -> None:
        """Start WebSocket connection."""
        self.manager.start()
    
    def disconnect(self) -> None:
        """Stop WebSocket connection."""
        self.manager.stop()
    
    def subscribe_to_site(self, site_id: str) -> bool:
        """
        Subscribe to updates for a specific site.
        
        Args:
            site_id: Site identifier
            
        Returns:
            True if subscription sent
        """
        return self.manager.send_message_sync({
            'type': 'subscribe',
            'site_id': site_id
        })
    
    def unsubscribe_from_site(self, site_id: str) -> bool:
        """
        Unsubscribe from site updates.
        
        Args:
            site_id: Site identifier
            
        Returns:
            True if unsubscription sent
        """
        return self.manager.send_message_sync({
            'type': 'unsubscribe',
            'site_id': site_id
        })
    
    def get_real_time_data(self, site_id: str) -> Optional[Dict]:
        """
        Get real-time data for a site.
        
        Args:
            site_id: Site identifier
            
        Returns:
            Real-time data or None
        """
        if 'real_time_data' not in st.session_state:
            return None
        
        return st.session_state.real_time_data.get(site_id)
    
    def render_connection_status(self) -> None:
        """Render WebSocket connection status indicator."""
        state = self.manager.get_state()
        
        status_colors = {
            ConnectionState.CONNECTED: "#54b892",
            ConnectionState.CONNECTING: "#647cb2",
            ConnectionState.RECONNECTING: "#bd6821",
            ConnectionState.DISCONNECTED: "#8c7f79",
            ConnectionState.ERROR: "#ff4444"
        }
        
        color = status_colors.get(state, "#5f5f5f")
        
        st.markdown(
            f"""
            <div style='display: flex; align-items: center; gap: 8px;'>
                <div style='width: 10px; height: 10px; border-radius: 50%; 
                           background: {color};'></div>
                <span style='font-size: 12px; color: #f0f0f0;'>
                    {state.value.capitalize()}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )


# Singleton WebSocket client
_websocket_client: Optional[StreamlitWebSocketClient] = None


def get_websocket_client(ws_url: str = None, site_id: str = None) -> StreamlitWebSocketClient:
    """
    Get or create WebSocket client singleton.
    
    Args:
        ws_url: WebSocket URL (uses env var if not provided)
        site_id: Optional site to subscribe to
        
    Returns:
        WebSocket client instance
    """
    global _websocket_client
    
    if _websocket_client is None:
        import os
        ws_url = ws_url or os.getenv('WS_BASE_URL', 'ws://localhost:8000')
        _websocket_client = StreamlitWebSocketClient(ws_url, site_id)
        _websocket_client.connect()
    
    return _websocket_client