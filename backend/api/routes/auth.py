from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2.extras
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from db.database import get_connection
from core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterInput(BaseModel):
    name: str
    email: str
    password: str
    major: str
    year_of_study: int
    university: str = "King Khalid University"


class LoginInput(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(data: RegisterInput):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT id FROM students WHERE email = %s", (data.email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    cursor.execute(
        """
        INSERT INTO students (name, email, major, year_of_study, university, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """,
        (
            data.name, data.email, data.major,
            data.year_of_study, data.university,
            hash_password(data.password),
        ),
    )
    student_id = cursor.fetchone()["id"]
    conn.commit()
    cursor.close()
    conn.close()

    return {"token": create_access_token(student_id), "student_id": student_id}


@router.post("/login")
def login(data: LoginInput):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT id, password_hash FROM students WHERE email = %s", (data.email,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row or not row["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(data.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"token": create_access_token(row["id"]), "student_id": row["id"]}
