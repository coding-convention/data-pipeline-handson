from pathlib import Path

from app.quiz_seed import init_db

if __name__ == "__main__":
    init_db(Path("app/data/quiz.sqlite3"))
    print("Initialized app/data/quiz.sqlite3 with 3 quiz questions.")
