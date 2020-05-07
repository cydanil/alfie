from asyncio import get_event_loop
from pathlib import Path

from databases import Database


async def create(path: Path) -> None:
    async with Database(f'sqlite:///{path}') as db:
        query = """CREATE TABLE Project(
            ProjectId INTEGER PRIMARY KEY,
            name VARCHAR(100),
            UNIQUE(name)
        );"""
        await db.execute(query)

        query = """CREATE TABLE Document(
            DocumentId INTEGER PRIMARY KEY,
            Name VARCHAR(100),
            Location VARCHAR(255),
            Description TEXT
        );"""
        await db.execute(query)

        query = """CREATE TABLE ProjectEntry(
            ProjectId INTEGER,
            DocumentId INTEGER,
            AccessCount INTEGER,
            FOREIGN KEY(ProjectId) REFERENCES Project(ProjectId),
            FOREIGN KEY(DocumentId) REFERENCES Document(DocumentId)
        );"""
        await db.execute(query)


if __name__ == "__main__":
    p = Path('alfie.db')
    loop = get_event_loop()
    loop.run_until_complete(create(p))
