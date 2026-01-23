from typing import Dict, List, Any, Set
from fastapi import WebSocket
from uuid import UUID

class ConnectionManager:
    def __init__(self):
        # user_id -> set of WebSockets
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
        # org_id -> set of user_ids (for easy broadcasting to org)
        self.org_connections: Dict[UUID, Set[UUID]] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID, org_id: UUID):
        await websocket.accept()
        print(f"🟢 [WS DEBUG] User {user_id} connected with org_id={org_id}")
        # User connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Org connections
        if org_id not in self.org_connections:
            self.org_connections[org_id] = set()
        self.org_connections[org_id].add(user_id)
        print(f"🟢 [WS DEBUG] After connect, org_connections: {dict((k, list(v)) for k,v in self.org_connections.items())}")

    def disconnect(self, websocket: WebSocket, user_id: UUID, org_id: UUID):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                # Remove user from org set if no more connections
                if org_id in self.org_connections and user_id in self.org_connections[org_id]:
                    self.org_connections[org_id].remove(user_id)
                    if not self.org_connections[org_id]:
                        del self.org_connections[org_id]

    async def send_to_user(self, user_id: UUID, message: Any):
        print(f"📤 [WS DEBUG] send_to_user called for user_id={user_id}")
        if user_id in self.active_connections:
            connections = self.active_connections[user_id]
            print(f"📤 [WS DEBUG] Found {len(connections)} connection(s) for user")
            for i, connection in enumerate(connections):
                try:
                    print(f"📤 [WS DEBUG] Sending to connection {i+1}, state={connection.client_state}")
                    await connection.send_json(message)
                    print(f"✅ [WS DEBUG] Successfully sent message to connection {i+1}")
                except Exception as e:
                    print(f"❌ [WS DEBUG] FAILED to send to connection {i+1}: {type(e).__name__}: {e}")
        else:
            print(f"⚠️ [WS DEBUG] No active connections found for user_id={user_id}")

    async def broadcast(self, user_ids: List[UUID], message: Any):
        for uid in user_ids:
            await self.send_to_user(uid, message)
            
    async def broadcast_to_org(self, org_id: UUID, message: Any):
        print(f"🔍 [WS DEBUG] broadcast_to_org called with org_id={org_id}")
        print(f"🔍 [WS DEBUG] Currently connected orgs: {list(self.org_connections.keys())}")
        print(f"🔍 [WS DEBUG] org_id in org_connections: {org_id in self.org_connections}")
        if org_id in self.org_connections:
            user_ids = list(self.org_connections[org_id])
            print(f"🔍 [WS DEBUG] Broadcasting to user_ids: {user_ids}")
            await self.broadcast(user_ids, message)
        else:
            print(f"⚠️ [WS DEBUG] No users connected for org {org_id} - message NOT sent!")

    async def handle_incoming(self, user_id: UUID, data: Dict[str, Any]):
        from server.services.websocket_events import handle_event
        await handle_event(user_id, data)

manager = ConnectionManager()
