from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio

from game import GameRoom
from models import Question
from question_store import add_question, get_questions

app = FastAPI()
rooms: dict[str, GameRoom] = {}

QUESTION_TIME = 10  # seconds

# ---------------- HEALTH ----------------
@app.get("/")
def health():
    return {"status": "Server running"}

# ---------------- ADMIN API ----------------
@app.post("/admin/question")
def create_question(question: Question):
    add_question(question)
    return {"status": "saved"}

@app.get("/admin/questions")
def list_questions():
    return get_questions()

# ---------------- WEBSOCKET GAME ----------------
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

    # Send player number
    await ws.send_json({
        "type": "PLAYER_INFO",
        "you_are": f"Player {room.get_player_number(player_id)}"
    })

    # Start game once
    if len(room.players) >= 2 and not room.started:
        room.started = True
        await start_question(room)

    try:
        while True:
            data = await ws.receive_json()

            if data.get("type") == "ANSWER":
                questions = get_questions()
                if room.current_index >= len(questions):
                    continue

                q = questions[room.current_index]

                correct = room.check_answer(
                    player_id,
                    data.get("answer"),
                    q.correct
                )

                # ✅ Only first correct wins
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
    questions = get_questions()

    if not questions or room.current_index >= len(questions):
        await end_game(room)
        return

    q = questions[room.current_index]

    await broadcast(room, {
        "type": "QUESTION",
        "question": q.question,
        "options": q.options,
        "index": room.current_index + 1
    })

    room.start_timer(QUESTION_TIME, room_timeout(room))

def room_timeout(room: GameRoom):
    async def _timeout():
        await advance_game(room)
    return _timeout

async def advance_game(room: GameRoom):
    questions = get_questions()
    room.cancel_timer()

    if room.next_question(len(questions)):
        await start_question(room)
    else:
        await end_game(room)

async def end_game(room: GameRoom):
    room.cancel_timer()
    await broadcast(room, {
        "type": "GAME_OVER",
        "scores": format_scores(room)
    })

# ---------------- UTIL ----------------
async def broadcast(room: GameRoom, message: dict):
    for ws in list(room.players.values()):
        await ws.send_json(message)

def format_scores(room: GameRoom):
    return {
        f"Player {i+1}": room.scores[pid]
        for i, pid in enumerate(room.player_order)
    }
