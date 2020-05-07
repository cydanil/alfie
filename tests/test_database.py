import os
import sys

from databases import Database
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from create_db import create  # noqa: import not at top of file


@pytest.mark.asyncio
async def test_create_db(tmpdir):
    p = tmpdir / 'alfie.db'
    await create(p)

    assert p.exists()

    query = 'SELECT name FROM sqlite_master;'
    async with Database(f'sqlite:///{p}') as db:
        ret = await db.fetch_all(query)
    assert ret == [('Project',), ('sqlite_autoindex_Project_1',),
                   ('Document',), ('ProjectEntry',)]
