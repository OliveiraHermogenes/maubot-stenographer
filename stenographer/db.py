from mautrix.util.async_db import UpgradeTable, Database, Connection
from mautrix.types import RoomID

upgrade_table = UpgradeTable()

@upgrade_table.register(description="Initial revision")
async def upgrade_v1(conn: Connection) -> None:
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS language_preferences (
            room_id   TEXT NOT NULL,
            language TEXT NOT NULL,
            PRIMARY KEY (room_id)
        )"""
    )

    await conn.execute(
        """CREATE TABLE IF NOT EXISTS auto_preferences (
            room_id   TEXT NOT NULL,
            auto BOOL NOT NULL,
            PRIMARY KEY (room_id)
        )"""
    )

class DB:
    db: Database

    def __init__(self, db: Database) -> None:
        self.db = db
        
    async def put_language(self, room_id: RoomID, language: str) -> None:
        query = """
        INSERT INTO language_preferences (room_id, language) VALUES ($1, $2)
        ON CONFLICT (room_id) DO UPDATE SET language=excluded.language
        """
        await self.db.execute(query, room_id, language)
    
    async def get_language(self, room_id: RoomID) -> str | None:
        query = "SELECT language FROM language_preferences WHERE room_id=$1"
        return await self.db.fetchval(query, room_id)

    async def put_auto(self, room_id: RoomID, auto: bool) -> None:
        query = """
        INSERT INTO auto_preferences (room_id, auto) VALUES ($1, $2)
        ON CONFLICT (room_id) DO UPDATE SET auto=excluded.auto
        """
        await self.db.execute(query, room_id, auto)
    
    async def get_auto(self, room_id: RoomID) -> bool | None:
        query = "SELECT auto FROM auto_preferences WHERE room_id=$1"
        return await self.db.fetchval(query, room_id)
