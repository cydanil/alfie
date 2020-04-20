import pytest

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import alfie  # noqa: import not at top of file
alfie.projects = {'icepap-ipassign':
                  {'README': ('tests/test_data/ipa/README.md',
                              'Full project readme'),
                   'GUI README': ('tests/test_data/ipa/gui/gui.md',
                                  'Qt GUI implementation details')}
                  }

from alfie import app  # noqa: import not at top of file


@pytest.mark.asyncio
async def test_export_data():
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
    alfie.projects['icepap-ipassign']['notafile'] = ('no/dir/not/a/file.txt',
                                                     '')
    response = await client.get('/export?project=icepap-ipassign&zip=True')
    assert response.status_code == 200

    data = await response.get_data()
    assert data.startswith(b'\x50\x4b')  # PK zip file header
