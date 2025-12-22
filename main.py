from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from game import GameRoom
import asyncio

app = FastAPI()
rooms = {}

QUESTION_TIME = 10

# 🔥 QUESTIONS COME FROM ADMIN (TEMP IN-MEMORY)
QUESTIONS_DB = []   # admin will populate this


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

    # Player info
    await ws.send_json({
        "type": "PLAYER_INFO",
        "you_are": f"Player {room.get_player_number(player_id)}"
    })

    # Start game
    if len(room.players) >= 2 and not room.started:
        room.started = True
        await start_question(room)

    try:
        while True:
            data = await ws.receive_json()

            if data["type"] == "ANSWER":
                question = QUESTIONS_DB[room.current_index]
                correct = room.check_answer(
                    player_id,
                    data["answer"],
                    question["correct"]
                )

                if correct:
                    room.cancel_timer()

                    await broadcast(room, {
                        "type": "RESULT",
                        "winner": f"Player {room.get_player_number(player_id)}",
                        "scores": format_scores(room)
                    })

                    await asyncio.sleep(1)
                    await advance_game(room)

    except WebSocketDisconnect:
        room.players.pop(player_id, None)


# ---------------- GAME FLOW ----------------

async def start_question(room: GameRoom):
    question = QUESTIONS_DB[room.current_index]

    await broadcast(room, {
        "type": "QUESTION",
        "question": question["question"],
        "options": question["options"],
        "index": room.current_index + 1
    })

    room.start_timer(QUESTION_TIME, lambda: advance_game(room))


async def advance_game(room: GameRoom):
    if room.next_question(len(QUESTIONS_DB)):
        await start_question(room)
    else:
        await broadcast(room, {
            "type": "GAME_OVER",
            "scores": format_scores(room)
        })


# ---------------- HELPERS ----------------

async def broadcast(room: GameRoom, message: dict):
    for ws in list(room.players.values()):
        await ws.send_json(message)


def format_scores(room: GameRoom):
    return {
        f"Player {i + 1}": room.scores[pid]
        for i, pid in enumerate(room.player_order)
    }
