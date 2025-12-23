from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from firebase import db

app = FastAPI()

rooms = {}
QUESTION_TIME = 10


@app.websocket("/ws/{admin_id}/{room_id}/{player_id}")
async def game_socket(ws: WebSocket, admin_id: str, room_id: str, player_id: str):
    await ws.accept()

    if room_id not in rooms:
        rooms[room_id] = {
            "players": {},
            "scores": {},
            "index": 0
        }

    room = rooms[room_id]
    room["players"][player_id] = ws
    room["scores"].setdefault(player_id, 0)

    questions = get_questions(admin_id)

    if not questions:
        await ws.send_json({"type": "ERROR", "message": "No questions"})
        return

    try:
        while True:
            q = questions[room["index"]]

            await broadcast(room, {
                "type": "QUESTION",
                "question": q["question"],
                "options": q["options"],
                "index": room["index"] + 1
            })

            try:
                msg = await asyncio.wait_for(ws.receive_json(), timeout=QUESTION_TIME)
                if msg["type"] == "ANSWER":
                    if msg["answer"] == q["correctIndex"]:
                        room["scores"][player_id] += 1
            except asyncio.TimeoutError:
                pass

            room["index"] += 1
            if room["index"] >= len(questions):
                break

        await broadcast(room, {
            "type": "GAME_OVER",
            "scores": room["scores"]
        })

    except WebSocketDisconnect:
        room["players"].pop(player_id, None)


def get_questions(admin_id: str):
    docs = (
        db.collection("admins")
        .document(admin_id)
        .collection("questions")
        .order_by("createdAt")
        .stream()
    )
    return [d.to_dict() for d in docs]


async def broadcast(room, message):
    for ws in room["players"].values():
        await ws.send_json(message)
