from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from typing import Dict, List
import asyncio
import re
import json
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.security import filter_user_input, filter_ai_output
from app.services.ai_service import call_ai, call_deepseek_stream, call_glm_stream

router = APIRouter(prefix="/api/chat", tags=["chat"])
STREAM_MAP = {
    "@DeepSeek": call_deepseek_stream,
    "@GLM": call_glm_stream,
}

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

            # 安全过滤
            is_safe, filtered = filter_user_input(data)
            if not is_safe:
                await websocket.send_text(json.dumps({"type": "system", "content": f"[系统] {filtered}"}))
                continue

            # 广播用户消息（JSON格式）
            msg_obj = {"type": "user", "sender": user_id, "content": filtered}
            await manager.broadcast(room_id, json.dumps(msg_obj, ensure_ascii=False))

            # 存入历史
            if room_id not in room_histories:
                room_histories[room_id] = []
            room_histories[room_id].append({"role": "user", "content": filtered})
            if len(room_histories[room_id]) > MAX_HISTORY:
                room_histories[room_id].pop(0)

            # 检测 @AI
            model_match = re.search(r'@(\w+)', filtered)
            if model_match:
                model_name = f"@{model_match.group(1)}"
                question = filtered.replace(model_name, "").strip()
                if question and model_name in STREAM_MAP:
                    try:
                        history = room_histories.get(room_id, [])[:]
                        stream_func = STREAM_MAP[model_name]
                        full_reply = ""
                        async for chunk in stream_func(history):
                            full_reply += chunk
                            # 每个 chunk 都广播给前端
                            stream_obj = {"type": "ai_stream", "model": model_name, "chunk": chunk, "done": False}
                            await manager.broadcast(room_id, json.dumps(stream_obj, ensure_ascii=False))
                        # 流式结束，发送完成标记
                        done_obj = {"type": "ai_stream", "model": model_name, "chunk": "", "done": True}
                        await manager.broadcast(room_id, json.dumps(done_obj, ensure_ascii=False))
                        # 审计并存入历史
                        _, safe_ai_reply = filter_ai_output(full_reply)
                        room_histories[room_id].append({"role": "assistant", "content": safe_ai_reply})
                    except Exception as e:
                        err_obj = {"type": "system", "content": f"[系统] AI调用失败: {str(e)}"}
                        await manager.broadcast(room_id, json.dumps(err_obj, ensure_ascii=False))

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