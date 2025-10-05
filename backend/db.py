import os
import re
from urllib.parse import urlparse
import mysql.connector
from mysql.connector import pooling

# Parse DATABASE_URL of form: mysql+mysqlconnector://user:pass@host:port/database
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:password@localhost:3306/infoclass_db")

# Fallback individual env vars (optional)
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

host = user = password = database = None
port = 3306

if DATABASE_URL:
    # Remove driver prefix if present
    cleaned = re.sub(r"^mysql\+mysqlconnector://", "", DATABASE_URL)
    parsed = urlparse(f"//{cleaned}")  # add // so urlparse treats it as netloc
    user = parsed.username or user
    password = parsed.password or password
    host = parsed.hostname or host
    port = parsed.port or port
    database = (parsed.path[1:] if parsed.path else None) or database

# Override with explicit env vars if provided
host = DB_HOST or host or "localhost"
user = DB_USER or user or "root"
password = DB_PASSWORD or password or "password"
database = DB_NAME or database or "infoclass_db"
port = int(DB_PORT or port or 3306)

_pool = pooling.MySQLConnectionPool(
    pool_name="infoclass_pool",
    pool_size=10,
    host=host,
    user=user,
    password=password,
    database=database,
    port=port,
    charset="utf8mb4",
    autocommit=True,
)

def get_conn():
    return _pool.get_connection()


def query_one(sql: str, params: tuple = ()):  # returns dict
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row


def query_all(sql: str, params: tuple = ()):  # returns list of dicts
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows


def execute(sql: str, params: tuple = ()):  # returns lastrowid, rowcount
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        last_id = cur.lastrowid
        rowcount = cur.rowcount
        cur.close()
        return last_id, rowcount
