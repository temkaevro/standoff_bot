import sqlite3
import json
import logging
from typing import List, Dict, Optional, Any

DB_PATH = "standoff.db"

def get_connection():
    """Возвращает соединение с базой данных."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создаёт таблицы, если их нет."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица оружия (справочник)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weapons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    
    # Таблица скинов (справочник)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            weapon_id INTEGER,
            name TEXT,
            FOREIGN KEY (weapon_id) REFERENCES weapons (id),
            UNIQUE(weapon_id, name)
        )
    ''')
    
    # Таблица наклеек (справочник)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stickers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            rarity TEXT
        )
    ''')
    
    # Таблица объявлений
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            weapon_name TEXT,
            skin_name TEXT,
            stickers TEXT,  -- JSON список наклеек
            price_gold INTEGER DEFAULT 0,
            price_rub INTEGER DEFAULT 0,
            price_stars INTEGER DEFAULT 0,
            trade BOOLEAN DEFAULT 0,
            bargain BOOLEAN DEFAULT 0,
            photo_file_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logging.info("Database initialized.")

# === Вспомогательные функции для работы с пользователями ===
def register_user(user_id: int, username: str):
    """Регистрирует пользователя, если его нет."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)
    ''', (user_id, username))
    conn.commit()
    conn.close()

def user_exists(user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

# === Функции для работы со справочниками ===
def get_weapons() -> List[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM weapons ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [row["name"] for row in rows]

def add_weapon(name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO weapons (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def get_skins_by_weapon(weapon_name: str) -> List[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.name FROM skins s
        JOIN weapons w ON w.id = s.weapon_id
        WHERE w.name = ?
        ORDER BY s.name
    ''', (weapon_name,))
    rows = cursor.fetchall()
    conn.close()
    return [row["name"] for row in rows]

def add_skin(weapon_name: str, skin_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    # Находим weapon_id
    cursor.execute("SELECT id FROM weapons WHERE name = ?", (weapon_name,))
    weapon_row = cursor.fetchone()
    if weapon_row:
        cursor.execute("INSERT OR IGNORE INTO skins (weapon_id, name) VALUES (?, ?)", (weapon_row["id"], skin_name))
        conn.commit()
    conn.close()

def get_stickers() -> List[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM stickers ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [row["name"] for row in rows]

def add_sticker(name: str, rarity: str = "Обычная"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO stickers (name, rarity) VALUES (?, ?)", (name, rarity))
    conn.commit()
    conn.close()

# === Функции для работы с объявлениями ===
def create_listing(user_id: int, weapon_name: str, skin_name: str, stickers: List[str],
                   price_gold: int, price_rub: int, price_stars: int,
                   trade: bool, bargain: bool, photo_file_id: str) -> int:
    """Создаёт объявление и возвращает его ID."""
    conn = get_connection()
    cursor = conn.cursor()
    stickers_json = json.dumps(stickers)
    cursor.execute('''
        INSERT INTO listings (
            user_id, weapon_name, skin_name, stickers,
            price_gold, price_rub, price_stars, trade, bargain, photo_file_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, weapon_name, skin_name, stickers_json,
          price_gold, price_rub, price_stars, trade, bargain, photo_file_id))
    conn.commit()
    listing_id = cursor.lastrowid
    conn.close()
    return listing_id

def get_active_listings_by_skin(weapon_name: str, skin_name: str) -> List[Dict]:
    """Возвращает активные объявления для указанного скина, сортированные по дате."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM listings
        WHERE weapon_name = ? AND skin_name = ? AND active = 1
        ORDER BY created_at DESC
    ''', (weapon_name, skin_name))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_listing_by_id(listing_id: int) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_listings(user_id: int) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM listings
        WHERE user_id = ? AND active = 1
        ORDER BY created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_listing(listing_id: int):
    """Мягкое удаление (помечает как неактивное)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE listings SET active = 0 WHERE id = ?", (listing_id,))
    conn.commit()
    conn.close()

def update_listing_price(listing_id: int, price_gold: int, price_rub: int, price_stars: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE listings SET price_gold = ?, price_rub = ?, price_stars = ?
        WHERE id = ?
    ''', (price_gold, price_rub, price_stars, listing_id))
    conn.commit()
    conn.close()

def update_listing_flags(listing_id: int, trade: bool, bargain: bool):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE listings SET trade = ?, bargain = ?
        WHERE id = ?
    ''', (trade, bargain, listing_id))
    conn.commit()
    conn.close()
