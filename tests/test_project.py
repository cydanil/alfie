import os.path as op
import sys

from databases import Database
import pytest

sys.path.append(op.abspath(op.join(op.dirname(__file__), '..')))
from alfie import app  # noqa: import not at top of file
import create_db  # noqa
from create_test_db import (create_and_populate_test_db,  # noqa
                            insert_document, insert_project_entry, projects)


@pytest.mark.asyncio
async def test_load_projects(tmpdir):
    await create_and_populate_test_db(tmpdir)
    db_path = f"sqlite:///{tmpdir / 'alfie.db'}"
    app.config['DATABASE'] = db_path
    client = app.test_client()

    # Test export as text file ok.
    response = await client.get('/index')
    assert response.status_code == 200

    page = (await response.get_data()).decode()

    for key in projects.keys():
        assert key in page
        for name, (loc, desc) in projects[key].items():
            assert name in page
            assert loc in page
            assert desc in page


@pytest.mark.asyncio
async def test_load_no_project(tmpdir):
    await create_db.create(tmpdir / 'alfie.db')
    db_path = f"sqlite:///{tmpdir / 'alfie.db'}"
    app.config['DATABASE'] = db_path
    client = app.test_client()

    response = await client.get('/index')
    page = await response.get_data()
    assert b'No project available' in page


@pytest.mark.asyncio
async def test_add_to_project(tmpdir):
    await create_and_populate_test_db(tmpdir)
    db_path = f"sqlite:///{tmpdir / 'alfie.db'}"
    app.config['DATABASE'] = db_path
    client = app.test_client()

    project = 'icepap-ipassign'
    name = 'Mock File'
    location = '/whatever/place/file.rst'
    description = 'Not a real file, just testing that entries are added ok'

    response = await client.post('/add', form={'name': name,
                                               'location': location,
                                               'description': description,
                                               'project': project})
    page = await response.get_data()
    assert b'<title>Redirect</title>' in page

    async with Database(db_path) as db:
        query = f'SELECT * FROM Document WHERE Name = "{name}"'
        ret = await db.fetch_one(query)
    assert name == ret[1]
    assert location == ret[2]
    assert description == ret[3]

    response = await client.get('/index')
    page = (await response.get_data()).decode()

    assert name in page
    assert location in page
    assert description in page


@pytest.mark.asyncio
async def test_remove_from_project(tmpdir):
    await create_and_populate_test_db(tmpdir)
    db_path = f"sqlite:///{tmpdir / 'alfie.db'}"
    app.config['DATABASE'] = db_path
    client = app.test_client()
    project = 'icepap-ipassign'
    name = 'Mock File'
    loc = '/whatever/place/file.rst'
    desc = 'Not a real file, just testing that entries are removed ok'

    get_pid = f'SELECT ProjectId FROM Project WHERE Name = "{project}"'
    async with Database(db_path) as db:
        pid = await db.fetch_val(get_pid)
        did = await db.execute(insert_document, values={'Name': name,
                                                        'Location': loc,
                                                        'Description': desc})
        await db.execute(insert_project_entry, values={'ProjectId': pid,
                                                       'DocumentId': did})

    response = await client.post('/remove', form={'document': name,
                                                  'project': project})
    page = await response.get_data()
    assert b'<title>Redirect</title>' in page

    async with Database(db_path) as db:
        query = f'SELECT * FROM Project WHERE ProjectId = {did}'
        ret = await db.fetch_one(query)
    assert ret is None

    response = await client.get('/index')
    page = (await response.get_data()).decode()
    assert f'{name} removed from {project}' in page


@pytest.mark.asyncio
async def test_add_project(tmpdir):
    await create_and_populate_test_db(tmpdir)
    db_path = f"sqlite:///{tmpdir / 'alfie.db'}"
    app.config['DATABASE'] = db_path
    client = app.test_client()

    response = await client.post('/create', form={'name': 'cuckoo'})
    page = await response.get_data()

    assert b'<title>Redirect</title>' in page

    query = 'SELECT ProjectId FROM Project WHERE Name = "cuckoo"'
    async with Database(db_path) as db:
        ret = await db.fetch_val(query)
    assert ret == 7

    response = await client.get('/index')
    page = (await response.get_data()).decode()

    assert '<div id="collapse-cuckoo"' in page
    assert '<div class="card-header" id="heading-cuckoo">' in page

    assert '<button id="cuckoo_export"' not in page
    assert '<button id="cuckoo_plus"' in page

    await client.post('/create', form={'name': 'cuckoo'})
    response = await client.get('/index')

    page = (await response.get_data()).decode()
    assert 'This project already exists' in page

    await client.post('/create')
    response = await client.get('/index')

    page = (await response.get_data()).decode()
    assert 'Did not specify a project name' in page
