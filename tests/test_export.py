import pytest

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alfie import app  # noqa: import not at top of file


@pytest.mark.asyncio
async def test_export_data():
    client = app.test_client()

    response = await client.get('/export?project=icepap-ipassign&zip=False')
    assert response.status_code == 200

    expected = (b'README: /home/cydanil/icepap-ipassign/README.md\n'
                b'GUI README: /home/cydanil/icepap-ipassign/ipa_gui/gui.md')
    data = await response.get_data()
    assert data == expected

    response = await client.get('/export?project=icepap-ipassign&zip=True')
    assert response.status_code == 200

    data = await response.get_data()
    assert data.startswith(b'\x50\x4b\x03\x04')  # PK zip file header
