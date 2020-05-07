import sys
import os.path as op
from pathlib import Path

from databases import Database

sys.path.append(op.abspath(op.join(op.dirname(__file__), '..')))
import create_db  # noqa: import not at top of file


projects = {'icepap-ipassign':
            {'README': ('tests/test_data/ipa/README.md',
                        'Complete ipassign documentation'),
             'GUI README': ('tests/test_data/ipa/gui/gui.md',
                            'Qt Gui development documentation')},
            'h5py':
            {'Groups': ('/home/cydanil/h5py/docs/high/group.rst',
                        'hdf5 groups manual'),
             'Files': ('/home/cydanil/h5py/docs/high/file.rst',
                       'hdf5 files manual'),
             'Build': ('/home/cydanil/h5py/docs/build.rst',
                       'hdf5 build how-to')},
            'rook':
            {'Sample docx file': ('tests/test_data/file-sample_1MB.docx',
                                  'Test microsoft docx file handling'),
             'Sample doc file': ('tests/test_data/file-sample_1MB.doc',
                                 'Test legacy doc file handling')},
            'bluejay': {},
            'pelican': {},
            'ostrich': {},
            }

insert_project = ('INSERT INTO "Project" ("Name") '
                  'VALUES (:Name)')

insert_document = ('INSERT INTO "Document" '
                   '("Name", "Location", "Description") '
                   'VALUES (:Name, :Location, :Description)')

insert_project_entry = ('INSERT INTO "ProjectEntry" '
                        '("ProjectId", "DocumentId") '
                        'VALUES (:ProjectId, :DocumentId)')


async def create_and_populate_test_db(path: Path) -> None:
    """Create and populate a test database at the given path."""
    if not str(path).endswith('alfie.db'):
        path = path / 'alfie.db'

    await create_db.create(path)

    async with Database(f'sqlite:///{path}') as db:
        for project, items in projects.items():
            pid = await db.execute(insert_project, {'Name': project})

            for name, (loc, desc) in items.items():
                did = await db.execute(insert_document, {'Name': name,
                                                         'Location': loc,
                                                         'Description': desc})

                await db.execute(insert_project_entry, {'ProjectId': pid,
                                                        'DocumentId': did})
