from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from game import GameRoom
import asyncio

app = FastAPI()
rooms = {}

@app.get("/")
def health():
    return {"status": "Server running"}

@app.websocket("/ws/{room_id}/{player_id}")
async def websocket_game(ws: WebSocket, room_id: str, player_id: str):
    await ws.accept()

    if room_id not in rooms:
        rooms[room_id] = GameRoom(room_id)

    room = rooms[room_id]

    try:
        room.add_player(player_id, ws)
    except Exception:
        await ws.close()
        return

    # 🔹 SEND PLAYER NUMBER (VERY IMPORTANT)
    player_number = room.get_player_number(player_id)
    await ws.send_json({
        "type": "PLAYER_INFO",
        "you_are": f"Player {player_number}"
    })

    # 🔹 START GAME WHEN MIN 2 PLAYERS JOIN (ONLY ONCE)
    if len(room.players) >= 2 and not room.started:
        room.started = True
        await send_question(room)

    try:
        while True:
            data = await ws.receive_json()

            if data["type"] == "ANSWER":
                correct = room.check_answer(player_id, data["answer"])

                if correct:
                    # 🔹 SEND RESULT TO ALL
                    await broadcast(room, {
                        "type": "RESULT",
                        "winner": f"Player {room.get_player_number(player_id)}",
                        "scores": format_scores(room)
                    })

                    await asyncio.sleep(1)

                    # 🔹 NEXT QUESTION OR GAME OVER
                    if room.next_question():
                        await send_question(room)
                    else:
                        await broadcast(room, {
                            "type": "GAME_OVER",
                            "scores": format_scores(room)
                        })

    except WebSocketDisconnect:
        room.players.pop(player_id, None)

# ===================== HELPERS =====================

async def send_question(room: GameRoom):
    q = room.current_question()
    await broadcast(room, {
        "type": "QUESTION",
        "question": q["question"],
        "options": q["options"],
        "index": room.current_index + 1
    })

def format_scores(room: GameRoom):
    return {
        f"Player {i+1}": room.scores[pid]
        for i, pid in enumerate(room.player_order)
    }

async def broadcast(room: GameRoom, message: dict):
    for ws in room.players.values():
        await ws.send_json(message)
