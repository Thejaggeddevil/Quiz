from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from game import GameRoom

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
    room.add_player(player_id, ws)

    # Start when 2 players join
    if len(room.players) == 2:
        q = room.current_question()
        for p in room.players.values():
            await p.send_json({
                "type": "QUESTION",
                "question": q["question"],
                "options": q["options"],
                "index": room.current_index + 1
            })

    try:
        while True:
            data = await ws.receive_json()

            if data["type"] == "ANSWER":
                winner = room.check_answer(player_id, data["answer"])

                if winner:
                    # send result
                    for p in room.players.values():
                        await p.send_json({
                            "type": "RESULT",
                            "winner": winner,
                            "scores": room.scores
                        })

                    # move to next question
                    if room.next_question():
                        q = room.current_question()
                        for p in room.players.values():
                            await p.send_json({
                                "type": "QUESTION",
                                "question": q["question"],
                                "options": q["options"],
                                "index": room.current_index + 1
                            })
                    else:
                        # game over
                        for p in room.players.values():
                            await p.send_json({
                                "type": "GAME_OVER",
                                "scores": room.scores
                            })

    except WebSocketDisconnect:
        room.players.pop(player_id, None)
