from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import Dict, List
import asyncio
import re
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.services.ai_service import call_ai
from app.utils.security import filter_user_input, filter_ai_output

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int, user_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        self.active_connections[room_id][user_id] = websocket

    def disconnect(self, room_id: int, user_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].pop(user_id, None)

    async def broadcast(self, room_id: int, message: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id].values():
                await connection.send_text(message)

manager = ConnectionManager()

# 房间消息历史缓存（用于AI上下文）
room_histories: Dict[int, list] = {}
MAX_HISTORY = 20


@router.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, user_id: str):
    await manager.connect(websocket, room_id, user_id)
    try:
        while True:
            data = await websocket.receive_text()

            # 安全过滤用户输入
            is_safe, filtered = filter_user_input(data)
            if not is_safe:
                await websocket.send_text(f"[系统] {filtered}")
                continue

            # 广播用户消息
            await manager.broadcast(room_id, f"{user_id}: {filtered}")

            # 存入历史
            if room_id not in room_histories:
                room_histories[room_id] = []
            room_histories[room_id].append({"role": "user", "content": f"{user_id}: {filtered}"})
            if len(room_histories[room_id]) > MAX_HISTORY:
                room_histories[room_id].pop(0)

            # 检测是否 @AI
            model_match = re.search(r'@(\w+)', filtered)
            if model_match:
                model_name = f"@{model_match.group(1)}"
                question = filtered.replace(model_name, "").strip()
                if question:
                    try:
                        history = room_histories.get(room_id, [])[:]
                        ai_reply = await call_ai(model_name, history)
                        _, safe_ai_reply = filter_ai_output(ai_reply)
                        await manager.broadcast(room_id, f"{model_name}: {safe_ai_reply}")
                        # AI回复也存入历史
                        room_histories[room_id].append({"role": "assistant", "content": f"{model_name}: {safe_ai_reply}"})
                    except Exception as e:
                        await manager.broadcast(room_id, f"[系统] AI调用失败: {str(e)}")

    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)


# ---------- REST 接口：房间管理 ----------
@router.get("/rooms", response_model=List[schemas.RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    rooms = db.query(models.ChatRoom).all()
    return rooms

@router.post("/rooms", response_model=schemas.RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(room: schemas.RoomCreate, db: Session = Depends(get_db)):
    db_room = models.ChatRoom(name=room.name)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room