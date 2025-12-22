import asyncio

MAX_PLAYERS = 5


class GameRoom:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = {}          # player_id -> websocket
        self.scores = {}           # player_id -> score
        self.player_order = []     # join order
        self.current_index = 0
        self.answered = False
        self.started = False

        self.timer_task = None

    # ---------------- PLAYER MANAGEMENT ----------------

    def add_player(self, player_id, ws):
        if player_id in self.players:
            return

        if len(self.player_order) >= MAX_PLAYERS:
            raise Exception("Room full")

        self.players[player_id] = ws
        self.scores.setdefault(player_id, 0)
        self.player_order.append(player_id)

    def get_player_number(self, player_id):
        return self.player_order.index(player_id) + 1

    # ---------------- GAME STATE ----------------

    def next_question(self, total_questions: int):
        if self.current_index + 1 >= total_questions:
            return False

        self.current_index += 1
        self.answered = False
        return True

    def check_answer(self, player_id, answer, correct_answer):
        if self.answered:
            return False

        if answer == correct_answer:
            self.answered = True
            self.scores[player_id] += 1
            return True

        return False

    # ---------------- TIMER ----------------

    def start_timer(self, seconds, on_timeout):
        self.cancel_timer()

        async def timer():
            await asyncio.sleep(seconds)
            if not self.answered:
                await on_timeout()

        self.timer_task = asyncio.create_task(timer())

    def cancel_timer(self):
        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None
