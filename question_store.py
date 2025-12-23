from typing import List
from models import Question

QUESTIONS: List[Question] = []

def add_question(q: Question):
    QUESTIONS.append(q)

def get_questions() -> List[Question]:
    return QUESTIONS

def clear_questions():
    QUESTIONS.clear()
