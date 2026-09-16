import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file")

engine = create_engine(DATABASE_URL, echo=False)


def test_connection():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        print("Connected to:")
        print(result.fetchone()[0])


def run_sql_file(path):
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print(f"Executed {path}")


if __name__ == "__main__":
    test_connection()