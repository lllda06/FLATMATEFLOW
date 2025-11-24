from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import redis.asyncio as redis

app = FastAPI()

# Разрешаем фронту ходить к FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище активных подключений: {user_id: [websocket1, websocket2...]}
connections: dict[int, list[WebSocket]] = {}

# Подключение к Redis (тот же, что ты можешь использовать в Django)
redis_client = redis.from_url("redis://127.0.0.1:6379", decode_responses=True)


async def broadcast_to_user(user_id: int, message: dict):
    """Отправить сообщение всем WebSocket-подключениям пользователя."""
    if user_id in connections:
        dead = []
        for ws in connections[user_id]:
            try:
                await ws.send_text(json.dumps(message))
            except WebSocketDisconnect:
                dead.append(ws)
        for ws in dead:
            connections[user_id].remove(ws)


@app.on_event("startup")
async def startup():
    # Подписываемся на Redis-канал, куда будет писать Django
    asyncio.create_task(redis_listener())


async def redis_listener():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("notifications")

    async for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        data = json.loads(msg["data"])
        user_id = data.get("user_id")
        if user_id:
            await broadcast_to_user(user_id, data)


@app.websocket("/ws/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()

    connections.setdefault(user_id, []).append(websocket)

    try:
        while True:
            # можем ничего не ждать, просто держать соединение
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections[user_id].remove(websocket)