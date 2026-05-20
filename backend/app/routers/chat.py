from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import Dict
import asyncio
from app.services.ai_service import call_deepseek
from app.utils.security import filter_user_input, filter_ai_output
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from typing import List

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}  # room_id -> {user_id: ws}

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
            await manager.broadcast(room_id, f"User {user_id}: {filtered}")
            
            # 检测是否 @AI
            if "@DeepSeek" in filtered:
                # 提取问题（去掉 @DeepSeek 部分）
                question = filtered.replace("@DeepSeek", "").strip()
                if question:
                    try:
                        ai_reply = await call_deepseek(question)
                        # 安全过滤 AI 输出
                        _, safe_ai_reply = filter_ai_output(ai_reply)
                        await manager.broadcast(room_id, f"DeepSeek: {safe_ai_reply}")
                    except Exception as e:
                        await manager.broadcast(room_id, f"[系统] AI调用失败: {str(e)}")
                        
    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)


# --- 新增：房间管理 REST 接口 ---

@router.get("/rooms", response_model=List[schemas.RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    """获取所有活跃的聊天室"""
    rooms = db.query(models.ChatRoom).all()
    return rooms

@router.post("/rooms", response_model=schemas.RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(room: schemas.RoomCreate, db: Session = Depends(get_db)):
    """创建一个新的聊天室"""
    # 暂时不校验用户，你可以后续加上 token 认证
    db_room = models.ChatRoom(name=room.name)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room