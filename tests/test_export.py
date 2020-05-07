import os
import sys

from databases import Database
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alfie import app  # noqa: import not at top of file
import create_db  # noqa
from create_test_db import (create_and_populate_test_db,  # noqa
                            insert_document, insert_project_entry, projects)


@pytest.mark.asyncio
async def test_export_data(tmpdir):
    await create_and_populate_test_db(tmpdir)
    db_path = f"sqlite:///{tmpdir / 'alfie.db'}"
    app.config['DATABASE'] = db_path
    client = app.test_client()

    # Test export as text file ok.
    response = await client.get('/export?project=icepap-ipassign&zip=False')
    assert response.status_code == 200

    expected = (b'README: tests/test_data/ipa/README.md\n'
                b'GUI README: tests/test_data/ipa/gui/gui.md')
    data = await response.get_data()
    assert data == expected

    # Test export zip file ok
    response = await client.get('/export?project=icepap-ipassign&zip=True')
    assert response.status_code == 200

    data = await response.get_data()
    assert data.startswith(b'\x50\x4b')  # PK zip file header

    # Test handling (skipping) inaccessible files ok.
    get_pid = f'SELECT ProjectId FROM Project WHERE Name = "icepap-ipassign"'
    async with Database(db_path) as db:
        pid = await db.fetch_val(get_pid)
        values = {'Name': 'notafile',
                  'Location': 'no/dir/not/a/file.txt',
                  'Description': ''}
        did = await db.execute(insert_document, values)
        await db.execute(insert_project_entry, values={'ProjectId': pid,
                                                       'DocumentId': did})
    response = await client.get('/export?project=icepap-ipassign&zip=True')
    assert response.status_code == 200

    data = await response.get_data()
    assert data.startswith(b'\x50\x4b')  # PK zip file header
