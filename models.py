from pydantic import BaseModel
from typing import List

class Question(BaseModel):
    question: str
    options: List[str]
    correct: str

class Answer(BaseModel):
    type: str
    answer: str
