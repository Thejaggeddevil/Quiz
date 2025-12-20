import time

QUESTIONS = [
    {
        "question": "Capital of India?",
        "options": ["Delhi", "Mumbai", "Chennai", "Kolkata"],
        "correct": "Delhi"
    },
    {
        "question": "2 + 2 = ?",
        "options": ["3", "4", "5", "6"],
        "correct": "4"
    },
    {
        "question": "Color of sky?",
        "options": ["Blue", "Red", "Green", "Yellow"],
        "correct": "Blue"
    },
    {
        "question": "Largest planet?",
        "options": ["Earth", "Mars", "Jupiter", "Venus"],
        "correct": "Jupiter"
    },
    {
        "question": "5 x 6 = ?",
        "options": ["30", "11", "56", "20"],
        "correct": "30"
    },
    {
        "question": "Opposite of hot?",
        "options": ["Cold", "Warm", "Fire", "Heat"],
        "correct": "Cold"
    },
    {
        "question": "Sun rises in?",
        "options": ["North", "South", "East", "West"],
        "correct": "East"
    },
    {
        "question": "Water freezes at?",
        "options": ["0°C", "50°C", "100°C", "10°C"],
        "correct": "0°C"
    },
    {
        "question": "Fastest animal?",
        "options": ["Dog", "Cheetah", "Horse", "Tiger"],
        "correct": "Cheetah"
    },
    {
        "question": "HTML is used for?",
        "options": ["Styling", "Logic", "Structure", "Database"],
        "correct": "Structure"
    }
]


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

    def current_question(self):
        return QUESTIONS[self.current_index]

    def check_answer(self, player_id, answer):
        if self.answered:
            return False

        if answer == self.current_question()["correct"]:
            self.answered = True
            self.scores[player_id] += 1
            return True
        return False

    def next_question(self):
        self.current_index += 1
        self.answered = False
        return self.current_index < len(QUESTIONS)
