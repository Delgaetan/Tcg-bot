"""
Gestion de la base de données SQLite pour le bot TCG.
Aucune connaissance en SQL n'est nécessaire pour utiliser le bot :
ce fichier gère tout automatiquement.
"""
import aiosqlite
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "tcg.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 200,
                last_daily TEXT DEFAULT NULL,
                deck TEXT DEFAULT '[]'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                card_id TEXT,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, card_id)
            )
        """)
        await db.commit()


async def get_player(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if row is None:
            await db.execute("INSERT INTO players (user_id) VALUES (?)", (user_id,))
            await db.commit()
            cur = await db.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
            row = await cur.fetchone()
        return dict(row)


async def update_coins(user_id: int, amount: int):
    await get_player(user_id)  # s'assure que le joueur existe
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE players SET coins = coins + ? WHERE user_id = ?", (amount, user_id)
        )
        await db.commit()


async def set_last_daily(user_id: int, iso_timestamp: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE players SET last_daily = ? WHERE user_id = ?", (iso_timestamp, user_id)
        )
        await db.commit()


async def add_card_to_inventory(user_id: int, card_id: str, quantity: int = 1):
    await get_player(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO inventory (user_id, card_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, card_id) DO UPDATE SET quantity = quantity + ?
        """, (user_id, card_id, quantity, quantity))
        await db.commit()


async def get_inventory(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT card_id, quantity FROM inventory WHERE user_id = ? AND quantity > 0",
            (user_id,)
        )
        rows = await cur.fetchall()
        return {row["card_id"]: row["quantity"] for row in rows}


async def get_card_quantity(user_id: int, card_id: str) -> int:
    inv = await get_inventory(user_id)
    return inv.get(card_id, 0)


async def set_deck(user_id: int, card_ids: list):
    await get_player(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE players SET deck = ? WHERE user_id = ?",
            (json.dumps(card_ids), user_id)
        )
        await db.commit()


async def get_deck(user_id: int) -> list:
    player = await get_player(user_id)
    return json.loads(player["deck"])
