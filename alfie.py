import quart.flask_patch  # noqa, required by Quart.

from asyncio import gather, get_event_loop
import io
import os
from pathlib import Path
import zipfile

import pypandoc
from quart import (flash, Quart, redirect, request, render_template, send_file,
                   url_for)
from sqlite3 import OperationalError
import toml

from create_db import create
from databases import Database
from database import Document, Project, ProjectEntry
from definitions import (MEDIA_EXTENSIONS, OFFICE_EXTENSIONS,
                         PANDOC_EXTENTIONS)

app = Quart(__name__)
app.config['SECRET_KEY'] = os.environ['ALFIE_SECRET']


config_path = Path(__file__).parent / 'config.toml'
config = toml.load(config_path)

db_path = config['database']['path']
if not db_path.endswith('/alfie.db'):
    db_path += '/alfie.db'
loop = get_event_loop()
try:
    loop.run_until_complete(create(db_path))
except OperationalError:
    pass
finally:
    app.config['DATABASE'] = f'sqlite:///{db_path}'


@app.route('/')
@app.route('/index')
async def index():
    projects = {}
    entries_retrieve = ('SELECT DocumentId FROM ProjectEntry '
                        'WHERE ProjectId = :pid')
    document_retrieve = ('SELECT Name, Location, Description FROM Document '
                         'WHERE DocumentId = :did')

    async with Database(app.config['DATABASE']) as db:
        for proj in await db.fetch_all(query=Project.select()):
            pid, pname = proj
            content = {}
            entries = await db.fetch_all(entries_retrieve, {'pid': pid})
            if entries:
                coros = [db.fetch_one(document_retrieve, {'did': did})
                         for did, in entries]
                ret = await gather(*coros)
                content = {name: _ for (name, *_) in ret}
            projects[pname] = content

    html = await render_template('index.html', projects=projects)
    return html


@app.route('/create', methods=['POST'])
async def create():
    """Create a new project in the database."""

    form = await request.form
    name = form.get('name')

    async with Database(app.config['DATABASE']) as db:
        project_id = await db.fetch_one(
            query='SELECT ProjectId FROM Project WHERE Name = :name',
            values={'name': name})

        if name is None:
            await flash('Did not specify a project name')
        elif project_id is not None:
            await flash('This project already exists')
        else:
            await db.execute(query=Project.insert(), values={'Name': name})
            await flash(f'{name} successfully added')

    ret = redirect(f'{url_for("index")}#{name}')
    return ret


@app.route('/add', methods=['POST'])
async def add():
    """Add an entry to a project.

    The arguments must be:
        project str: the name of the project where to add the new entry to
        name str: the name/key of the entry in the project.
                  This name will be used when exporting the project.
        location str: the document's URI
        description str: a short summary of the file. Typically used to get
                        a quick glance of the file. This is also used when
                        searching.
    """
    form = await request.form

    try:
        project = form['project']
        name = form['name']
        loc = form['location']
        description = form.get('description', '')
    except KeyError:
        await flash('Could not add content')
        return redirect('{url_for("index")}')

    ret = redirect(f'{url_for("index")}#{project}')

    async with Database(app.config['DATABASE']) as db:
        project_id = await db.fetch_val(
            query='SELECT ProjectId FROM Project WHERE Name = :project',
            values={'project': project})

        if project_id is None:
            await flash('This project does not exist')
            return ret

        doc_id = await db.execute(query=Document.insert(),
                                  values={'Name': name,
                                          'Location': loc,
                                          'Description': description})

        await db.execute(query=ProjectEntry.insert(),
                         values={'ProjectId': project_id,
                                 'DocumentId': doc_id})
    return ret


@app.route('/remove', methods=['POST'])
async def remove():
    """Remove an entry from a project.

    This post method expects the keys `project` and `document` in it, both
    strings.
    The document should refer to a key within the project.
    """
    form = await request.form

    # We can allow ourselves to have one try-except statement, as either we
    # miss keys in the POST arguments, or these are incorrect within the db.
    try:
        doc_name = form['document']
        proj_name = form['project']

        async with Database(app.config['DATABASE']) as db:
            query = 'SELECT ProjectId from Project WHERE Name = :name'
            proj_id = await db.fetch_val(query, values={'name': proj_name})

            query = 'SELECT DocumentId FROM Document WHERE Name = :name'
            doc_id = await db.fetch_val(query, values={'name': doc_name})

            query = 'DELETE FROM Document WHERE Name = :name'
            await db.execute(query, values={'name': doc_name})

            query = ("DELETE FROM ProjectEntry WHERE ProjectId = :proj_id AND "
                     "DocumentId = :doc_id")
            await db.execute(query, values={'proj_id': proj_id,
                                            'doc_id': doc_id})

        await flash(f'{doc_name} removed from {proj_name}')

    except (KeyError, OperationalError) as e:
        raise(e) from None
        await flash('Could not remove document')
        return redirect(f'{url_for("index")}')

    return redirect(f'{url_for("index")}#{proj_name}')


@app.route('/retrieve/<path:filename>')
async def retrieve(filename: str) -> str:
    """Retrieve the files from a project.

    The filename consists of a path to the file.

    Various strategies are used depending on the file type:
        - file types supported by pandoc are converted to html;
        - PDFs are rendered using an iframe, letting the browser do the work;
        - .doc files are either converted to docx (if soffice is available)
          then converted using pandoc, or else served as files to download;
        - media files are served as files.
    """
    if not filename.startswith('/'):
        filename = '/' + filename

    extension = filename.split('.')[-1].lower()
    if extension in PANDOC_EXTENTIONS:
        loop = get_event_loop()
        try:
            content = await loop.run_in_executor(None,
                                                 pypandoc.convert_file,
                                                 filename,
                                                 'html')
            ret = await render_template('render.html', content=content)
        except RuntimeError as e:
            ret = await render_template('base.html')
            ret += str(e)

    elif extension in OFFICE_EXTENSIONS or extension in MEDIA_EXTENSIONS:
        ret = await send_file(filename, attachment_filename=filename)

    elif extension == 'pdf':
        await flash('This is not done yet!')
        url = url_for('pdf', filename=filename)
        content = f'<embed src="{url}" type="application/pdf#view=FitH" width="actual-width.px" height="actual-height.px"></embed>'
        ret = await render_template('render.html', content=content)

    elif extension == 'html':
        try:
            with open(filename, 'r') as fin:
                content = fin.read()
            ret = await render_template('render.html', content=content)
        except FileNotFoundError:
            await flash(f'{filename}: not found!')
            ret = await render_template('base.html')
    else:
        return

    return ret


@app.route('/pdf/<path:filename>')
async def pdf(filename=None):
    if filename is None:
        return
    if not filename.startswith('/'):
        filename = '/' + filename

    ret = await send_file(filename,
                          attachment_filename=filename,
                          mimetype='application/pdf',
                          as_attachment=False)
    return ret


@app.route('/export')
async def export():
    """Export the project for download.

    This url expect the project name as `project`, and an optional `zip`
    boolean.

    If `zip` is set, zip the files from the storage path.
    External resources (ie. link) are then compiled into an
    `external_resources.txt` file, itself appended to the archive.
    Its format will be 'resource_name: resource_location'.

    If `zip` is unset, then all resources in the project will be listed in
    a text file in the same format as above, and this text file will be served
    to the user.
    """
    project_name = request.args.get('project')
    zip_files = request.args.get('zip', default=True)
    zip_files = True if zip_files in ['True', True] else False

    async with Database(app.config['DATABASE']) as db:
        query = 'SELECT ProjectId FROM Project WHERE Name = :name'
        project_id = await db.fetch_val(query, {'name': project_name})

        query = 'SELECT DocumentId FROM ProjectEntry WHERE ProjectId = :pid'
        entries = await db.fetch_all(query, {'pid': project_id})

        query = ('SELECT Name, Location, Description FROM Document '
                 'WHERE DocumentId = :did')
        coros = [db.fetch_one(query, {'did': did})
                 for did, in entries]

        ret = await gather(*coros)
        documents = {name: _ for (name, *_) in ret}

    attachment_filename = project_name
    file_ = io.BytesIO()

    if zip_files:
        attachment_filename += '.zip'
        mimetype = 'application/zip'
        externals = []
        with zipfile.ZipFile(file_, 'w') as zf:
            for filename, (location, description) in documents.items():
                if location.startswith('http'):
                    externals.append((filename, location))
                    continue
                # Sanitize the file name
                fname = filename.replace(' ', '_')
                fname_ext = fname.split('.')[-1]
                loc_ext = location.split('.')[-1]
                if fname_ext != loc_ext:
                    fname = f'{fname}.{loc_ext}'
                # Write the file
                try:
                    zf.write(location, fname)
                except FileNotFoundError:
                    continue  # TODO: flash a message

            # Handle external resources
            if externals:
                zf.writestr('external_resources.txt',
                            '\n'.join(f'{n}: {uri}' for n, uri in externals))
    else:
        attachment_filename += '.txt'
        content = '\n'.join([f'{fname}: {loc}' for fname, (loc, _)
                             in documents.items()])
        file_.write(content.encode())
        mimetype = 'text/csv'

    file_.seek(0)
    ret = await send_file(file_,
                          attachment_filename=attachment_filename,
                          mimetype=mimetype,
                          as_attachment=True)
    return ret


if __name__ == '__main__':
    app.run(host='0.0.0.0')
