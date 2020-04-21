import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alfie import app  # noqa: import not at top of file
import alfie  # noqa: import not at top of file
alfie.projects = {'icepap-ipassign':
                  {'README': ('tests/test_data/ipa/README.md',
                              'Full project readme'),
                   'GUI README': ('tests/test_data/ipa/gui/gui.md',
                                  'Qt GUI implementation details')}
                  }


@pytest.mark.asyncio
async def test_load_projects():
    client = app.test_client()

    # Test export as text file ok.
    response = await client.get('/index')
    assert response.status_code == 200

    page = (await response.get_data()).decode()

    key, = alfie.projects.keys()
    assert key in page

    for name, (loc, desc) in alfie.projects[key].items():
        assert name in page
        assert loc in page
        assert desc in page


@pytest.mark.asyncio
async def test_load_no_project():
    projects, alfie.projects = alfie.projects, {}
    client = app.test_client()

    response = await client.get('/index')
    page = await response.get_data()
    assert b'No project available' in page

    alfie.projects = projects


@pytest.mark.asyncio
async def test_add_to_project():
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

    response = await client.get('/index')
    page = (await response.get_data()).decode()

    assert name in page
    assert location in page
    assert description in page


@pytest.mark.asyncio
async def test_add_project():
    client = app.test_client()

    response = await client.post('/create', form={'name': 'cuckoo'})
    page = await response.get_data()

    assert b'<title>Redirect</title>' in page

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
