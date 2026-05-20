from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import Dict
import asyncio
from app.services.ai_service import call_deepseek
from app.utils.security import filter_user_input, filter_ai_output
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from typing import List

# 房间消息历史缓存
room_histories: Dict[int, list] = {}
MAX_HISTORY = 20

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
            await manager.broadcast(room_id, f"{user_id}: {filtered}")
            # 存入历史
            if room_id not in room_histories:
                room_histories[room_id] = []
            room_histories[room_id].append({"role": "user", "content": f"{user_id}: {filtered}"})
            # 保持历史长度
            if len(room_histories[room_id]) > MAX_HISTORY:
                room_histories[room_id].pop(0)

            
            # 检测是否 @AI
            if "@DeepSeek" in filtered:
                question = filtered.replace("@DeepSeek", "").strip()
                if question:
                    try:
                        # 取出该房间的历史（包含刚刚这条）
                        history = room_histories.get(room_id, [])[:]
                        # 也可以再加一条当前问题
                        ai_reply = await call_deepseek(history, system_prompt="你是群聊中的 AI 助手，请结合历史对话进行回答。")
                        _, safe_ai_reply = filter_ai_output(ai_reply)
                        await manager.broadcast(room_id, f"DeepSeek: {safe_ai_reply}")
                        # AI 回复也存入历史
                        room_histories[room_id].append({"role": "assistant", "content": f"DeepSeek: {safe_ai_reply}"})
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